import os
import uuid
import json
import base64
import hashlib
import re
from app.core.files import resolve_static_file, sanitize_svg
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from openai import OpenAI
from loguru import logger

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user, get_current_user_optional, require_admin
from app.core.task_assets import task_collected, task_image_asset, owned_task_for_asset
from app.schemas.common import success_response, error_response
from app.models.entities import AiTask, AiModel, Asset, GrowthEvent, UserGrowth, SysConfig, SysUser
from app.models.mobile import UserCollection
from app.core import image_generation
from app.core.asset_generator import (
    generate_shadow_puppet_svg,
    generate_shadow_puppet_template_svg,
    generate_bronze_taotie_svg,
    generate_ballad_sheet_svg,
    generate_lacquer_design_svg,
    extract_hex_colors,
    save_generated_asset
)


router = APIRouter(prefix="/ai", tags=["AI工坊"])

STATIC_UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads")
os.makedirs(STATIC_UPLOADS_DIR, exist_ok=True)

class CreateTaskRequest(BaseModel):
    tool_type: Literal["SHADOW_PUPPET", "BRONZE", "BALLAD", "LACQUER", "EMBROIDERY", "MESH_3D"]
    input_payload: Dict[str, Any]
    model_id: Optional[int] = None
    generation_mode: Literal["LOCAL", "AI"] = "LOCAL"
    request_id: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9_-]{16,64}$")


@router.get("/capabilities")
def image_capabilities(db: Session = Depends(get_db)):
    return success_response(image_generation.capabilities(db))


def execute_image_task(db: Session, task: AiTask):
    """Keep remote image bytes locally; publish results/rewards only if still running."""
    cfg = image_generation.resolve_connection(image_generation.read_settings(db))
    reference = (image_generation.owned_reference(db, task.input_json["sketch_url"], task.user_id)
                 if task.input_json.get("sketch_url") else None)
    # Release read transactions during a potentially long provider request.
    task_id, user_id, tool, payload = task.task_id, task.user_id, task.tool_type, dict(task.input_json)
    db.commit()
    data = image_generation.generate_image(cfg, image_generation.build_prompt(tool, payload), reference)
    extension, mime = image_generation.validate_image(data)
    image_generation.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path = image_generation.GENERATED_DIR / f"{task_id}_image.{extension}"
    path.write_bytes(data)
    url = f"/static/generated/{path.name}"
    result = {
        "title": payload["prompt"].strip()[:80], "colored_image_url": url, "rendered_image_url": url,
        "line_art_url": None, "vector_svg_url": None, "print_template_url": None, "mesh_3d_url": None,
        "model_available": False, "generation_method": "ai_image", "image_model": cfg["model_name"],
        "reference_sketch_url": payload.get("sketch_url") or None,
        "completed_sketch_url": url if reference else None, "sketch_redraw_available": bool(reference),
        "lora_available": False, "lora_applied": False, "color_palette": payload.get("color_palette") or [],
        "description": ("已根据参考草图和文字要求完成 AI 图像编辑。" if reference else "已根据文字与设计参数生成 AI 图像。")
                       + "结果为二维创意参考，不是可编辑矢量、切割纸样或三维模型。",
    }
    try:
        user = db.query(SysUser).filter_by(id=user_id).with_for_update().first()
        if not user or user.status != "ACTIVE":
            raise image_generation.ImageGenerationError("账号状态已变化，任务未保存")
        finished = db.query(AiTask).filter_by(task_id=task_id, status="RUNNING").update(
            {"status": "SUCCESS", "progress": 100, "result_summary_json": result,
             "model_version": cfg["model_name"]}, synchronize_session=False)
        if not finished:
            db.rollback()
            path.unlink(missing_ok=True)
            return
        db.add(Asset(asset_type="IMAGE", object_key=f"generated/{path.name}", file_url=url,
                     mime_type=mime, created_by=user_id))
        event_ref = f"ai_{task_id}"
        if not db.query(GrowthEvent).filter_by(user_id=user_id, event_type="AI_CREATE", ref_id=event_ref).first():
            db.add(GrowthEvent(user_id=user_id, event_type="AI_CREATE", ref_id=event_ref, value=20))
            growth = db.query(UserGrowth).filter_by(user_id=user_id).with_for_update().first()
            if growth:
                growth.energy_value += 20
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise


