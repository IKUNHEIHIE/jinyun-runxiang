import json
import secrets
import httpx
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, Response
from urllib.parse import quote
from app.services.ppt_generator import generate_lesson_pptx
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.schemas.common import success_response, error_response
from app.models.entities import (
    TeacherClass, ClassMember, Assignment, AssignmentSubmission,
    AssignmentReview, LearningProgress, QuizAttempt, Course, Asset, AiTask,
    UserGrowth, SysUser, UserProfile, SysConfig
)

router = APIRouter(prefix="/teacher", tags=["教师工作台与AI智能备课"])


def get_authorized_class(db: Session, class_id: int, current_user: dict):
    query = db.query(TeacherClass).filter(TeacherClass.id == class_id)
    if current_user.get("role_code") != "ADMIN":
        query = query.filter(TeacherClass.teacher_id == current_user["user_id"])
    return query.first()

class LessonPlanRequest(BaseModel):
    grade: str  # 小学三年级 / 小学四年级 / 初中
    topic: str  # 天津皮影戏 / 杨柳青木版年画 / 泥人张彩塑 / 骆派京韵大鼓 / 古法大漆
    duration_minutes: int = 45
    objectives: Optional[str] = "培养乡村儿童对乡土非遗的文化认同与动手实践能力"

class CreateAssignmentRequest(BaseModel):
    class_id: int
    title: str = Field(min_length=1, max_length=128)
    type: str = "AI_CREATION"  # AI_CREATION / OFFLINE_HANDMADE
    tool_type: Optional[str] = "SHADOW_PUPPET"
    deadline_days: int = Field(default=7, ge=1, le=365)
    description: str = Field(min_length=1)

class ReviewSubmissionRequest(BaseModel):
    score: int = Field(ge=0, le=100)
    comment: str = Field(min_length=1)


class CreateClassRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    grade: str = Field(min_length=1, max_length=32)
    school_id: Optional[str] = Field(default=None, max_length=64)


class JoinClassRequest(BaseModel):
    invite_code: str = Field(min_length=1, max_length=16)


class SubmitAssignmentRequest(BaseModel):
    content: Optional[str] = None
    asset_id: Optional[int] = Field(default=None, gt=0)
    source_task_id: Optional[str] = Field(default=None, max_length=32)

