"""Teacher and student workflows shared by Android and the desktop workspace."""
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.schemas.common import success_response
from app.api.teacher import owned_class, LessonPlanRequest
from app.models.entities import TeacherClass, ClassMember, SysUser, LearningProgress, Course, CourseChapter, UserGrowth, Badge, UserBadge, Quiz, QuizAttempt, QuizQuestion, Assignment, AssignmentSubmission, AssignmentReview
from app.models.mobile import LessonPlanRecord, ClassNotice, ClassAttendance, ClassSession, ClassMessage, LearningDay

router = APIRouter(prefix="/mobile", tags=["手机与教师后台协同"])


def today():
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def class_access(db, class_id, user):
    if user["role_code"] in {"TEACHER", "ADMIN"}:
        return owned_class(db, class_id, user)
    record = db.get(TeacherClass, class_id)
    if not record or record.status != "ACTIVE" or not db.query(ClassMember).filter_by(
            class_id=class_id, student_id=user["user_id"], status="ACTIVE").first():
        raise HTTPException(404, "班级不存在或您未加入该班级")
    return record


def student_stats(db, classroom, local_day=None):
    members = db.query(ClassMember).filter_by(class_id=classroom.id, status="ACTIVE").all()
    published_chapters = set(db.query(CourseChapter.course_id, CourseChapter.id).join(
        Course, Course.id == CourseChapter.course_id).filter(Course.status == "PUBLISHED").all())
    quiz_totals = dict(db.query(QuizQuestion.quiz_id, func.sum(QuizQuestion.score)).group_by(QuizQuestion.quiz_id).all())
    local_day = local_day or datetime.now(ZoneInfo("Asia/Shanghai")).date()
    window_start = datetime.combine(local_day - timedelta(days=6), time.min, ZoneInfo("Asia/Shanghai")).astimezone(timezone.utc).replace(tzinfo=None)
    window_end = datetime.combine(local_day + timedelta(days=1), time.min, ZoneInfo("Asia/Shanghai")).astimezone(timezone.utc).replace(tzinfo=None)
    result = []
    seen = set()
    for member in members:
        if member.student_id in seen:
            continue
        student = db.get(SysUser, member.student_id)
        if not student or student.status != "ACTIVE" or student.role_code != "STUDENT":
            continue
        seen.add(member.student_id)
        progress = [p for p in db.query(LearningProgress).filter_by(user_id=student.id).all()
                    if (p.course_id, p.chapter_id) in published_chapters]
        courses = {p.course_id for p in progress}
        chapters = sum(course_id in courses for course_id, _ in published_chapters)
        completed = {(p.course_id, p.chapter_id) for p in progress if p.completed}
        quizzes = db.query(QuizAttempt).join(Quiz, Quiz.id == QuizAttempt.quiz_id).join(
            Course, Course.id == Quiz.course_id).filter(
                QuizAttempt.user_id == student.id, Course.status == "PUBLISHED",
                QuizAttempt.submitted_at < window_end).all()
        def accuracy(attempts):
            scored = [(q.score, quiz_totals.get(q.quiz_id, 0)) for q in attempts if quiz_totals.get(q.quiz_id, 0) > 0]
            possible = sum(total for _, total in scored)
            return round(100 * sum(max(0, min(score, total)) for score, total in scored) / possible, 1) if possible else None
        recent = [q for q in quizzes if q.submitted_at >= window_start]
        growth = db.get(UserGrowth, student.id)
        attendance = db.get(ClassAttendance, (classroom.id, student.id, local_day.isoformat()))
        result.append({"id": student.id, "nickname": student.nickname, "avatar_url": student.avatar_url,
                       "completion_rate": round(100 * len(completed) / chapters, 1) if chapters else None,
                       "quiz_pass_rate": round(100 * sum(q.passed for q in quizzes) / len(quizzes), 1) if quizzes else None,
                       "quiz_accuracy": accuracy(quizzes), "quiz_accuracy_7d": accuracy(recent),
                       "quiz_attempt_count_7d": len(recent),
                       "energy_value": growth.energy_value if growth else 0,
                       "badge_count": db.query(UserBadge.badge_id).join(Badge, Badge.id == UserBadge.badge_id).filter(
                           UserBadge.user_id == student.id).distinct().count(),
                       "attendance": attendance.status if attendance else "UNRECORDED"})
    return result


