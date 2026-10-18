from html import escape
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, Response
from urllib.parse import quote
from app.services.ppt_generator import generate_lesson_pptx
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import require_teacher
from app.core.lesson_plans import generate_lesson
from app.schemas.common import success_response, error_response
from app.models.entities import (
    TeacherClass, ClassMember, Assignment, AssignmentSubmission,
    AssignmentReview, LearningProgress, UserGrowth, SysUser, QuizAttempt, CommunityPost,
    Contest,
)

router = APIRouter(prefix="/teacher", tags=["教师工作台与AI智能备课"])

def owned_class(db: Session, class_id: int, user: dict):
    query = db.query(TeacherClass).filter(TeacherClass.id == class_id)
    if user["role_code"] != "ADMIN":
        query = query.filter(TeacherClass.teacher_id == user["user_id"])
    result = query.first()
    if not result:
        raise HTTPException(404, "班级不存在或无权访问")
    return result


def owned_assignment(db: Session, assignment_id: int, user: dict):
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(404, "作业不存在")
    owned_class(db, assignment.class_id, user)
    return assignment


class LessonPlanRequest(BaseModel):
    grade: str = Field(min_length=1, max_length=64)
    topic: str = Field(min_length=1, max_length=128)
    duration_minutes: int = Field(45, ge=10, le=240)
    objectives: Optional[str] = Field(None, max_length=2000)

    @field_validator("grade", "topic", "objectives", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

class CreateAssignmentRequest(BaseModel):
    class_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=128)
    type: Literal["AI_CREATION", "OFFLINE_HANDMADE", "CONTEST"] = "AI_CREATION"
    tool_type: Optional[Literal["SHADOW_PUPPET", "BRONZE_PATTERN", "LACQUER"]] = "SHADOW_PUPPET"
    deadline_days: int = Field(7, ge=1, le=365)
    description: str = Field(min_length=1, max_length=10000)

class ReviewSubmissionRequest(BaseModel):
    score: int = Field(..., ge=0, le=100)
    comment: str = Field(max_length=5000)

@router.get("/classes")
def list_teacher_classes(
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher_id = current_user["user_id"]
    query = db.query(TeacherClass).filter(TeacherClass.status == "ACTIVE")
    if current_user["role_code"] != "ADMIN":
        query = query.filter(TeacherClass.teacher_id == teacher_id)
    classes = query.all()

    return success_response([{
        "id": c.id,
        "name": c.name,
        "grade": c.grade,
        "invite_code": c.invite_code,
        "student_count": db.query(ClassMember.student_id).join(SysUser, SysUser.id == ClassMember.student_id).filter(
            ClassMember.class_id == c.id, ClassMember.status == "ACTIVE",
            SysUser.status == "ACTIVE", SysUser.role_code == "STUDENT").distinct().count()
    } for c in classes])

@router.post("/lesson-plans/generate")
def generate_lesson_plan(
    req: LessonPlanRequest,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    return success_response(generate_lesson(req, db), message="备课方案已生成")

@router.get("/lesson-plans/export-html", response_class=HTMLResponse)
def export_lesson_plan_html(
    topic: str = Query("杨柳青木版年画", description="非遗主题"),
    grade: str = Query("小学三年级", description="适用学段"),
    duration_minutes: int = Query(45, ge=10, le=240, description="课时时长"),
    current_user: dict = Depends(require_teacher)
):
    """导出排版工整的标准非遗美育教案 (支持直接打印与另存为 PDF)"""
    date_str = datetime.utcnow().strftime("%Y年%m月%d日")
    topic, grade = escape(topic), escape(grade)
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
    <div class="print-btn">请使用浏览器打印 / 另存为 PDF</div>
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
    return HTMLResponse(content=html_content, headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'none'", "X-Content-Type-Options": "nosniff"})

@router.get("/lesson-plans/export-pptx")
def export_lesson_plan_pptx(
    topic: str = Query("杨柳青木版年画", description="非遗主题"),
    grade: str = Query("小学三年级", description="适用学段"),
    duration_minutes: int = Query(45, ge=10, le=240, description="课时时长"),
    current_user: dict = Depends(require_teacher)
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
    owned_class(db, class_id, current_user)
    teacher_id = current_user["user_id"]
    query = db.query(Assignment).filter(Assignment.class_id == class_id)
    if current_user["role_code"] != "ADMIN":
        query = query.filter(Assignment.teacher_id == teacher_id)
    assignments = query.order_by(Assignment.created_at.desc()).all()

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
    class_obj = owned_class(db, req.class_id, current_user)
    teacher_id = class_obj.teacher_id
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
    owned_assignment(db, assignment_id, current_user)
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
            "ai_suggestion": None
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
    
    owned_assignment(db, sub.assignment_id, current_user)
    assignment = db.get(Assignment, sub.assignment_id)
    if assignment and assignment.contest_id:
        contest = db.get(Contest, assignment.contest_id)
        if contest and contest.status == "PUBLISHED":
            raise HTTPException(409, "对抗赛成绩已公布，不能再修改")
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
    class_obj = owned_class(db, class_id, current_user)
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

    progresses = db.query(LearningProgress).filter(LearningProgress.user_id.in_(student_ids)).all() if student_ids else []
    quizzes = db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(student_ids)).all() if student_ids else []
    assignment_ids = [a.id for a in db.query(Assignment).filter(Assignment.class_id == class_id).all()]
    submissions = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id.in_(assignment_ids)).count() if assignment_ids else 0
    analytics_data = {
        "class_name": class_obj.name, "grade": class_obj.grade, "student_count": len(student_ids),
        "course_completion_rate": round(100 * sum(bool(p.completed) for p in progresses) / len(progresses), 1) if progresses else None,
        "quiz_pass_rate": round(100 * sum(bool(q.passed) for q in quizzes) / len(quizzes), 1) if quizzes else None,
        "homework_submit_rate": round(100 * submissions / (len(assignment_ids) * len(student_ids)), 1) if assignment_ids and student_ids else None,
        "ranking": ranking, "radar_capabilities": [], "category_preference": [],
        "data_source": "database"
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
    class_obj = owned_class(db, class_id, current_user)
    class_name = class_obj.name if class_obj else "乡村非遗美育特色示范班"
    grade = class_obj.grade if class_obj else "小学三年级"

    # 获取班级学生信息与代表性作品
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.status == "ACTIVE").all()
    student_ids = [m.student_id for m in members]
    users = db.query(SysUser).filter(SysUser.id.in_(student_ids)).all() if student_ids else []
    student_map = {u.id: u for u in users}

    posts = db.query(CommunityPost).filter(CommunityPost.user_id.in_(student_ids),
                                           CommunityPost.status == "APPROVED").all() if student_ids else []
    exhibition_items = [{"id": str(post.id), "student_id": post.user_id,
        "student_name": student_map[post.user_id].nickname if post.user_id in student_map else "学员",
        "student_school": class_obj.school_id or "", "student_avatar": student_map[post.user_id].avatar_url if post.user_id in student_map else "",
        "work_title": post.title, "tool_type": post.category, "tool_name": post.category,
        "colored_image_url": post.cover_url, "line_art_url": None, "template_url": None,
        "color_palette": [], "historical_context": "", "craft_technique": "",
        "mentor_critique": "", "qr_verify_url": f"/community?post={post.id}",
        "status": post.status, "award": ""} for post in posts]

    return success_response({
        "class_id": class_id,
        "class_name": class_name,
        "grade": grade,
        "curator_title": f"《津韵润乡·乡土非遗美育成果走廊实体展册（{class_name}）》",
        "academic_year": str(datetime.utcnow().year),
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