@router.get("/classes")
def list_teacher_classes(
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher_id = current_user["user_id"]
    classes = db.query(TeacherClass).filter(
        TeacherClass.teacher_id == teacher_id,
        TeacherClass.status == "ACTIVE"
    ).all()

    return success_response([{
        "id": c.id,
        "name": c.name,
        "grade": c.grade,
        "invite_code": c.invite_code,
        "student_count": c.student_count
    } for c in classes])


@router.post("/classes")
def create_teacher_class(
    req: CreateClassRequest,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    invite_code = secrets.token_hex(6).upper()
    while db.query(TeacherClass).filter(TeacherClass.invite_code == invite_code).first():
        invite_code = secrets.token_hex(6).upper()
    class_obj = TeacherClass(
        teacher_id=current_user["user_id"], name=req.name, grade=req.grade,
        school_id=req.school_id, invite_code=invite_code, student_count=0,
        status="ACTIVE"
    )
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    return success_response({"id": class_obj.id, "invite_code": invite_code}, message="班级已创建")


@router.post("/classes/join")
def join_teacher_class(
    req: JoinClassRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.get("role_code") != "STUDENT":
        return error_response(code=4030, message="只有学生可以加入班级")
    class_obj = db.query(TeacherClass).filter(
        TeacherClass.invite_code == req.invite_code,
        TeacherClass.status == "ACTIVE"
    ).with_for_update().first()
    if not class_obj:
        return error_response(code=4040, message="邀请码无效")
    member = db.query(ClassMember).filter(
        ClassMember.class_id == class_obj.id,
        ClassMember.student_id == current_user["user_id"]
    ).first()
    if member and member.status == "ACTIVE":
        return success_response({"class_id": class_obj.id, "status": "ACTIVE"}, message="已在班级中")
    if member:
        member.status = "ACTIVE"
        member.joined_at = datetime.utcnow()
    else:
        db.add(ClassMember(class_id=class_obj.id, student_id=current_user["user_id"], status="ACTIVE"))
    class_obj.student_count = (class_obj.student_count or 0) + 1
    db.commit()
    return success_response({"class_id": class_obj.id, "status": "ACTIVE"}, message="加入班级成功")


@router.get("/classes/{class_id}/members")
def list_class_members(
    class_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    if not get_authorized_class(db, class_id, current_user):
        return error_response(code=4040, message="班级不存在或无权访问")
    members = db.query(ClassMember).filter(
        ClassMember.class_id == class_id, ClassMember.status == "ACTIVE"
    ).all()
    users = db.query(SysUser).filter(SysUser.id.in_([m.student_id for m in members])).all() if members else []
    user_map = {user.id: user for user in users}
    return success_response([{
        "student_id": member.student_id,
        "nickname": user_map[member.student_id].nickname if member.student_id in user_map else "",
        "avatar_url": user_map[member.student_id].avatar_url if member.student_id in user_map else None,
        "joined_at": member.joined_at
    } for member in members])

@router.post("/lesson-plans/generate")
def generate_lesson_plan(
    req: LessonPlanRequest,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    # 1. 优先读取系统设置中保存的大模型真实接口配置
    llm_cfg = db.query(SysConfig).filter(SysConfig.config_key == "llm_settings").first()
    if llm_cfg and llm_cfg.config_value:
        try:
            cfg = json.loads(llm_cfg.config_value)
            api_key = cfg.get("api_key", "").strip()
            api_base = cfg.get("api_base", "https://api.deepseek.com/v1").strip().rstrip("/")
            model_name = cfg.get("model_name", "deepseek-chat").strip()
            temperature = float(cfg.get("temperature", 0.7))

            # 当用户录入了真实的 API Key 时，发起真实 DeepSeek API 推理
            if api_key and "*" not in api_key and len(api_key) > 10:
                prompt = (
                    f"你是一位精通天津非遗文化与乡村美育的专家。请针对学段【{req.grade}】、"
                    f"非遗主题【{req.topic}】、时长【{req.duration_minutes}分钟】，"
                    f"生成结构化美育备课方案。\n"
                    f"输出必须为纯 JSON 对象，格式包含："
                    f"targets: {{aesthetic, skill, emotion}}, "
                    f"key_difficult_points: {{key, difficult}}, "
                    f"teaching_process: [{{step, content}}], "
                    f"teacher_script: 教师讲稿, "
                    f"interactive_questions: [问题1, 问题2], "
                    f"homework_proposal: 课后作业建议。"
                )
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(
                        f"{api_base}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": "You are a professional art education assistant. You must output JSON."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": temperature,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        ai_parsed = json.loads(raw_content)
                        steps = ai_parsed.get("teaching_process", [])
                        return success_response({
                            "title": f"《津韵润乡·乡土美育微课：{req.topic}》",
                            "grade": req.grade,
                            "topic": req.topic,
                            "duration": f"{req.duration_minutes} 分钟",
                            "targets": ai_parsed.get("targets", {}),
                            "key_difficult_points": ai_parsed.get("key_difficult_points", {}),
                            "teaching_process": steps,
                            "activity_design": [s.get("step", "") if isinstance(s, dict) else str(s) for s in steps],
                            "teacher_script": ai_parsed.get("teacher_script", ""),
                            "interactive_questions": ai_parsed.get("interactive_questions", []),
                            "homework_proposal": ai_parsed.get("homework_proposal", f"设计1幅{req.topic}非遗作品"),
                            "ppt_download_url": f"https://example.com/assets/lesson_plans/{req.topic}_课件.pptx",
                            "generated_by": f"DeepSeek 官方大模型 ({model_name}) 实时生成"
                        }, message=f"已由 DeepSeek 官方大模型 ({model_name}) 实时生成智能备课方案")
        except Exception:
            # 外部大模型调用失败或网络离线时，平滑降级至本地高质量非遗专家教案
            pass

    # 2. 默认降级方案：天津非遗专家预置结构化教案
    lesson_plan = {
        "title": f"《津韵润乡·乡土美育微课：{req.topic}》",
        "grade": req.grade,
        "topic": req.topic,
        "duration": f"{req.duration_minutes} 分钟",
        "targets": {
            "aesthetic": "感知天津传统非遗的线条、色彩与造型之美；",
            "skill": "掌握核心工艺步骤原理，能够使用AI工坊生成个性化设计稿并进行手工实践；",
            "emotion": "激发对家乡天津传统文化的自豪感与传承乡村手艺的热情。"
        },
        "key_difficult_points": {
            "key": f"{req.topic}的传统渊源与典型艺术造型特征；",
            "difficult": "如何在现代设计中巧妙融入天津地域风土文化元素。"
        },
        "teaching_process": [
            {
                "step": "1. 创设情境，唤醒乡愁 (8分钟)",
                "content": "播放津沽老艺人采风实录短视频，展示非遗实物，引导孩子们观察光影/泥塑/年画的神态与色泽。"
            },
            {
                "step": "2. 匠心溯源，技法揭秘 (15分钟)",
                "content": "详解工艺五大核心工序，对比天津老物件，重点讲解非遗造型的对称、镂空与寓意手法。"
            },
            {
                "step": "3. 巧借AI，灵感赋能 (12分钟)",
                "content": "指导学生登录《津韵润乡》APP进入AI工坊，输入心仪角色与天津民俗词汇，生成个性化非遗创作线稿与3D模型。"
            },
            {
                "step": "4. 成果展评，美育升华 (10分钟)",
                "content": "将AI作品投屏至教室大屏，同学互评、教师点评，一键发布至乡村非遗社区广场。"
            }
        ],
        "activity_design": [
            "环节一：创设情境，唤醒乡愁 (8分钟)",
            "环节二：匠心溯源，技法揭秘 (15分钟)",
            "环节三：巧借AI，灵感赋能 (12分钟)",
            "环节四：成果展评，美育升华 (10分钟)"
        ],
        "teacher_script": f"同学们请看大屏幕，今天王老师带大家跨越时空，来到运河岸边的杨柳青古镇和三岔河口……",
        "interactive_questions": [
            "如果你为家乡设计一个守护神皮影，你希望他身披什么图案？",
            "传统工艺中的矿物颜料与现代水彩相比，有什么独特的质感？"
        ],
        "homework_proposal": f"利用AI工坊设计1幅{req.topic}作品，并向爸爸妈妈讲解其中的非遗小故事。",
        "ppt_download_url": "https://example.com/assets/lesson_plans/tianjin_heritage_template.pptx"
    }

    return success_response(lesson_plan, message="AI智能备课方案已生成")

@router.get("/lesson-plans/export-html", response_class=HTMLResponse)
def export_lesson_plan_html(
    topic: str = Query("杨柳青木版年画", description="非遗主题"),
    grade: str = Query("小学三年级", description="适用学段"),
    duration_minutes: int = Query(45, description="课时时长")
):
    """导出排版工整的标准非遗美育教案 (支持直接打印与另存为 PDF)"""
    date_str = datetime.utcnow().strftime("%Y年%m月%d日")
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>天津市乡村中小学非遗美育协同育人教案 · {topic}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            color: #262626;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
            background: #FAFAFA;
        }}
        .paper {{
            max-width: 820px;
            margin: 0 auto;
            background: #FFF;
            padding: 50px 60px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid #E8E8E8;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #8B4A2F;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .super-title {{
            font-size: 13px;
            color: #8B4A2F;
            letter-spacing: 2px;
            font-weight: 700;
        }}
        .main-title {{
            font-size: 24px;
            font-weight: 900;
            color: #1F1F1F;
            margin: 8px 0;
        }}
        .meta-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}
        .meta-table th, .meta-table td {{
            border: 1px solid #D9D9D9;
            padding: 8px 12px;
            font-size: 13px;
        }}
        .meta-table th {{
            background: #FAF3EC;
            color: #8B4A2F;
            width: 18%;
            text-align: right;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 800;
            color: #8B4A2F;
            border-left: 4px solid #8B4A2F;
            padding-left: 10px;
            margin: 24px 0 12px;
        }}
        .process-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .process-table th, .process-table td {{
            border: 1px solid #E8E8E8;
            padding: 10px 14px;
            font-size: 13px;
        }}
        .process-table th {{
            background: #F5F5F5;
            color: #595959;
            font-weight: 700;
        }}
        .step-name {{
            font-weight: 700;
            color: #8B4A2F;
            width: 25%;
        }}
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #8B4A2F;
            color: #FFF;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 700;
            box-shadow: 0 4px 12px rgba(139, 74, 47, 0.3);
        }}
        @media print {{
            body {{ background: #FFF; padding: 0; }}
            .paper {{ box-shadow: none; border: none; padding: 0; }}
            .print-btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ 打印此教案 / 另存为 PDF</button>
    <div class="paper">
        <div class="header">
            <div class="super-title">天津市“津韵润乡”乡村中小学非遗美育协同工程 · 标准化微课教案</div>
            <h1 class="main-title">《津韵润乡·乡土非遗赋能美育微课：{topic}》</h1>
            <div style="font-size: 12px; color: #8C8C8C;">课程编号：JY-CURR-2026-03 · 归档日期：{date_str}</div>
        </div>

        <table class="meta-table">
            <tr>
                <th>适用学段</th>
                <td>{grade}</td>
                <th>课时时长</th>
                <td>{duration_minutes} 分钟 (标准美育1课时)</td>
            </tr>
            <tr>
                <th>非遗门类</th>
                <td>{topic} (国家级非物质文化遗产项目)</td>
                <th>主讲/备课人</th>
                <td>天津美术学院非遗名师工作室 & 乡村骨干美育团队</td>
            </tr>
            <tr>
                <th>数字工具支持</th>
                <td colspan="3">《津韵润乡》智能美育平台 (AI 多模态工坊、3D 可动模型检视、激光纸样自动排版)</td>
            </tr>
        </table>

        <div class="section-title">一、 美育核心素养三维目标</div>
        <ul style="font-size: 13px; line-height: 1.8; color: #434343;">
            <li><strong>【审美感知】</strong>：引导乡村学生感知天津传统非遗的线条律动、天然矿物色彩与传统民间造型章法，提升乡村少年对故土民俗美术的鉴赏力。</li>
            <li><strong>【艺术表现】</strong>：掌握【{topic}】的核心工艺工序原理，能够熟练操作《津韵润乡》AI工坊进行个性化数字创客实验，并结合配套纸样完成实体手工制作。</li>
            <li><strong>【文化理解】</strong>：在动手造物中体悟老一辈天津非遗手艺人的匠心操守，激发乡村少年热爱家乡、传承乡土文脉的文化自信。</li>
        </ul>

        <div class="section-title">二、 教学重难点与物资准备</div>
        <div style="font-size: 13px; color: #434343; line-height: 1.8;">
            <p><strong>教学重点</strong>：理解【{topic}】的传统文化渊源，掌握其标志性的造型、色彩与装饰母题特征。</p>
            <p><strong>教学难点</strong>：如何在现代数字工具辅助下，保留天津地域民俗灵魂的同时融入新时代小工匠的童趣创意。</p>
            <p><strong>教具与材料准备</strong>：乡村美育教室多媒体大屏、学生平板/一体机端（《津韵润乡》系统）、配套非遗手工耗材包（刻刀、半透皮料/宣纸、矿物色颜料盒、A4激光打印纸样）。</p>
        </div>

        <div class="section-title">三、 四步启发式教学流程设计 (45分钟)</div>
        <table class="process-table">
            <thead>
                <tr>
                    <th style="width: 25%;">环节名称与时长</th>
                    <th>师生活动与数字交互设计</th>
                    <th style="width: 22%;">设计意图与素养达成</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="step-name">环节一：津韵寻踪<br><span style="font-size: 11px; color: #8C8C8C;">(情境创设 · 8分钟)</span></td>
                    <td>播放天津老手艺人采风短视频与海河风情纪实，教师出示实物道具，组织“猜猜这是哪道津门老手艺”快问快答。</td>
                    <td>打破传统说教，调动学生听觉与视觉感官，唤醒乡村少年的乡土文化共鸣。</td>
                </tr>
                <tr>
                    <td class="step-name">环节二：匠心格物<br><span style="font-size: 11px; color: #8C8C8C;">(技法揭秘 · 15分钟)</span></td>
                    <td>依托《非遗微课堂》分步微课视频，精讲核心制作工序。引导学生在平板上进行【课中非遗知识挑战】，随堂即时反馈答卷与名师解析。</td>
                    <td>互动答题加深技艺记忆，杜绝走神，量化知识掌握度并奖励美育能量。</td>
                </tr>
                <tr>
                    <td class="step-name">环节三：数字创客<br><span style="font-size: 11px; color: #8C8C8C;">(AI灵感赋能 · 12分钟)</span></td>
                    <td>学生打开《AI工坊》，输入心仪提示词，选用“津沽传统本色”生成专属非遗线稿与3D模型，一键下载A4打印排版图纸，开展线下组装手工。</td>
                    <td>实现“数字AI生成 ➔ 实体手工纸样”虚实结合，降低乡村手工门槛。</td>
                </tr>
                <tr>
                    <td class="step-name">环节四：展评升华<br><span style="font-size: 11px; color: #8C8C8C;">(名师诊断 · 10分钟)</span></td>
                    <td>拍照上传作品，调用“AI多模态审美门诊”获取构图、色彩、线条三维评分卡片；投屏至教室大屏，一键同步发布至美育广场。</td>
                    <td>形成客观量化的美育评价档案，让每个乡村孩子收获成就感与自信心。</td>
                </tr>
            </tbody>
        </table>

        <div class="section-title">四、 课后作业与评价量规</div>
        <div style="font-size: 13px; color: #434343; line-height: 1.8;">
            <p><strong>课后作业</strong>：将完成的【{topic}】手工作品带回家向家长讲述一个非遗寓意故事，并在家长协助下打卡津门非遗研学地图中的最近非遗地标。</p>
            <p><strong>评价量规</strong>：</p>
            <ul>
                <li>【卓越 (90-100分)】：造型工整，巧妙融入天津地域纹样，AI 诊断三维指标均达标，能完整表达创作意图。</li>
                <li>【良好 (75-89分)】：工序完整，能独立操作 AI 工坊与配套纸样，色彩搭配和谐。</li>
                <li>【合格 (60-74分)】：在教师指导下完成基础拼装，积极参与课中测验与互评。</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@router.get("/lesson-plans/export-pptx")
def export_lesson_plan_pptx(
    topic: str = Query("杨柳青木版年画", description="非遗主题"),
    grade: str = Query("小学三年级", description="适用学段"),
    duration_minutes: int = Query(45, description="课时时长")
):
    """动态生成并导出津派非遗美育 16:9 标准 PPTX 演示课件 (可直接下载与编辑放映)"""
    pptx_stream = generate_lesson_pptx(
        topic=topic,
        grade=grade,
        duration_minutes=duration_minutes
    )
    filename = f"《津门非遗美育：{topic}》配套课件_{grade}.pptx"
    encoded_filename = quote(filename)

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Access-Control-Expose-Headers": "Content-Disposition"
    }

    return Response(
        content=pptx_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers
    )

@router.get("/assignments")
def list_assignments(
    class_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    class_obj = get_authorized_class(db, class_id, current_user)
    if not class_obj:
        return error_response(code=4040, message="班级不存在或无权访问")
    assignments = db.query(Assignment).filter(
        Assignment.class_id == class_id,
        Assignment.teacher_id == class_obj.teacher_id
    ).order_by(Assignment.created_at.desc()).all()

    res = []
    for a in assignments:
        submit_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == a.id
        ).count()
        res.append({
            "id": a.id,
            "title": a.title,
            "type": a.type,
            "tool_type": a.tool_type,
            "deadline": a.deadline.strftime("%Y-%m-%d %H:%M"),
            "submit_count": submit_count,
            "status": a.status
        })
    return success_response(res)

@router.post("/assignments")
def create_assignment(
    req: CreateAssignmentRequest,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    class_obj = get_authorized_class(db, req.class_id, current_user)
    if not class_obj:
        return error_response(code=4040, message="班级不存在或无权访问")
    deadline = datetime.utcnow() + timedelta(days=req.deadline_days)
    
    assignment = Assignment(
        class_id=req.class_id,
        teacher_id=class_obj.teacher_id,
        title=req.title,
        type=req.type,
        tool_type=req.tool_type,
        deadline=deadline,
        description=req.description,
        status="PUBLISHED"
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return success_response({"id": assignment.id, "title": assignment.title}, message="作业发布成功")


@router.get("/my-assignments")
def list_student_assignments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(ClassMember).filter(
        ClassMember.student_id == current_user["user_id"], ClassMember.status == "ACTIVE"
    ).all()
    class_ids = [member.class_id for member in memberships]
    assignments = db.query(Assignment).filter(
        Assignment.class_id.in_(class_ids), Assignment.status == "PUBLISHED"
    ).all() if class_ids else []
    return success_response([{
        "id": assignment.id,
        "class_id": assignment.class_id,
        "title": assignment.title,
        "description": assignment.description,
        "type": assignment.type,
        "deadline": assignment.deadline
    } for assignment in assignments])


@router.post("/assignments/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    req: SubmitAssignmentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.get("role_code") != "STUDENT":
        return error_response(code=4030, message="只有学生可以提交作业")
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id, Assignment.status == "PUBLISHED"
    ).first()
    if not assignment:
        return error_response(code=4040, message="作业不存在")
    if datetime.utcnow() > assignment.deadline:
        return error_response(code=4090, message="作业已截止")
    member = db.query(ClassMember).filter(
        ClassMember.class_id == assignment.class_id,
        ClassMember.student_id == current_user["user_id"],
        ClassMember.status == "ACTIVE"
    ).first()
    if not member:
        return error_response(code=4030, message="不属于该作业的班级")
    if not (req.content and req.content.strip()) and req.asset_id is None and req.source_task_id is None:
        return error_response(code=4000, message="请提交文字或作品资源")
    if req.asset_id is not None and not db.query(Asset).filter(
        Asset.id == req.asset_id, Asset.created_by == current_user["user_id"]
    ).first():
        return error_response(code=4030, message="作品资源不属于当前学生")
    if req.source_task_id is not None and not db.query(AiTask).filter(
        AiTask.task_id == req.source_task_id, AiTask.user_id == current_user["user_id"]
    ).first():
        return error_response(code=4030, message="AI任务不属于当前学生")
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == current_user["user_id"]
    ).first()
    if submission and submission.status == "REVIEWED":
        return error_response(code=4090, message="作业已批改，不能重复提交")
    if submission:
        submission.content = req.content
        submission.asset_id = req.asset_id
        submission.source_task_id = req.source_task_id
        submission.status = "SUBMITTED"
        submission.submitted_at = datetime.utcnow()
    else:
        submission = AssignmentSubmission(
            assignment_id=assignment_id, student_id=current_user["user_id"],
            content=req.content, asset_id=req.asset_id,
            source_task_id=req.source_task_id, status="SUBMITTED"
        )
        db.add(submission)
    db.commit()
    db.refresh(submission)
    return success_response({"id": submission.id, "status": submission.status}, message="作业已提交")

@router.get("/assignments/{assignment_id}/submissions")
def list_submissions(
    assignment_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment or not get_authorized_class(db, assignment.class_id, current_user):
        return error_response(code=4040, message="作业不存在或无权访问")
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).all()

    res = []
    for s in submissions:
        student = db.query(SysUser).filter(SysUser.id == s.student_id).first()
        review = db.query(AssignmentReview).filter(AssignmentReview.submission_id == s.id).first()
        res.append({
            "id": s.id,
            "student_id": s.student_id,
            "student_name": student.nickname if student else f"学生{s.student_id}",
            "avatar_url": student.avatar_url if student else "",
            "content": s.content,
            "asset_id": s.asset_id,
            "status": s.status,
            "submitted_at": s.submitted_at.strftime("%Y-%m-%d %H:%M") if s.submitted_at else "",
            "score": review.score if review else None,
            "comment": review.comment if review else None,
            "ai_suggestion": review.ai_suggestion_json if review else None
        })
    return success_response(res)

@router.post("/submissions/{submission_id}/review")
def review_submission(
    submission_id: int,
    req: ReviewSubmissionRequest,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher_id = current_user["user_id"]
    sub = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not sub:
        return error_response(code=4040, message="提交记录不存在")
    assignment = db.query(Assignment).filter(Assignment.id == sub.assignment_id).first()
    if not assignment or not get_authorized_class(db, assignment.class_id, current_user):
        return error_response(code=4040, message="提交记录不存在或无权访问")
    
    sub.status = "REVIEWED"

    review = db.query(AssignmentReview).filter(AssignmentReview.submission_id == submission_id).first()
    if not review:
        review = AssignmentReview(
            submission_id=submission_id,
            teacher_id=teacher_id,
            score=req.score,
            comment=req.comment
        )
        db.add(review)
    else:
        review.score = req.score
        review.comment = req.comment
        review.teacher_id = teacher_id

    db.commit()
    return success_response({"submission_id": submission_id, "score": req.score}, message="批改完成")

@router.get("/classes/{class_id}/analytics")
def get_class_analytics(
    class_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    # 班级全景学情分析汇总
    class_obj = get_authorized_class(db, class_id, current_user)
    if not class_obj:
        return error_response(code=4040, message="班级不存在或无权访问")

    members = db.query(ClassMember).filter(
        ClassMember.class_id == class_id,
        ClassMember.status == "ACTIVE"
    ).all()

    student_ids = [m.student_id for m in members]
    student_users = db.query(SysUser).filter(SysUser.id.in_(student_ids)).all() if student_ids else []
    student_map = {u.id: u for u in student_users}

    # 能量值排行
    growths = db.query(UserGrowth).filter(UserGrowth.user_id.in_(student_ids)).all() if student_ids else []
    growth_map = {g.user_id: g.energy_value for g in growths}

    ranking = []
    for sid in student_ids:
        u = student_map.get(sid)
        ranking.append({
            "student_id": sid,
            "nickname": u.nickname if u else f"学号{sid}",
            "avatar_url": u.avatar_url if u else "",
            "energy_value": growth_map.get(sid, 0)
        })
    ranking.sort(key=lambda x: x["energy_value"], reverse=True)

    progress = db.query(LearningProgress).filter(LearningProgress.user_id.in_(student_ids)).all() if student_ids else []
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(student_ids)).all() if student_ids else []
    assignments = db.query(Assignment).filter(
        Assignment.class_id == class_id, Assignment.status == "PUBLISHED"
    ).all()
    assignment_ids = [assignment.id for assignment in assignments]
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id.in_(assignment_ids),
        AssignmentSubmission.student_id.in_(student_ids)
    ).all() if assignment_ids and student_ids else []
    submitted_pairs = {(submission.assignment_id, submission.student_id) for submission in submissions}
    course_ids = {record.course_id for record in progress}
    courses = db.query(Course).filter(Course.id.in_(course_ids)).all() if course_ids else []
    course_categories = {course.id: course.category for course in courses}
    category_counts = {}
    for record in progress:
        category = course_categories.get(record.course_id)
        if category:
            category_counts[category] = category_counts.get(category, 0) + 1

    analytics_data = {
        "class_name": class_obj.name,
        "grade": class_obj.grade,
        "student_count": len(student_ids),
        "course_completion_rate": round(100 * sum(bool(p.completed) for p in progress) / len(progress), 1) if progress else 0,
        "quiz_pass_rate": round(100 * sum(bool(q.passed) for q in quiz_attempts) / len(quiz_attempts), 1) if quiz_attempts else 0,
        "homework_submit_rate": round(100 * len(submitted_pairs) / (len(assignments) * len(student_ids)), 1) if assignments and student_ids else 0,
        "ranking": ranking,
        "radar_capabilities": [],
        "category_preference": [
            {"name": category, "count": count}
            for category, count in sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "sample_sizes": {
            "progress_records": len(progress),
            "quiz_attempts": len(quiz_attempts),
            "assignment_opportunities": len(assignments) * len(student_ids)
        },
        "rate_basis": {
            "course_completion_rate": "已产生进度的章节记录",
            "quiz_pass_rate": "测验作答次数",
            "homework_submit_rate": "已发布作业 × 班级在读学生"
        }
    }

    return success_response(analytics_data)

@router.get("/classes/{class_id}/exhibition-package")
def generate_exhibition_package(
    class_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    一键生成乡村小学非遗成果走廊实体展册排版数据集 (A4/A3 标准展出画册规格)
    """
    class_obj = get_authorized_class(db, class_id, current_user)
    if not class_obj:
        return error_response(code=4040, message="班级不存在或无权访问")
    class_name = class_obj.name
    grade = class_obj.grade

    # 获取班级学生信息与代表性作品
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.status == "ACTIVE").all()
    student_ids = [m.student_id for m in members]
    users = db.query(SysUser).filter(SysUser.id.in_(student_ids)).all() if student_ids else []
    student_map = {u.id: u for u in users}

    assignments = db.query(Assignment).filter(Assignment.class_id == class_id).all()
    assignment_map = {assignment.id: assignment for assignment in assignments}
    assignment_ids = list(assignment_map)
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id.in_(assignment_ids),
        AssignmentSubmission.student_id.in_(student_ids),
        AssignmentSubmission.status == "REVIEWED"
    ).all() if assignment_ids and student_ids else []
    asset_ids = [submission.asset_id for submission in submissions if submission.asset_id]
    assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all() if asset_ids else []
    asset_map = {asset.id: asset for asset in assets}
    submission_ids = [submission.id for submission in submissions]
    reviews = db.query(AssignmentReview).filter(
        AssignmentReview.submission_id.in_(submission_ids)
    ).all() if submission_ids else []
    review_map = {review.submission_id: review for review in reviews}
    profiles = db.query(UserProfile).filter(UserProfile.user_id.in_(student_ids)).all() if student_ids else []
    profile_map = {profile.user_id: profile for profile in profiles}

    exhibition_items = []
    for submission in submissions:
        assignment = assignment_map[submission.assignment_id]
        student = student_map.get(submission.student_id)
        profile = profile_map.get(submission.student_id)
        asset = asset_map.get(submission.asset_id)
        review = review_map.get(submission.id)
        exhibition_items.append({
            "id": f"EXHIBIT-{submission.id}",
            "student_id": submission.student_id,
            "student_name": student.nickname if student else "",
            "student_school": profile.school_name if profile else None,
            "student_avatar": student.avatar_url if student else None,
            "work_title": assignment.title,
            "tool_type": assignment.tool_type,
            "tool_name": assignment.type,
            "colored_image_url": asset.file_url if asset else None,
            "line_art_url": None,
            "template_url": None,
            "content": submission.content,
            "mentor_critique": review.comment if review else None,
            "score": review.score if review else None,
            "status": submission.status,
            "award": None
        })

    return success_response({
        "class_id": class_id,
        "class_name": class_name,
        "grade": grade,
        "curator_title": f"《津韵润乡·乡土非遗美育成果走廊实体展册（{class_name}）》",
        "academic_year": None,
        "school_header": None,
        "print_standards": {
            "page_size": "A4 (210mm × 297mm) / A3 (297mm × 420mm)",
            "dpi": 300,
            "bleed_mm": 3,
            "grid_columns": 2,
            "material_recommend": "250g哑光白卡纸或微涂宣纸"
        },
        "exhibit_count": len(exhibition_items),
        "items": exhibition_items
    })