@router.get("/teacher/classes/{class_id}/students")
def students(class_id: int, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    classroom = owned_class(db, class_id, user)
    return success_response(student_stats(db, classroom))


@router.get("/teacher/classes/{class_id}/analytics")
def class_analytics(class_id: int, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    classroom = owned_class(db, class_id, user)
    if classroom.status != "ACTIVE":
        raise HTTPException(404, "班级已停用")
    local_day = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    rows = student_stats(db, classroom, local_day)
    ids = {s["id"] for s in rows}
    catalog = db.query(Badge).order_by(Badge.id).all()
    badges = {b.id: {"id": b.id, "code": b.code, "name": b.name, "description": b.description, "icon_url": b.icon_url}
              for b in catalog}
    awards = {(a.user_id, a.badge_id) for a in db.query(UserBadge).filter(UserBadge.user_id.in_(ids)).all()
              if a.badge_id in badges} if ids else set()
    days = {(d.user_id, d.day) for d in db.query(LearningDay).filter(LearningDay.user_id.in_(ids)).all()} if ids else set()
    for student in rows:
        student["badges"] = [badges[bid] for bid in badges if (student["id"], bid) in awards]
        student["badge_count"] = len(student["badges"])
        student["learning_days"] = sum(uid == student["id"] for uid, _ in days)
    for bid, badge in badges.items():
        badge["student_count"] = sum(award_bid == bid for _, award_bid in awards)
    known = [s["completion_rate"] for s in rows if s["completion_rate"] is not None]
    return success_response({
        "class": {"id": classroom.id, "name": classroom.name, "grade": classroom.grade, "invite_code": classroom.invite_code},
        "day": local_day.isoformat(), "quiz_window_start": (local_day - timedelta(days=6)).isoformat(),
        "quiz_window_end": local_day.isoformat(), "students": rows, "student_count": len(rows),
        "mean_completion_rate": round(sum(known) / len(known), 1) if known else None,
        "progress_student_count": len(known), "badge_total": len(awards), "badge_catalog_count": len(badges),
        "unlocked_badge_types": len({bid for _, bid in awards}), "learning_days_total": len(days),
        "badge_catalog": list(badges.values()),
        "progress_basis": "已开始的已发布课程，按有效章节完成数计算；未开始者不计入平均值",
        "quiz_basis": "近七个上海自然日，按当前题目分值加权计算；无有效试题时显示未知",
    })


@router.get("/teacher/overview")
def overview(user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    query = db.query(TeacherClass).filter_by(status="ACTIVE")
    if user["role_code"] != "ADMIN":
        query = query.filter_by(teacher_id=user["user_id"])
    classes = query.all()
    ids = [c.id for c in classes]
    members = db.query(ClassMember).join(SysUser, SysUser.id == ClassMember.student_id).filter(
        ClassMember.class_id.in_(ids), ClassMember.status == "ACTIVE",
        SysUser.status == "ACTIVE", SysUser.role_code == "STUDENT").all() if ids else []
    # Older databases may contain duplicate membership/submission rows. Count each
    # class/student and assignment/student pair once, including across owned classes.
    member_pairs = {(m.class_id, m.student_id) for m in members}
    student_ids = {student_id for _, student_id in member_pairs}
    assignments = db.query(Assignment).filter(
        Assignment.class_id.in_(ids), Assignment.status == "PUBLISHED").all() if ids else []
    assignment_classes = {a.id: a.class_id for a in assignments}
    submitted_pairs = {(s.assignment_id, s.student_id) for s in db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id.in_(assignment_classes),
        AssignmentSubmission.status.in_(["SUBMITTED", "REVIEWED"])).all()
        if (assignment_classes[s.assignment_id], s.student_id) in member_pairs} if assignments else set()
    expected_submissions = sum(sum(class_id == a.class_id for class_id, _ in member_pairs) for a in assignments)
    attendance = [a for a in db.query(ClassAttendance).filter(
        ClassAttendance.class_id.in_(ids), ClassAttendance.day == today()).all()
        if (a.class_id, a.student_id) in member_pairs] if ids else []
    sessions = db.query(ClassSession).filter(ClassSession.class_id.in_(ids)).all() if ids else []
    session_classes = {s.id: s.class_id for s in sessions}
    local_day = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    day_start = datetime.combine(local_day, time.min, ZoneInfo("Asia/Shanghai")).astimezone(timezone.utc).replace(tzinfo=None)
    messages_today = db.query(ClassMessage).filter(
        ClassMessage.session_id.in_(session_classes), ClassMessage.created_at >= day_start,
        ClassMessage.created_at < day_start + timedelta(days=1)).all() if sessions else []
    student_messages = [m for m in messages_today if (session_classes[m.session_id], m.user_id) in member_pairs]
    participants = {m.user_id for m in student_messages}
    hand_raisers = {m.user_id for m in student_messages if m.type == "HAND"}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    pending_assignments = [a for a in assignments if a.deadline >= now and
        any((a.id, student_id) not in submitted_pairs for class_id, student_id in member_pairs if class_id == a.class_id)]
    next_deadline = min((a.deadline for a in pending_assignments), default=None)
    lesson_plans = db.query(LessonPlanRecord).filter_by(teacher_id=user["user_id"])
    plan_count = lesson_plans.count()
    reviewed = db.query(AssignmentReview).join(
        AssignmentSubmission, AssignmentSubmission.id == AssignmentReview.submission_id).filter(
        AssignmentReview.teacher_id == user["user_id"],
        AssignmentSubmission.assignment_id.in_(assignment_classes)).count() if assignments else 0
    # 待批改 = 本班学生已提交、且还没有任何批改记录的作业（assignment_review.submission_id 唯一）。
    member_submissions = [s for s in (db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id.in_(assignment_classes)).all() if assignments else [])
        if (assignment_classes[s.assignment_id], s.student_id) in member_pairs]
    reviewed_submission_ids = {r.submission_id for r in db.query(AssignmentReview).filter(
        AssignmentReview.submission_id.in_([s.id for s in member_submissions])).all()} if member_submissions else set()
    review_pending = sum(1 for s in member_submissions if s.id not in reviewed_submission_ids)
    from app.core.course_badges import course_badge_progress
    completed_courses = sum(p["completed_courses"] for p in course_badge_progress(db, user["user_id"]).values())
    # The design names four achievements but supplies no thresholds. These are
    # explicitly described current milestones, not historical awarded badges.
    achievements = [
        {"code":"LESSON_PLAN", "name":"匠心独运", "description":"保存至少一份备课教案",
         "current":plan_count, "target":1, "path":"/teacher/lesson-plan"},
        {"code":"ACTIVE_STUDENT", "name":"桃李芬芳", "description":"负责的班级中有至少一名在读学生",
         "current":len(student_ids), "target":1, "path":"/teacher/analytics"},
        {"code":"REVIEW", "name":"春风化雨", "description":"完成至少一份已发布作业的批改",
         "current":reviewed, "target":1, "path":"/teacher/assignments"},
        {"code":"COURSE", "name":"博学笃行", "description":"完成一门已发布非遗专题课程的全部章节",
         "current":completed_courses, "target":1, "path":"/courses"},
    ]
    for achievement in achievements:
        achievement["completed"] = achievement["current"] >= achievement["target"]
    return success_response({
        "class_count":len(classes), "student_count":len(student_ids), "assignment_count":len(assignments),
        "submission_count":len(submitted_pairs), "submission_expected":expected_submissions,
        "submission_pending":expected_submissions - len(submitted_pairs),
        "review_pending":review_pending, "submission_submitted":len(member_submissions),
        "submission_rate":round(100 * len(submitted_pairs) / expected_submissions, 1) if expected_submissions else None,
        "next_assignment_deadline":next_deadline.replace(tzinfo=timezone.utc).isoformat() if next_deadline else None,
        "active_contest_count":sum(a.type == "CONTEST" for a in pending_assignments),
        "attendance_expected":len(member_pairs), "attendance_recorded":len(attendance),
        "attendance_present":sum(a.status == "PRESENT" for a in attendance),
        "attendance_leave":sum(a.status == "LEAVE" for a in attendance),
        "attendance_absent":sum(a.status == "ABSENT" for a in attendance),
        "attendance_unrecorded":len(member_pairs) - len(attendance),
        "attendance_rate":round(100 * sum(a.status == "PRESENT" for a in attendance) / len(member_pairs), 1)
            if member_pairs and attendance else None,
        "badge_count":db.query(UserBadge).filter(UserBadge.user_id.in_(student_ids)).count() if student_ids else 0,
        "session_count":len(sessions), "interaction_count":len(messages_today), "hand_raiser_count":len(hand_raisers),
        "activity_participant_count":len(participants),
        "activity_score":round(100 * len(participants) / len(student_ids)) if student_ids and sessions else None,
        "active_session_count":sum(s.status == "LIVE" for s in sessions), "lesson_plan_count":plan_count,
        "lesson_plan_today_count":lesson_plans.filter(LessonPlanRecord.created_at >= day_start,
            LessonPlanRecord.created_at < day_start + timedelta(days=1)).count(),
        "achievements":achievements, "day":local_day.isoformat(), "data_source":"database",
    })


class AttendanceItem(BaseModel):
    student_id: int = Field(gt=0)
    status: Literal["PRESENT", "LEAVE", "ABSENT"]


class AttendanceInput(BaseModel):
    records: list[AttendanceItem] = Field(min_length=1, max_length=500)
    day: date | None = None


@router.put("/teacher/classes/{class_id}/attendance")
def attendance(class_id: int, req: AttendanceInput, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    owned_class(db, class_id, user)
    target_day = today()
    if req.day and req.day.isoformat() != target_day:
        raise HTTPException(409, "考勤日期已变化，请刷新后重新记录今日考勤")
    members = {m.student_id for m in db.query(ClassMember).join(SysUser, SysUser.id == ClassMember.student_id).filter(
        ClassMember.class_id == class_id, ClassMember.status == "ACTIVE",
        SysUser.status == "ACTIVE", SysUser.role_code == "STUDENT").all()}
    if any(item.student_id not in members for item in req.records):
        raise HTTPException(422, "记录中包含不属于该班级的学生")
    for item in req.records:
        record = db.get(ClassAttendance, (class_id, item.student_id, target_day))
        if not record:
            record = ClassAttendance(class_id=class_id, student_id=item.student_id, day=target_day)
            db.add(record)
        record.status, record.recorded_by = item.status, user["user_id"]
    db.commit()
    return success_response({"day": target_day, "recorded": len(req.records)})


class NoticeInput(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=10000)


@router.post("/teacher/classes/{class_id}/notices")
def publish_notice(class_id: int, req: NoticeInput, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    owned_class(db, class_id, user)
    record = ClassNotice(class_id=class_id, teacher_id=user["user_id"], **req.model_dump())
    db.add(record); db.commit()
    return success_response({"id": record.id, "title": record.title})


@router.get("/classes/{class_id}/notices")
def notices(class_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    class_access(db, class_id, user)
    return success_response([{"id": n.id, "title": n.title, "content": n.content, "created_at": n.created_at.isoformat()}
                             for n in db.query(ClassNotice).filter_by(class_id=class_id).order_by(ClassNotice.created_at.desc()).all()])


@router.get("/me/classes")
def my_classes(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    classes = db.query(TeacherClass).join(ClassMember, ClassMember.class_id == TeacherClass.id).filter(
        ClassMember.student_id == user["user_id"], ClassMember.status == "ACTIVE", TeacherClass.status == "ACTIVE").all()
    return success_response([{"id": c.id, "name": c.name, "grade": c.grade} for c in classes])


class PlanInput(BaseModel):
    grade: str = Field(min_length=1, max_length=64)
    topic: str = Field(min_length=1, max_length=128)
    duration_minutes: int = Field(45, ge=10, le=240)
    mode: Literal["AUTO", "LOCAL"] = "AUTO"
    request_id: str | None = Field(None, min_length=8, max_length=64, pattern=r"^[a-z0-9_-]+$")

    @field_validator("grade", "topic", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


def plan_response(record):
    content = dict(record.content_json) if isinstance(record.content_json, dict) else {"teacher_script":str(record.content_json)}
    content.pop("ppt_download_url", None)
    # MySQL JSON key order is unrelated to the teaching sequence.
    for name, keys in [("targets", ("aesthetic", "skill", "emotion")), ("key_difficult_points", ("key", "difficult"))]:
        value = content.get(name)
        if isinstance(value, dict):
            content[name] = {key:value[key] for key in (*keys, *value) if key in value}
    content.update(title=record.title, grade=record.grade, topic=record.topic, duration=str(record.duration_minutes)+" 分钟")
    return {"id":record.id, "content":content, "source":record.source,
            "created_at":record.created_at.replace(tzinfo=timezone.utc).isoformat() if record.created_at else None,
            "pptx_url":"/api/mobile/teacher/lesson-plans/"+str(record.id)+"/pptx"}


@router.get("/teacher/lesson-plans/capabilities")
def plan_capabilities(user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    from app.core.lesson_plans import model_configuration
    return success_response({"model_enabled":bool(model_configuration(db)), "default_mode":"LOCAL",
                             "min_duration_minutes":10,"max_duration_minutes":240})


@router.get("/teacher/lesson-plans/history")
def plan_history(limit: int = Query(20, ge=1, le=50), before_id: int | None = Query(None, gt=0),
                 user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    query = db.query(LessonPlanRecord).filter_by(teacher_id=user["user_id"])
    total = query.count()
    if before_id:
        query = query.filter(LessonPlanRecord.id < before_id)
    rows = query.order_by(LessonPlanRecord.id.desc()).limit(limit+1).all()
    items = [{"id":r.id,"title":r.title,"grade":r.grade,"topic":r.topic,"source":r.source,
              "duration_minutes":r.duration_minutes,
              "created_at":r.created_at.replace(tzinfo=timezone.utc).isoformat() if r.created_at else None} for r in rows[:limit]]
    return success_response({"items":items,"total":total,"next_cursor":rows[limit-1].id if len(rows)>limit else None})


@router.post("/teacher/lesson-plans")
def create_plan(req: PlanInput, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    db.query(SysUser).filter_by(id=user["user_id"]).with_for_update().one()
    if req.request_id:
        previous = db.query(LessonPlanRecord).filter_by(teacher_id=user["user_id"],request_id=req.request_id).first()
        if previous:
            if (previous.grade,previous.topic,previous.duration_minutes,previous.request_mode) != (req.grade,req.topic,req.duration_minutes,req.mode):
                raise HTTPException(409,"该请求标识已用于其他备课配置")
            return success_response(plan_response(previous))
    from app.core.lesson_plans import generate_lesson
    plan = generate_lesson(LessonPlanRequest(grade=req.grade,topic=req.topic,duration_minutes=req.duration_minutes),db,req.mode)
    source = plan.get("generated_by") or "本地课程模板"
    record = LessonPlanRecord(teacher_id=user["user_id"], title=plan["title"], grade=req.grade, topic=req.topic,
                              duration_minutes=req.duration_minutes, content_json=plan, source=source,
                              request_id=req.request_id,request_mode=req.mode)
    db.add(record); db.commit()
    return success_response(plan_response(record))


def owned_plan(db, plan_id, user):
    record = db.get(LessonPlanRecord, plan_id)
    if not record or (record.teacher_id != user["user_id"] and user["role_code"] != "ADMIN"):
        raise HTTPException(404, "备课记录不存在")
    return record


@router.get("/teacher/lesson-plans")
def plans(user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    records = db.query(LessonPlanRecord).filter_by(teacher_id=user["user_id"]).order_by(LessonPlanRecord.created_at.desc()).all()
    return success_response([{"id": p.id, "title": p.title, "grade": p.grade, "topic": p.topic, "source": p.source,
                              "created_at": p.created_at.isoformat()} for p in records])


@router.get("/teacher/lesson-plans/{plan_id}")
def plan_detail(plan_id: int, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    record = owned_plan(db, plan_id, user)
    return success_response(plan_response(record))


@router.get("/teacher/lesson-plans/{plan_id}/pptx")
def export_plan(plan_id: int, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    from app.services.ppt_generator import generate_lesson_pptx
    record = owned_plan(db, plan_id, user)
    plan = plan_response(record)["content"]
    stream = generate_lesson_pptx(
        topic=record.topic, grade=record.grade, duration_minutes=record.duration_minutes,
        title=record.title, source=record.source,
        targets=plan.get("targets", {}), key_difficult=plan.get("key_difficult_points", {}),
        teaching_process=plan.get("teaching_process", []), teacher_script=plan.get("teacher_script", ""),
        interactive_questions=plan.get("interactive_questions", []), homework_proposal=plan.get("homework_proposal", ""))
    return Response(stream.getvalue(), media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(record.topic + ".pptx")})


class SessionInput(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    stream_url: HttpUrl | None = None


@router.post("/teacher/classes/{class_id}/sessions")
def start_session(class_id: int, req: SessionInput, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    owned_class(db, class_id, user)
    if req.stream_url and req.stream_url.scheme != "https":
        raise HTTPException(422, "课堂视频地址必须使用HTTPS")
    record = ClassSession(class_id=class_id, host_id=user["user_id"], title=req.title,
                          stream_url=str(req.stream_url) if req.stream_url else None)
    db.add(record); db.commit()
    return success_response({"id": record.id, "status": record.status})


@router.get("/classes/{class_id}/sessions")
def sessions(class_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    class_access(db, class_id, user)
    return success_response([{"id": r.id, "title": r.title, "status": r.status, "stream_url": r.stream_url}
                             for r in db.query(ClassSession).filter_by(class_id=class_id).order_by(ClassSession.created_at.desc()).all()])


def owned_session(db, session_id, user):
    record = db.get(ClassSession, session_id)
    if not record:
        raise HTTPException(404, "课堂不存在")
    class_access(db, record.class_id, user)
    return record


@router.get("/classroom/{session_id}")
def classroom(session_id: int, after_id: int = Query(0, ge=0), user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    record = owned_session(db, session_id, user)
    rows = db.query(ClassMessage, SysUser).join(SysUser, SysUser.id == ClassMessage.user_id).filter(
        ClassMessage.session_id == session_id, ClassMessage.id > after_id).order_by(ClassMessage.id).limit(100).all()
    return success_response({"id": record.id, "class_id": record.class_id, "title": record.title, "status": record.status,
                             "stream_url": record.stream_url, "host_id": record.host_id,
                             "messages": [{"id": m.id, "type": m.type, "content": m.content, "user_id": m.user_id,
                                           "nickname": u.nickname, "created_at": m.created_at.isoformat()} for m, u in rows]})


class MessageInput(BaseModel):
    type: Literal["CHAT", "HAND"] = "CHAT"
    content: str = Field(min_length=1, max_length=1000)


@router.post("/classroom/{session_id}/messages")
def send_message(session_id: int, req: MessageInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    record = owned_session(db, session_id, user)
    if record.status != "LIVE":
        raise HTTPException(409, "课堂已经结束")
    message = ClassMessage(session_id=session_id, user_id=user["user_id"], **req.model_dump())
    db.add(message); db.commit()
    return success_response({"id": message.id})


@router.post("/classroom/{session_id}/end")
def end_session(session_id: int, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    record = owned_session(db, session_id, user)
    record.status, record.ended_at = "ENDED", datetime.utcnow()
    db.commit()
    return success_response({"status": record.status})
