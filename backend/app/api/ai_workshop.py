import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.database import get_db, SessionLocal, redis_client
from app.core.security import get_current_user
from app.schemas.common import success_response, error_response
from app.models.entities import AiTask, AiModel, Asset, GrowthEvent, UserGrowth

router = APIRouter(prefix="/ai", tags=["AI工坊"])

class CreateTaskRequest(BaseModel):
    tool_type: str  # SHADOW_PUPPET, BRONZE, BALLAD, LACQUER, EMBROIDERY, MESH_3D
    input_payload: Dict[str, Any]
    model_id: Optional[int] = None

def simulate_ai_inference(task_id: str, tool_type: str, user_id: int):
    """
    异步多模态推理 Worker：更新任务进度 25% -> 50% -> 75% -> 100% 并写入非遗生成资产
    """
    db = SessionLocal()
    try:
        task = db.query(AiTask).filter(AiTask.task_id == task_id).first()
        if not task:
            return
        
        # 1. 模拟排队和运行
        task.status = "RUNNING"
        task.progress = 25
        db.commit()
        
        # 2. 依据不同的非遗工具类型生成专属天津非遗艺术资产
        if tool_type == "SHADOW_PUPPET":
            # 皮影生成：线稿提取、传统套色、3D可动骨骼
            result = {
                "role_type": task.input_json.get("role_type", "生角·津门书生"),
                "line_art_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600",
                "colored_image_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800",
                "mesh_3d_url": "https://modelviewer.dev/shared-assets/models/Astronaut.glb",
                "print_template_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1200",
                "description": "基于传统津派皮影雕镂技艺生成。头戴文生巾，驴皮透光材质经多次刮浆渲染，关节已做三签铆接标记，可直接输出激光切割或A4手工打印。"
            }
        elif tool_type == "BRONZE":
            # 青铜纹样：氧化、拓片、彩色珐琅
            result = {
                "pattern_type": task.input_json.get("pattern_type", "饕餮纹"),
                "style_filter": task.input_json.get("style", "氧化古铜"),
                "rendered_image_url": "https://images.unsplash.com/photo-1569783727725-b88d3e230756?w=800",
                "vector_svg_url": "https://img.icons8.com/color/96/antique.png",
                "description": "萃取天津博物馆馆藏青铜礼器饕餮纹神韵，结合现代几何对称美学，已应用铜绿氧化与金石拓片质感。"
            }
        elif tool_type == "BALLAD":
            # 鼓曲哼唱：简谱、三弦鼓点音频
            result = {
                "tune_name": "津韵新声·时调大鼓",
                "sheet_music_text": "1 1 5 5 | 6 6 5 - | 4 4 3 3 | 2 2 1 -",
                "audio_url": "https://actions.google.com/sounds/v1/water/rain_heavy.ogg",
                "rhythm_style": "骆派京韵大鼓快板",
                "description": "AI已为您生成的唱词完成五声音阶配曲，并融合传统三弦伴奏与津门书场鼓板节奏。"
            }
        elif tool_type == "LACQUER" or tool_type == "EMBROIDERY":
            # 漆艺螺钿 / 刺绣补全
            result = {
                "color_palette": ["#8B4A2F (岱红)", "#D6A85C (泥金)", "#2F4F4F (螺钿青)", "#1A1A1A (生漆黑)"],
                "completed_sketch_url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800",
                "description": "AI对草图线条进行了流线型平滑修整，并根据古法大漆髹饰标准匹配了中国传统天然矿物色系。"
            }
        else: # MESH_3D
            result = {
                "model_url": "https://modelviewer.dev/shared-assets/models/Astronaut.glb",
                "face_count": 12800,
                "texture_format": "GLTF/GLB"
            }

        task.status = "SUCCESS"
        task.progress = 100
        task.result_summary_json = result
        db.commit()

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
            growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).first()
            if growth:
                growth.energy_value += 20
            db.commit()

    finally:
        db.close()

@router.post("/tasks")
def create_ai_task(
    req: CreateTaskRequest,
    bg: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    task_uuid = uuid.uuid4().hex

    new_task = AiTask(
        task_id=task_uuid,
        user_id=user_id,
        tool_type=req.tool_type,
        status="QUEUED",
        progress=10,
        model_id=req.model_id or 1,
        model_version="1.0.0",
        input_json=req.input_payload,
        trace_id=f"trace_{task_uuid[:8]}"
    )
    db.add(new_task)
    db.commit()

    # 启动后台异步推理
    bg.add_task(simulate_ai_inference, task_uuid, req.tool_type, user_id)

    return success_response({
        "task_id": task_uuid,
        "tool_type": req.tool_type,
        "status": "QUEUED",
        "progress": 10,
        "estimated_wait_seconds": 3
    }, message="AI创作任务已创建")

@router.get("/tasks/{task_id}")
def get_ai_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(AiTask).filter(AiTask.task_id == task_id).first()
    if not task:
        return error_response(code=4040, message="任务不存在")
    
    return success_response({
        "task_id": task.task_id,
        "tool_type": task.tool_type,
        "status": task.status,
        "progress": task.progress,
        "model_version": task.model_version,
        "input": task.input_json,
        "result": task.result_summary_json,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None
    })

@router.post("/tasks/{task_id}/cancel")
def cancel_ai_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(AiTask).filter(AiTask.task_id == task_id).first()
    if not task:
        return error_response(code=4040, message="任务不存在")
    if task.status in ["SUCCESS", "FAILED"]:
        return error_response(code=4090, message="已完成的任务不可取消")
    
    task.status = "CANCELLED"
    db.commit()
    return success_response({"task_id": task_id, "status": "CANCELLED"}, message="任务已取消")

@router.get("/models")
def list_ai_models(task_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AiModel).filter(AiModel.status == "ACTIVE")
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
        "config": m.config_json,
        "is_default": m.is_default
    } for m in models])

@router.post("/assets/presign")
def presign_upload(asset_type: str = "IMAGE"):
    # 模拟对象存储预签名上传契约
    file_id = uuid.uuid4().hex
    return success_response({
        "upload_url": f"/api/upload/mock/{file_id}",
        "object_key": f"uploads/{asset_type.lower()}/{file_id}.webp",
        "file_url": f"https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800",
        "asset_type": asset_type
    })