def expire_image_tasks(db: Session, user_id: int):
    # A killed web worker cannot resume an Images API request safely. Never retry it automatically.
    stale = db.query(AiTask).filter(AiTask.user_id == user_id, AiTask.status.in_(["QUEUED", "RUNNING"]),
                                   AiTask.updated_at < datetime.utcnow() - timedelta(minutes=10)).all()
    changed = False
    for row in stale:
        if isinstance(row.input_json, dict) and row.input_json.get("_generation_mode") == "AI":
            updated = db.query(AiTask).filter(AiTask.task_id == row.task_id,
                AiTask.status.in_(["QUEUED", "RUNNING"]),
                AiTask.updated_at < datetime.utcnow() - timedelta(minutes=10)).update({
                    "status": "FAILED", "error_code": "TASK_INTERRUPTED",
                    "error_message": "生成任务已中断或超时，未自动重试。可重新发起创作"}, synchronize_session="fetch")
            changed = changed or bool(updated)
    if changed:
        db.commit()

def get_llm_client_and_config(db: Session):
    """提取运营后台配置的真实大模型接入参数与 OpenAI 客户端"""
    llm_cfg = db.query(SysConfig).filter(SysConfig.config_key == "llm_settings").first()
    if not llm_cfg or not llm_cfg.config_value:
        return None, None
    try:
        cfg = json.loads(llm_cfg.config_value)
        api_key = (cfg.get("api_key") or "").strip()
        api_base = (cfg.get("api_base") or "https://api.deepseek.com/v1").strip().rstrip("/")
        if not api_key or "*" in api_key or len(api_key) < 8:
            return None, None
        client = OpenAI(api_key=api_key, base_url=api_base)
        return client, cfg
    except Exception:
        return None, None

def extract_json_from_llm(raw_text: str) -> Optional[dict]:
    """从大模型原始回复中稳健提取合法 JSON 对象"""
    if not raw_text:
        return None
    raw = raw_text.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(raw)
    except Exception:
        # 截取最外层大括号
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end+1])
            except Exception:
                pass
        return None

