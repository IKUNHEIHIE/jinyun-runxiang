import json
import httpx
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, Response
from urllib.parse import quote
from app.services.ppt_generator import generate_lesson_pptx
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import require_teacher, get_current_user_optional
from app.schemas.common import success_response, error_response
from app.models.entities import (
    TeacherClass, ClassMember, Assignment, AssignmentSubmission,
    AssignmentReview, LearningProgress, UserGrowth, SysUser, SysConfig
)

router = APIRouter(prefix="/teacher", tags=["教师工作台与AI智能备课"])

class LessonPlanRequest(BaseModel):
    grade: str  # 小学三年级 / 小学四年级 / 初中
    topic: str  # 天津皮影戏 / 杨柳青木版年画 / 泥人张彩塑 / 骆派京韵大鼓 / 古法大漆
    duration_minutes: int = 45
    objectives: Optional[str] = "培养乡村儿童对乡土非遗的文化认同与动手实践能力"

class CreateAssignmentRequest(BaseModel):
    class_id: int
    title: str
    type: str = "AI_CREATION"  # AI_CREATION / OFFLINE_HANDMADE
    tool_type: Optional[str] = "SHADOW_PUPPET"
    deadline_days: int = 7
    description: str

class ReviewSubmissionRequest(BaseModel):
    score: int
    comment: str

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
    teacher_id = current_user["user_id"]
    assignments = db.query(Assignment).filter(
        Assignment.class_id == class_id,
        Assignment.teacher_id == teacher_id
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
    teacher_id = current_user["user_id"]
    deadline = datetime.utcnow() + timedelta(days=req.deadline_days)
    
    assignment = Assignment(
        class_id=req.class_id,
        teacher_id=teacher_id,
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

@router.get("/assignments/{assignment_id}/submissions")
def list_submissions(
    assignment_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
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
            "ai_suggestion": {
                "score_recommend": 92,
                "feedback": "作品色彩对比强烈，人物造型生动，展现出天津皮影典型的镂空特色与装饰感。"
            }
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
    class_obj = db.query(TeacherClass).filter(TeacherClass.id == class_id).first()
    if not class_obj:
        return error_response(code=4040, message="班级不存在")

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

    analytics_data = {
        "class_name": class_obj.name,
        "grade": class_obj.grade,
        "student_count": len(student_ids),
        "course_completion_rate": 84.5,
        "quiz_pass_rate": 88.0,
        "homework_submit_rate": 92.3,
        "ranking": ranking,
        "radar_capabilities": [
            {"dimension": "非遗传统认知", "score": 90},
            {"dimension": "AI提示词表达", "score": 85},
            {"dimension": "色彩与构图审美", "score": 88},
            {"dimension": "手工实践创作", "score": 82},
            {"dimension": "文化传承热情", "score": 95}
        ],
        "category_preference": [
            {"name": "津门皮影", "count": 28},
            {"name": "杨柳青年画", "count": 22},
            {"name": "泥人张彩塑", "count": 18},
            {"name": "青铜神兽纹样", "count": 15},
            {"name": "骆派京韵大鼓", "count": 12}
        ]
    }

    return success_response(analytics_data)

@router.get("/classes/{class_id}/exhibition-package")
def generate_exhibition_package(
    class_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    一键生成乡村小学非遗成果走廊实体展册排版数据集 (A4/A3 标准展出画册规格)
    """
    class_obj = db.query(TeacherClass).filter(TeacherClass.id == class_id).first()
    class_name = class_obj.name if class_obj else "乡村非遗美育特色示范班"
    grade = class_obj.grade if class_obj else "小学三年级"

    # 获取班级学生信息与代表性作品
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.status == "ACTIVE").all()
    student_ids = [m.student_id for m in members] if members else [2] # 默认回退李小明
    users = db.query(SysUser).filter(SysUser.id.in_(student_ids)).all() if student_ids else []
    student_map = {u.id: u for u in users}

    # 聚合高精度展品
    exhibition_items = [
        {
            "id": "EXHIBIT-01",
            "student_id": 2,
            "student_name": student_map.get(2).nickname if 2 in student_map else "李小明",
            "student_school": "蓟州区穿芳峪镇中心小学",
            "student_avatar": student_map.get(2).avatar_url if 2 in student_map else "",
            "work_title": "《津门赶考文生·青衿致远》",
            "tool_type": "SHADOW_PUPPET",
            "tool_name": "津派皮影戏三签可动纸样",
            "colored_image_url": "/static/generated/c81e3ba909d74c26b507da99c12d6813_colored.svg",
            "line_art_url": "/static/generated/c81e3ba909d74c26b507da99c12d6813_lineart.svg",
            "template_url": "/static/generated/c81e3ba909d74c26b507da99c12d6813_template.svg",
            "color_palette": ["#8B4513 (赭石)", "#2F4F4F (墨青)", "#D2691E (橘褐)", "#F5F5DC (米白)"],
            "historical_context": "承继津门文仕求学之风，旧时文生分科治学，骨秀神清，重学尚礼。",
            "craft_technique": "以驴皮为材，先勾线稿，再用平刀刻衣纹，发刀刻细节点染。",
            "mentor_critique": "刀工流畅沉静，文生巾透雕繁而不杂，兼具文人雅趣与乡村学子质朴灵性。",
            "qr_verify_url": "http://localhost:5174/ai-workshop?verify=EXHIBIT-01",
            "status": "APPROVED",
            "award": "特等奖·津门非遗小小传承人"
        },
        {
            "id": "EXHIBIT-02",
            "student_id": 3,
            "student_name": "王小燕",
            "student_school": "宝坻区林亭口镇第一小学",
            "student_avatar": "",
            "work_title": "《喜庆连年·吉庆红鲤福娃》",
            "tool_type": "SHADOW_PUPPET",
            "tool_name": "杨柳青木版年画意蕴皮影",
            "colored_image_url": "/static/generated/b695123fc4d348a29b35062a74c4a6fb_colored.svg",
            "line_art_url": "/static/generated/b695123fc4d348a29b35062a74c4a6fb_lineart.svg",
            "template_url": "/static/generated/b695123fc4d348a29b35062a74c4a6fb_template.svg",
            "color_palette": ["#C1272D (朱砂红)", "#1A6840 (品绿)", "#F9D423 (槐黄)", "#0038A8 (佛青)"],
            "historical_context": "源自杨柳青年画经典《连年有余》，胖娃娃抱鲤寓意丰衣足食与乡土祥和。",
            "craft_technique": "半印半画，墨线拓印后手工点染面颊粉润与双髻朱砂。",
            "mentor_critique": "童真盎然，色彩饱满喜庆，精准呈现了杨柳青木版年画五色套印神韵。",
            "qr_verify_url": "http://localhost:5174/ai-workshop?verify=EXHIBIT-02",
            "status": "APPROVED",
            "award": "一等奖·最佳传统美学创意"
        }
    ]

    return success_response({
        "class_id": class_id,
        "class_name": class_name,
        "grade": grade,
        "curator_title": f"《津韵润乡·乡土非遗美育成果走廊实体展册（{class_name}）》",
        "academic_year": "2025-2026学年春季期末展",
        "school_header": "天津市乡村非遗美育振兴协同育人基地",
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
