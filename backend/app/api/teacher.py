from html import escape
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, Response
from urllib.parse import quote
from app.services.ppt_generator import generate_lesson_pptx
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import require_teacher
from app.core.lesson_plans import generate_lesson, local_lesson
from app.schemas.common import success_response, error_response
from app.models.entities import (
    TeacherClass, ClassMember, Assignment, AssignmentSubmission,
    AssignmentReview, LearningProgress, UserGrowth, SysUser, QuizAttempt, CommunityPost,
    Contest, Course, CourseChapter, UserProfile,
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

def class_completion_rates(db: Session, class_ids):
    """按班级统计真实学完率: 学生已完成章节 / 该生已开始课程的已发布章节, 再取学生均值。"""
    if not class_ids:
        return {}
    students_by_class = {}
    rows = db.query(ClassMember.class_id, ClassMember.student_id).join(
        SysUser, SysUser.id == ClassMember.student_id).filter(
        ClassMember.class_id.in_(class_ids), ClassMember.status == "ACTIVE",
        SysUser.status == "ACTIVE", SysUser.role_code == "STUDENT").distinct().all()
    for class_id, student_id in rows:
        students_by_class.setdefault(class_id, set()).add(student_id)

    published = set(db.query(CourseChapter.course_id, CourseChapter.id).join(
        Course, Course.id == CourseChapter.course_id).filter(Course.status == "PUBLISHED").all())
    student_ids = set().union(*students_by_class.values()) if students_by_class else set()
    progress_by_student = {}
    if student_ids:
        for record in db.query(LearningProgress).filter(LearningProgress.user_id.in_(student_ids)).all():
            if (record.course_id, record.chapter_id) in published:
                progress_by_student.setdefault(record.user_id, []).append(record)

    result = {}
    for class_id, members in students_by_class.items():
        rates = []
        for student_id in members:
            progress = progress_by_student.get(student_id, [])
            courses = {record.course_id for record in progress}
            available = sum(course_id in courses for course_id, _ in published)
            if not available:
                continue
            completed = {(record.course_id, record.chapter_id) for record in progress if record.completed}
            rates.append(100 * len(completed) / available)
        result[class_id] = round(sum(rates) / len(rates), 1) if rates else None
    return result


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
    class_ids = [c.id for c in classes]
    teacher_ids = {c.teacher_id for c in classes}
    student_counts = dict(db.query(ClassMember.class_id, func.count(func.distinct(ClassMember.student_id))).join(
        SysUser, SysUser.id == ClassMember.student_id).filter(
        ClassMember.class_id.in_(class_ids), ClassMember.status == "ACTIVE",
        SysUser.status == "ACTIVE", SysUser.role_code == "STUDENT").group_by(ClassMember.class_id).all()) if class_ids else {}
    teachers = {u.id: u for u in db.query(SysUser).filter(SysUser.id.in_(teacher_ids)).all()} if teacher_ids else {}
    profiles = {p.user_id: p for p in db.query(UserProfile).filter(UserProfile.user_id.in_(teacher_ids)).all()} if teacher_ids else {}
    completion_rates = class_completion_rates(db, class_ids)

    return success_response([{
        "id": c.id,
        "name": c.name,
        "grade": c.grade,
        "invite_code": c.invite_code,
        "student_count": student_counts.get(c.id, 0),
        "teacher_name": teachers[c.teacher_id].nickname if c.teacher_id in teachers else "",
        "school": profiles[c.teacher_id].school_name if c.teacher_id in profiles and profiles[c.teacher_id].school_name else "",
        "completion": completion_rates.get(c.id),
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
    plan = local_lesson(LessonPlanRequest(grade=grade, topic=topic, duration_minutes=duration_minutes))
    targets = plan["targets"]
    points = plan["key_difficult_points"]
    target_html = "".join(
        f"<li><strong>【{label}】</strong>：{escape(str(value))}</li>"
        for label, value in (("审美感知", targets["aesthetic"]), ("艺术表现", targets["skill"]),
                             ("文化理解", targets["emotion"]))
    )
    process_html = "".join(
        f'<tr><td class="step-name">{escape(str(step["step"]))}</td><td>{escape(str(step["content"]))}</td></tr>'
        for step in plan["teaching_process"]
    )
    question_html = "".join(f"<li>{escape(str(question))}</li>" for question in plan["interactive_questions"])
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>课堂教案 · {{TOPIC}}</title>
    <style>
        body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; color: #262626; line-height: 1.7;
               margin: 0; padding: 40px; background: #FAFAFA; }
        .paper { max-width: 820px; margin: 0 auto; background: #FFF; padding: 50px 60px;
                 box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #E8E8E8; }
        .notice { max-width: 820px; margin: 0 auto 16px; padding: 10px 14px; background: #FFF7E6;
                  border: 1px solid #FFD591; color: #874D00; font-size: 13px; }
        .header { text-align: center; border-bottom: 2px solid #8B4A2F; padding-bottom: 16px; margin-bottom: 24px; }
        .super-title { font-size: 13px; color: #8B4A2F; letter-spacing: 2px; font-weight: 700; }
        .main-title { font-size: 24px; font-weight: 900; color: #1F1F1F; margin: 8px 0; }
        .meta-line { font-size: 12px; color: #8C8C8C; }
        .meta-table, .process-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .meta-table th, .meta-table td, .process-table th, .process-table td {
            border: 1px solid #D9D9D9; padding: 8px 12px; font-size: 13px; vertical-align: top; }
        .meta-table th, .process-table th { background: #FAF3EC; color: #8B4A2F; text-align: left; }
        .meta-table th { width: 16%; }
        .step-name { width: 24%; font-weight: 700; color: #8B4A2F; }
        .section-title { font-size: 16px; font-weight: 800; color: #8B4A2F; border-left: 4px solid #8B4A2F;
                         padding-left: 10px; margin: 24px 0 12px; }
        ul, ol { margin: 0; padding-left: 24px; font-size: 13px; }
        li { margin: 6px 0; }
        .script { white-space: pre-wrap; font-size: 13px; line-height: 1.9; color: #434343;
                  background: #FCFAF7; border: 1px solid #F0E6DA; padding: 16px; }
        .footer-note { margin-top: 28px; padding-top: 12px; border-top: 1px dashed #D9D9D9;
                       font-size: 12px; color: #8C8C8C; }
        @media print { body { background: #FFF; padding: 0; } .paper { box-shadow: none; border: none; padding: 0; }
                       .notice { display: none; } }
    </style>
</head>
<body>
    <div class="notice">本文件由本地课程模板生成，请教师结合学段、材料和课堂实际审核后再使用。</div>
    <div class="paper">
        <div class="header">
            <div class="super-title">天津市“津韵润乡”乡村中小学非遗美育协同工程</div>
            <h1 class="main-title">{{TOPIC}} · 课堂教案</h1>
            <div class="meta-line">归档日期：{{DATE}}</div>
        </div>
        <table class="meta-table">
            <tr><th>适用学段</th><td>{{GRADE}}</td><th>课时时长</th><td>{{DURATION}} 分钟</td></tr>
            <tr><th>非遗主题</th><td>{{TOPIC}}</td><th>生成方式</th><td>本地课程模板（教师审核后使用）</td></tr>
        </table>

        <div class="section-title">一、教学目标</div>
        <ul>{{TARGETS}}</ul>

        <div class="section-title">二、教学重难点</div>
        <p><strong>重点：</strong>{{KEY}}</p>
        <p><strong>难点：</strong>{{DIFFICULT}}</p>

        <div class="section-title">三、教学过程</div>
        <table class="process-table">
            <thead><tr><th>环节</th><th>师生活动</th></tr></thead>
            <tbody>{{PROCESS}}</tbody>
        </table>

        <div class="section-title">四、互动问题</div>
        <ol>{{QUESTIONS}}</ol>

        <div class="section-title">五、课后作业</div>
        <p>{{HOMEWORK}}</p>

        <div class="section-title">六、课堂讲稿</div>
        <div class="script">{{SCRIPT}}</div>

        <div class="footer-note">
            本教案由本地课程模板生成，未调用外部模型；不包含未接入的 3D 模型、A4 纸样、实拍视频或自动评分。
            请教师结合学段、材料和课堂实际审核调整。
        </div>
    </div>
</body>
</html>"""
    for marker, value in {
        "TOPIC": escape(topic),
        "GRADE": escape(grade),
        "DURATION": str(duration_minutes),
        "DATE": escape(date_str),
        "TARGETS": target_html,
        "KEY": escape(str(points["key"])),
        "DIFFICULT": escape(str(points["difficult"])),
        "PROCESS": process_html,
        "QUESTIONS": question_html,
        "HOMEWORK": escape(str(plan["homework_proposal"])),
        "SCRIPT": escape(str(plan["teacher_script"])),
    }.items():
        html_content = html_content.replace("{{" + marker + "}}", value)
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
    ids = [a.id for a in assignments]
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id.in_(ids)).all() if ids else []
    reviewed_ids = {r.submission_id for r in db.query(AssignmentReview).filter(
        AssignmentReview.submission_id.in_([s.id for s in submissions])).all()} if submissions else set()
    counts = {}
    for s in submissions:
        c = counts.setdefault(s.assignment_id, {"submitted": 0, "review_pending": 0})
        c["submitted"] += 1
        if s.id not in reviewed_ids:
            c["review_pending"] += 1
    for a in assignments:
        c = counts.get(a.id, {"submitted": 0, "review_pending": 0})
        res.append({
            "id": a.id,
            "title": a.title,
            "type": a.type,
            "tool_type": a.tool_type,
            "deadline": a.deadline.strftime("%Y-%m-%d %H:%M"),
            "submit_count": c["submitted"],
            "review_pending": c["review_pending"],
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
    if req.type == "CONTEST":
        # 对抗赛必须成对生成两个班的作业并登记 ContestEntry，走 /teacher/contests；
        # 这里放行会造出没有对手班、永远无法评分的假对抗赛，还会虚增教师端「进行中对抗赛」计数。
        raise HTTPException(409, "班级对抗赛请在「对抗赛」页新建，单班作业不能标记为对抗赛")
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