def execute_ai_inference(task_id: str, tool_type: str, user_id: int):
    """
    可选语言模型提供文字分析；实际图片与纸样由本地矢量模板生成。
    三维生成服务尚未接入，不将固定示意模型作为生成结果。
    """
    db = SessionLocal()
    try:
        task = db.query(AiTask).filter(AiTask.task_id == task_id).first()
        if not task or task.status != "QUEUED":
            return
        started = db.query(AiTask).filter(AiTask.task_id == task_id, AiTask.status == "QUEUED").update(
            {"status": "RUNNING", "progress": 30}, synchronize_session=False
        )
        db.commit()
        if not started:
            return

        if isinstance(task.input_json, dict) and task.input_json.get("_generation_mode") == "AI":
            execute_image_task(db, task)
            return

        # 尝试调用真实大模型发起非遗结构化推理
        client, cfg = ((None, None) if task.input_json.get("_generation_mode") == "LOCAL"
                       else get_llm_client_and_config(db))
        llm_analysis = None
        model_name = cfg.get("model_name", "step-3.7-flash") if cfg else None
        user_prompt = task.input_json.get("prompt", "") if isinstance(task.input_json, dict) else ""

        if client and cfg and user_prompt:
            tool_name_map = {
                "SHADOW_PUPPET": "津派皮影戏",
                "BRONZE": "蓟州青铜器饕餮纹饰",
                "BALLAD": "津门曲艺与时调大鼓",
                "LACQUER": "古法大漆与螺钿髹饰",
                "EMBROIDERY": "津派刺绣与民间剪纸"
            }
            tool_cn = tool_name_map.get(tool_type, "天津传统非遗")
            system_msg = "你是国家级非遗工艺传承大师。请简明扼要输出纯JSON，严禁输出任何多余废话或Markdown标记。"
            user_msg = f"""
针对用户在【{tool_cn}】工坊的创作灵感【{user_prompt}】，输出标准纯JSON对象：
{{
  "title": "作品定名",
  "historical_context": "津派文化渊源（40字左右）",
  "color_palette": ["#十六进制色彩1 (色名)", "#十六进制色彩2 (色名)", "#十六进制色彩3 (色名)", "#十六进制色彩4 (色名)"],
  "craft_technique": "传统技艺操作手法与刀法制作指导（50字左右）",
  "mentor_description": "大师综合寄语与艺术价值点评（60字左右）"
}}
"""
            try:
                chat_resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    max_tokens=4096,
                    temperature=0.5,
                    timeout=30.0
                )
                raw_json = chat_resp.choices[0].message.content or ""
                llm_analysis = extract_json_from_llm(raw_json)
            except Exception as e:
                print(f"[AI Workshop] Live LLM inference fallback: {e}")
        
        # 依据不同的非遗工具类型组装资产
        llm_colors = llm_analysis.get("color_palette") if llm_analysis else None
        supplied_colors = validated_input_palette(task.input_json)
        if supplied_colors:
            llm_colors = supplied_colors
        if tool_type == "SHADOW_PUPPET":
            role_type = task.input_json.get("role_type", "生角·津门书生") if isinstance(task.input_json, dict) else "生角·津门书生"
            face_style = task.input_json.get("face_style", "CLASSIC") if isinstance(task.input_json, dict) else "CLASSIC"

            # 1. 真实生成线稿矢量图
            line_art_svg = generate_shadow_puppet_svg(role_type, colored=False, prompt=user_prompt, colors=llm_colors, face_style=face_style)
            line_art_url = save_generated_asset(f"{task_id}_lineart.svg", line_art_svg)
            
            # 2. 真实生成津派矿物套色皮影
            colored_svg = generate_shadow_puppet_svg(role_type, colored=True, prompt=user_prompt, colors=llm_colors, face_style=face_style)
            colored_url = save_generated_asset(f"{task_id}_colored.svg", colored_svg)
            
            # 3. 真实生成可打印 A4 激光切割纸样排版
            template_svg = generate_shadow_puppet_template_svg(role_type, prompt=user_prompt, face_style=face_style)
            template_url = save_generated_asset(f"{task_id}_template.svg", template_svg)
            
            desc = shadow_template_description(role_type)
            
            result = {
                "role_type": role_type,
                "face_style": face_style,
                "title": llm_analysis.get("title") if llm_analysis else f"{role_type} · 皮影创作",
                "line_art_url": line_art_url,
                "colored_image_url": colored_url,
                "rendered_image_url": colored_url,
                "mesh_3d_url": None,
                "model_available": False,
                "generation_method": "local_template",
                "print_template_url": template_url,
                "description": desc,
                "historical_context": llm_analysis.get("historical_context") if llm_analysis else "津派皮影融合东路皮影与津门时调规范，清末民初在海河沿岸茶馆盛行，风格硬朗中见儒雅。",
                "color_palette": extract_hex_colors(llm_colors),
                "craft_technique": llm_analysis.get("craft_technique") if llm_analysis else "阴阳刻结合，软线硬刻，三签五骨操纵布局。",
                "llm_generated": bool(llm_analysis),
                "llm_model": model_name if llm_analysis else None
            }
        elif tool_type == "BRONZE":
            pattern_type = task.input_json.get("pattern_type", "饕餮纹") if isinstance(task.input_json, dict) else "饕餮纹"
            style_filter = task.input_json.get("style", "氧化古铜") if isinstance(task.input_json, dict) else "氧化古铜"
            if llm_analysis and llm_analysis.get("title"):
                pattern_type = llm_analysis.get("title")

            bronze_svg = generate_bronze_taotie_svg(pattern_type, style_filter, prompt=user_prompt, colors=llm_colors)
            bronze_url = save_generated_asset(f"{task_id}_bronze.svg", bronze_svg)
            
            desc = llm_analysis.get("mentor_description") if llm_analysis else f"萃取天津博物馆馆藏商周青铜器【{pattern_type}】艺术语言，已生成带云雷底纹与{style_filter}质感的原生矢量雕模图谱。"

            result = {
                "pattern_type": pattern_type,
                "style_filter": style_filter,
                "colored_image_url": bronze_url,
                "rendered_image_url": bronze_url,
                "vector_svg_url": bronze_url,
                "print_template_url": bronze_url,
                "description": desc,
                "historical_context": llm_analysis.get("historical_context") if llm_analysis else "源自蓟州古遗址与北方金石铭文，云雷纹衬地，气势凝重沉稳。",
                "color_palette": llm_analysis.get("color_palette") if llm_analysis else ["#4D5D53 (铜绿)", "#2B2625 (铁褐)", "#C59B27 (泥金)"],
                "craft_technique": llm_analysis.get("craft_technique") if llm_analysis else "范铸法浮雕双勾线条，地纹细密工整。",
                "llm_generated": bool(llm_analysis),
                "llm_model": model_name if llm_analysis else None
            }
        elif tool_type == "BALLAD":
            tune_name = llm_analysis.get("title", "津韵新声·时调大鼓") if llm_analysis else "津韵新声·时调大鼓"
            desc = "当前仅提供本地曲艺简谱版式参考，音符为固定示例，并非根据唱词自动作曲；演唱与伴奏音频服务尚未接入。"
            sheet_music_text = "1 1 5 5 | 6 6 5 - | 4 4 3 3 | 2 2 1 -"
            rhythm_style = "骆派京韵大鼓快板"
            ballad_lyrics = "运河水阔映津门，曲艺声声唱古今。"
            if llm_analysis and llm_analysis.get("craft_technique"):
                ballad_lyrics = llm_analysis.get("craft_technique")[:30]

            ballad_svg = generate_ballad_sheet_svg(tune_name, rhythm_style, sheet_music_text, ballad_lyrics, prompt=user_prompt, colors=llm_colors)
            ballad_url = save_generated_asset(f"{task_id}_ballad.svg", ballad_svg)

            result = {
                "tune_name": tune_name,
                "sheet_music_text": sheet_music_text,
                "audio_url": None,
                "audio_available": False,
                "custom_melody_available": False,
                "generation_method": "local_sheet_template",
                "rhythm_style": rhythm_style,
                "colored_image_url": ballad_url,
                "rendered_image_url": ballad_url,
                "completed_sketch_url": None,
                "sheet_music_url": ballad_url,
                "vector_svg_url": ballad_url,
                "print_template_url": ballad_url,
                "description": desc,
                "historical_context": llm_analysis.get("historical_context") if llm_analysis else "津门漕运文化孕育曲艺生态，杨柳青码头书场为津派时调大鼓核心传承地，积淀百年市井民俗文脉。",
                "color_palette": ["#B63E2C (扁鼓朱红)", "#D6A85C (泥金音符)", "#5C3317 (檀板紫檀)", "#FAF5EB (宣纸米白)"],
                "craft_technique": llm_analysis.get("craft_technique") if llm_analysis else "单楗打鼓，左手执鸳鸯板，五声音阶简谱与鼓板板眼对齐。",
                "llm_generated": bool(llm_analysis),
                "llm_model": model_name if llm_analysis else None
            }
        elif tool_type in ["LACQUER", "EMBROIDERY"]:
            title = llm_analysis.get("title", "漆绣纹样参考") if llm_analysis else "漆绣纹样参考"
            local_pattern = task.input_json.get("local_pattern", "FLORAL")
            lacquer_svg = generate_lacquer_design_svg(title, local_pattern, prompt=user_prompt, colors=llm_colors)
            lacquer_url = save_generated_asset(f"{task_id}_lacquer.svg", lacquer_svg)
            result = {
                "title": title,
                "local_pattern": local_pattern,
                "color_palette": extract_hex_colors(llm_colors, ["#C4A35A", "#D4AF37", "#2D5A4A", "#1A1817", "#F7F4ED"]),
                "colored_image_url": lacquer_url,
                "rendered_image_url": lacquer_url,
                "completed_sketch_url": None,
                "reference_sketch_url": task.input_json.get("sketch_url") or None,
                "vector_svg_url": lacquer_url,
                "print_template_url": None,
                "description": lacquer_template_description(),
                "generation_method": "local_template",
                "model_available": False,
                "sketch_redraw_available": False,
                "lora_available": False,
                "lora_applied": False,
                "historical_context": llm_analysis.get("historical_context") if llm_analysis else "津派大漆螺钿承继北方宫廷造办处推光漆器与民间螺钿镶嵌风貌，光泽深邃内敛。",
                "craft_technique": llm_analysis.get("craft_technique") if llm_analysis else "生漆刮灰底，螺钿薄片镶嵌，推光研磨显珠光。",
                "llm_generated": bool(llm_analysis),
                "llm_model": model_name if llm_analysis else None
            }
        else:  # No three-dimensional generator is configured.
            raise ValueError("三维生成服务尚未配置")

        finished = db.query(AiTask).filter(AiTask.task_id == task_id, AiTask.status == "RUNNING").update(
            {"status": "SUCCESS", "progress": 100, "result_summary_json": result}, synchronize_session=False
        )
        if not finished:
            db.rollback()
            return
        for url in {v for v in result.values() if isinstance(v, str) and v.startswith("/static/generated/")}:
            db.add(Asset(asset_type="IMAGE", object_key=url.removeprefix("/static/"),
                         file_url=url, mime_type="image/svg+xml", created_by=user_id))

        # 首次生成奖励能量值
        event_ref = f"ai_{task_id}"
        exist_ev = db.query(GrowthEvent).filter(
            GrowthEvent.user_id == user_id,
            GrowthEvent.event_type == "AI_CREATE",
            GrowthEvent.ref_id == event_ref
        ).first()
        if not exist_ev:
            db.add(GrowthEvent(
                user_id=user_id,
                event_type="AI_CREATE",
                ref_id=event_ref,
                value=20
            ))
            growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).with_for_update().first()
            if growth:
                growth.energy_value += 20
        db.commit()

    except Exception as exc:
        logger.warning("[AI Workshop] Task {} failed ({})", task_id, type(exc).__name__)
        db.rollback()
        try:
            message = str(exc) if isinstance(exc, image_generation.ImageGenerationError) else "生成失败，请重试或联系管理员"
            db.query(AiTask).filter(AiTask.task_id == task_id, AiTask.status.in_(["QUEUED", "RUNNING"])).update(
                {"status": "FAILED", "error_code": "INFERENCE_ERROR", "error_message": message}, synchronize_session=False)
            db.commit()
        except Exception as inner_e:
            logger.error(f"[AI Workshop] Failed to mark task as FAILED: {inner_e}")
    finally:
        db.close()

@router.post("/tasks")
def create_ai_task(
    req: CreateTaskRequest,
    bg: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.tool_type == "MESH_3D":
        raise HTTPException(503, "三维生成服务尚未配置")
    if req.generation_mode == "AI" and req.tool_type not in {"BRONZE", "SHADOW_PUPPET", "LACQUER", "EMBROIDERY"}:
        raise HTTPException(422, "此工坊暂不支持图像生成")
    prompt = req.input_payload.get("prompt")
    if req.tool_type == "BRONZE" or req.generation_mode == "AI":
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 1000:
            raise HTTPException(422, "请输入 1–1000 字的创作描述")
    if req.tool_type == "SHADOW_PUPPET":
        face = req.input_payload.get("face_style", "CLASSIC")
        prompt = req.input_payload.get("prompt")
        role = req.input_payload.get("role_type", "生角")
        if not isinstance(face, str) or face not in {"CLASSIC", "FLORAL", "BOLD"}:
            raise HTTPException(422, "不支持的脸谱样式")
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 1000:
            raise HTTPException(422, "请输入 1–1000 字的创作描述")
        if not isinstance(role, str) or not 1 <= len(role) <= 80:
            raise HTTPException(422, "角色类型无效")
        if "color_palette" in req.input_payload and not validated_input_palette(req.input_payload):
            raise HTTPException(422, "服饰颜色无效")
    if req.tool_type in {"LACQUER", "EMBROIDERY"}:
        prompt = req.input_payload.get("prompt")
        pattern = req.input_payload.get("local_pattern", "FLORAL")
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 1000:
            raise HTTPException(422, "请输入 1–1000 字的创作描述")
        if not isinstance(pattern, str) or pattern not in {"FLORAL", "GEOMETRIC", "AUSPICIOUS"}:
            raise HTTPException(422, "不支持的本地纹样类型")
        if "color_palette" in req.input_payload and not validated_input_palette(req.input_payload):
            raise HTTPException(422, "配色无效")
        sketch = req.input_payload.get("sketch_url")
        if sketch is not None and sketch != "":
            if not isinstance(sketch, str) or not sketch.startswith("/static/"):
                raise HTTPException(422, "草图资源无效")
            asset = db.query(Asset).filter_by(file_url=sketch, created_by=current_user["user_id"]).first()
            if not asset or not (asset.mime_type or "").startswith("image/"):
                raise HTTPException(404, "草图资源不存在")
            resolve_static_file(sketch)
    user_id = current_user["user_id"]
    payload = dict(req.input_payload)
    payload.pop("_generation_mode", None)
    if req.generation_mode == "AI":
        payload["_generation_mode"] = "AI"
    elif "generation_mode" in req.model_fields_set:
        payload["_generation_mode"] = "LOCAL"
    task_uuid = (hashlib.sha256(f"workshop:{user_id}:{req.request_id}".encode()).hexdigest()[:32]
                 if req.request_id else uuid.uuid4().hex)
    expire_image_tasks(db, user_id)
    db.query(SysUser).filter_by(id=user_id).with_for_update().first()
    existing = db.get(AiTask, task_uuid)
    if existing:
        if existing.user_id != user_id or existing.tool_type != req.tool_type or existing.input_json != payload or existing.model_id != req.model_id:
            raise HTTPException(409, "同一创作请求的内容发生变化，请重新提交")
        return success_response({"task_id": existing.task_id, "tool_type": existing.tool_type,
                                 "status": existing.status, "progress": existing.progress})
    if req.generation_mode == "AI":
        try:
            cfg = image_generation.resolve_connection(image_generation.read_settings(db))
            sketch = payload.get("sketch_url")
            if sketch:
                if not isinstance(sketch, str):
                    raise HTTPException(422, "参考图地址无效")
                if not cfg["supports_edit"]:
                    raise HTTPException(422, "当前模型未启用图片编辑，请移除参考图或联系管理员")
                image_generation.owned_reference(db, sketch, user_id)
        except image_generation.ImageGenerationError as exc:
            raise HTTPException(503, str(exc)) from None
        if db.query(AiTask).filter(AiTask.user_id == user_id, AiTask.status.in_(["QUEUED", "RUNNING"])).first():
            raise HTTPException(409, "已有创作正在进行，请等待完成或取消后再提交")

    new_task = AiTask(
        task_id=task_uuid,
        user_id=user_id,
        tool_type=req.tool_type,
        status="QUEUED",
        progress=10,
        model_id=req.model_id,
        model_version="1.0.0",
        input_json=payload,
        trace_id=f"trace_{task_uuid[:8]}"
    )
    db.add(new_task)
    db.commit()

    # 启动后台异步推理
    bg.add_task(execute_ai_inference, task_uuid, req.tool_type, user_id)

    return success_response({
        "task_id": task_uuid,
        "tool_type": req.tool_type,
        "status": "QUEUED",
        "progress": 10,
        "estimated_wait_seconds": 3
    }, message="AI创作任务已创建")

def shadow_template_description(role_type: str) -> str:
    return (f"已根据【{role_type}】的本地工艺模板生成彩色 SVG、轮廓图与 A4 比例纸样参考。"
            "纸样尚未经过实体装配或设备切割验证；三维模型生成尚未接入。")


def lacquer_template_description() -> str:
    return ("已根据文字、纹样类型和配色生成本地二维 SVG 参考。上传草图仅保留为创作参考，"
            "未进行轮廓识别或草图重绘，未应用 LoRA；色板不代表实物材料色号，实体制作尚未验证。")


def validated_input_palette(payload):
    supplied = payload.get("color_palette") if isinstance(payload, dict) else None
    if isinstance(supplied, list) and 1 <= len(supplied) <= 8 and all(
            isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", c) for c in supplied):
        return supplied
    return None


def task_result_for_client(task: AiTask):
    """Correct legacy capability claims without rewriting saved task records."""
    if not isinstance(task.result_summary_json, dict):
        return task.result_summary_json
    result = dict(task.result_summary_json)
    if result.get("generation_method") == "ai_image":
        return result
    if task.tool_type == "SHADOW_PUPPET":
        result.update(mesh_3d_url=None, model_available=False, generation_method="local_template",
                      description=shadow_template_description(result.get("role_type") or "皮影角色"))
        # Earlier local tasks used this palette in the SVG but returned an unrelated default legend.
        supplied_colors = validated_input_palette(task.input_json)
        if supplied_colors and not result.get("llm_generated"):
            result["color_palette"] = extract_hex_colors(supplied_colors)
    elif task.tool_type == "BALLAD":
        result.update(audio_url=None, audio_available=False, custom_melody_available=False,
                      completed_sketch_url=None, generation_method="local_sheet_template",
                      description="此任务提供本地简谱版式与固定示例音符，不是自动作曲；演唱与伴奏音频服务尚未接入。")
    elif task.tool_type == "MESH_3D":
        result.update(model_url=None, model_available=False, face_count=None,
                      description="此历史任务仅包含二维示意预览，三维模型生成服务尚未接入。")
    elif task.tool_type in {"LACQUER", "EMBROIDERY"}:
        result.update(completed_sketch_url=None, print_template_url=None, model_available=False,
                      generation_method="local_template", sketch_redraw_available=False,
                      lora_available=False, lora_applied=False, description=lacquer_template_description())
    return result


@router.get("/tasks/latest")
def get_latest_task(
    tool_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expire_image_tasks(db, current_user["user_id"])
    query = db.query(AiTask).filter(AiTask.user_id == current_user["user_id"])
    if tool_type:
        query = query.filter(AiTask.tool_type == tool_type)
    task = query.order_by(AiTask.created_at.desc()).first()
    if not task:
        return success_response(None)
    return success_response({
        "task_id": task.task_id,
        "tool_type": task.tool_type,
        "status": task.status,
        "progress": task.progress,
        "input": task.input_json,
        "result": task_result_for_client(task),
        "collected": task_collected(db, task),
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None
    })

@router.get("/tasks/{task_id}")
def get_ai_task(task_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    expire_image_tasks(db, current_user["user_id"])
    task = db.query(AiTask).filter(AiTask.task_id == task_id, AiTask.user_id == current_user["user_id"]).first()
    if not task:
        return error_response(code=4040, message="任务不存在")
    
    return success_response({
        "task_id": task.task_id,
        "tool_type": task.tool_type,
        "status": task.status,
        "progress": task.progress,
        "model_version": task.model_version,
        "input": task.input_json,
        "result": task_result_for_client(task),
        "collected": task_collected(db, task),
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None
    })

class TaskFavoriteRequest(BaseModel):
    collected: bool


@router.post("/tasks/{task_id}/favorite")
def save_task_favorite(task_id: str, req: TaskFavoriteRequest, current_user: dict = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    db.query(SysUser).filter_by(id=user_id).with_for_update().one()
    task = db.query(AiTask).filter_by(task_id=task_id, user_id=user_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    asset = task_image_asset(db, task)
    if not asset:
        raise HTTPException(409, "请先完成创作")
    owned_task_for_asset(db, asset, user_id)
    key = (user_id, "ASSET", asset.id)
    record = db.get(UserCollection, key)
    if req.collected and not record:
        db.add(UserCollection(user_id=user_id, target_type="ASSET", target_id=asset.id))
    elif not req.collected and record:
        db.delete(record)
    db.commit()
    return success_response({"collected":req.collected})


@router.post("/tasks/{task_id}/cancel")
def cancel_ai_task(task_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(AiTask).filter(AiTask.task_id == task_id, AiTask.user_id == current_user["user_id"]).with_for_update().first()
    if not task:
        return error_response(code=4040, message="任务不存在")
    if task.status not in ["QUEUED", "RUNNING"]:
        return error_response(code=4090, message="已完成的任务不可取消")
    
    task.status = "CANCELLED"
    db.commit()
    message = ("任务已取消；已发出的模型请求可能仍会执行" if task.input_json.get("_generation_mode") == "AI" else "任务已取消")
    return success_response({"task_id": task_id, "status": "CANCELLED"}, message=message)

class UpdateAiModelRequest(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    prompt_template: Optional[str] = None
    config: Optional[dict] = None

@router.get("/models")
def list_ai_models(task_type: Optional[str] = None, all_status: bool = False, current_user: Optional[dict] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    is_admin = bool(current_user and current_user["role_code"] == "ADMIN")
    if all_status and not is_admin:
        raise HTTPException(403, "仅管理员可查询全部模型")
    query = db.query(AiModel)
    if not all_status:
        query = query.filter(AiModel.status == "ACTIVE")
    if task_type:
        query = query.filter(AiModel.task_type == task_type)
    models = query.all()
    return success_response([{
        "id": m.id,
        "code": m.code,
        "name": m.name,
        "task_type": m.task_type,
        "version": m.version,
        "provider": m.provider,
        "config": m.config_json if is_admin else None,
        "prompt_template": m.prompt_template if is_admin else None,
        "status": m.status,
        "is_default": m.is_default
    } for m in models])

@router.put("/models/{model_id}")
def update_ai_model(model_id: int, req: UpdateAiModelRequest, current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    m = db.query(AiModel).filter(AiModel.id == model_id).first()
    if not m:
        return error_response(code=4040, message="模型不存在")
    if req.name is not None:
        m.name = req.name
    if req.version is not None:
        m.version = req.version
    if req.status is not None:
        m.status = req.status
    if req.prompt_template is not None:
        m.prompt_template = req.prompt_template
    if req.config is not None:
        m.config_json = req.config
    db.commit()
    return success_response({"id": m.id, "status": m.status, "name": m.name}, message="模型配置已更新")

@router.post("/assets/upload")
async def upload_asset(file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """真实多模态素材与学生作品文件上传 (含安全白名单校验)"""
    allowed_exts = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".mp4", ".glb"}
    raw_ext = os.path.splitext(file.filename or "")[1].lower()
    if raw_ext not in allowed_exts:
        return error_response(code=4003, message="不支持的文件格式，仅允许上传图片、微课视频或3D非遗模型")

    content = await file.read(50 * 1024 * 1024 + 1)
    if len(content) > 50 * 1024 * 1024:
        return error_response(code=4004, message="文件体积超过限制 (最大 50MB)")

    mime_types = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
                  ".jpeg": "image/jpeg", ".webp": "image/webp", ".mp4": "video/mp4", ".glb": "model/gltf-binary"}
    if raw_ext == ".svg":
        try:
            content = sanitize_svg(content).encode("utf-8")
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    else:
        valid = ((raw_ext == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
                 or (raw_ext in {".jpg", ".jpeg"} and content.startswith(b"\xff\xd8\xff"))
                 or (raw_ext == ".webp" and content[:4] == b"RIFF" and content[8:12] == b"WEBP")
                 or (raw_ext == ".mp4" and content[4:8] == b"ftyp")
                 or (raw_ext == ".glb" and content.startswith(b"glTF")))
        if not valid:
            raise HTTPException(400, "文件内容与扩展名不匹配")

    file_id = f"{uuid.uuid4().hex}{raw_ext}"
    dest_path = os.path.join(STATIC_UPLOADS_DIR, file_id)
    with open(dest_path, "wb") as f:
        f.write(content)
    file_url = f"/static/uploads/{file_id}"
    db.add(Asset(asset_type="IMAGE" if raw_ext in {".svg", ".png", ".jpg", ".jpeg", ".webp"} else "MEDIA",
                 object_key=f"uploads/{file_id}", file_url=file_url, mime_type=mime_types[raw_ext],
                 size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                 created_by=current_user["user_id"]))
    db.commit()
    return success_response({
        "file_id": file_id,
        "filename": file.filename,
        "file_url": file_url,
        "size": len(content)
    }, message="文件上传成功")

@router.post("/assets/presign")
def presign_upload(asset_type: str = "IMAGE", current_user: dict = Depends(get_current_user)):
    """对象存储预签名/直传接口"""
    file_id = uuid.uuid4().hex
    return success_response({
        "upload_url": "/api/ai/assets/upload",
        "object_key": f"uploads/{asset_type.lower()}/{file_id}.png",
        "file_url": f"/static/uploads/{file_id}.png",
        "asset_type": asset_type
    })

class EvaluateArtworkRequest(BaseModel):
    image_url: str
    heritage_type: str = "SHADOW_PUPPET"
    title: Optional[str] = "非遗手作作品"
    notes: Optional[str] = None

class ArtworkEvaluation(BaseModel):
    total_score: float = Field(..., ge=0, le=100)
    stars: int = Field(..., ge=1, le=5)
    composition_score: int = Field(..., ge=0, le=100)
    color_score: int = Field(..., ge=0, le=100)
    technique_score: int = Field(..., ge=0, le=100)
    composition_feedback: str
    color_feedback: str
    technique_feedback: str
    mentor_comment: str


@router.post("/evaluate")
def evaluate_artwork(req: EvaluateArtworkRequest, current_user: dict = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.file_url == req.image_url,
                                  Asset.created_by == current_user["user_id"]).first()
    if not asset:
        raise HTTPException(404, "作品不存在或无权访问")
    path = resolve_static_file(req.image_url)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(path.suffix.lower())
    if not mime:
        raise HTTPException(415, "审美测评需要上传 PNG、JPEG 或 WebP 图片")
    if path.stat().st_size > 10 * 1024 * 1024:
        raise HTTPException(413, "测评图片不能超过10MB")
    client, cfg = get_llm_client_and_config(db)
    model_name = cfg.get("vision_model_name") if cfg else None
    if not client or not model_name:
        raise HTTPException(503, "图像测评服务尚未配置，请联系管理员")
    content = path.read_bytes()
    prompt = f"请评价非遗作品《{req.title}》，门类：{req.heritage_type}，手记：{req.notes or ''}。"
    prompt += "只返回JSON，包含total_score、stars、composition_score、color_score、technique_score，以及composition_feedback、color_feedback、technique_feedback、mentor_comment。分数0至100，星级1至5。"
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(content).decode()}"}}
            ]}], max_tokens=2048, temperature=0.3, timeout=30,
        )
        evaluation = ArtworkEvaluation.model_validate(extract_json_from_llm(response.choices[0].message.content or ""))
    except Exception as exc:
        logger.warning("Image evaluation failed: {}", type(exc).__name__)
        raise HTTPException(502, "图像测评暂时不可用，请稍后重试") from exc
    ref = hashlib.sha256(content).hexdigest()
    growth = db.query(UserGrowth).filter(UserGrowth.user_id == current_user["user_id"]).with_for_update().first()
    existing = db.query(GrowthEvent).filter(GrowthEvent.user_id == current_user["user_id"],
                                           GrowthEvent.event_type == "AI_EVALUATION", GrowthEvent.ref_id == ref).first()
    reward = 30 if growth and not existing else 0
    if reward:
        db.add(GrowthEvent(user_id=current_user["user_id"], event_type="AI_EVALUATION", ref_id=ref, value=reward))
        growth.energy_value += reward
        if growth.energy_value >= 1000:
            growth.level_code = "LV3_CRAFTSMAN"
        elif growth.energy_value >= 500:
            growth.level_code = "LV2_JOURNEYMAN"
    db.commit()
    return success_response({
        "evaluation_id": f"JY-EVAL-{ref[:12]}", "heritage_name": req.heritage_type,
        "title": req.title, "image_url": req.image_url,
        "total_score": evaluation.total_score, "stars": evaluation.stars,
        "dimensions": {
            "composition": {"name": "构图均衡度", "score": evaluation.composition_score, "feedback": evaluation.composition_feedback},
            "color": {"name": "色彩美学", "score": evaluation.color_score, "feedback": evaluation.color_feedback},
            "technique": {"name": "线条与工艺", "score": evaluation.technique_score, "feedback": evaluation.technique_feedback}
        },
        "mentor_comment": evaluation.mentor_comment, "energy_reward": reward,
        "certified_by": "AI 图像测评", "created_at": datetime.utcnow().isoformat(),
        "llm_generated": True, "llm_model": model_name,
    }, message="作品图像测评完成")
