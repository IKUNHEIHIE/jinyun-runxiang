from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional, require_admin
from app.schemas.common import success_response, error_response
from app.models.entities import (
    Course, CourseChapter, LearningProgress, OfflineSyncEvent,
    Quiz, QuizQuestion, QuizAttempt, UserGrowth, GrowthEvent, SysUser
)
from app.models.mobile import LearningDay, CourseRating
from app.core.course_badges import award_course_badges

router = APIRouter(prefix="/courses", tags=["非遗小课堂"])

class ProgressReportRequest(BaseModel):
    course_id: int
    chapter_id: int
    position_seconds: int = Field(..., ge=0)
    duration_seconds: int = Field(..., ge=1)
    completed: bool = False

class OfflineEventItem(BaseModel):
    event_id: str
    event_type: str
    payload: dict
    event_time: str

class OfflineSyncRequest(BaseModel):
    events: List[OfflineEventItem] = Field(..., min_length=1, max_length=100)

class QuizSubmitRequest(BaseModel):
    answers: dict  # {"1": ["B"], "2": ["C"]}

class CreateCourseRequest(BaseModel):
    title: str
    subtitle: Optional[str] = "传承津沽非遗文化"
    category: str = "SHADOW_PUPPET"
    age_group: str = "小学低段"
    duration_minutes: int = 45
    energy_reward: int = 50
    cover_url: Optional[str] = None
    description: Optional[str] = "非遗美育专业微课"

@router.post("")
def create_course(
    req: CreateCourseRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    course = Course(
        title=req.title,
        subtitle=req.subtitle,
        category=req.category,
        age_group=req.age_group,
        cover_url=req.cover_url or "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600",
        description=req.description,
        duration_minutes=req.duration_minutes,
        energy_reward=req.energy_reward,
        status="PUBLISHED",
        view_count=0
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return success_response({"id": course.id, "title": course.title}, message="非遗课程已成功创建并发布")

@router.put("/{course_id}/status")
def toggle_course_status(
    course_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return error_response(code=4040, message="课程不存在")
    course.status = "OFFLINE" if course.status == "PUBLISHED" else "PUBLISHED"
    db.commit()
    msg = "课程已上线发布" if course.status == "PUBLISHED" else "课程已下架"
    return success_response({"id": course.id, "status": course.status}, message=msg)

@router.get("")
def list_courses(
    category: Optional[str] = None,
    age_group: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    if status and status != "PUBLISHED" and (not current_user or current_user["role_code"] != "ADMIN"):
        raise HTTPException(403, "仅管理员可查询非公开课程")
    query = db.query(Course)
    if status and status != "ALL":
        query = query.filter(Course.status == status)
    elif status is None:
        query = query.filter(Course.status == "PUBLISHED")
    if category:
        query = query.filter(Course.category == category)
    if age_group:
        query = query.filter(Course.age_group == age_group)
    if keyword:
        query = query.filter(Course.title.ilike(f"%{keyword}%"))
    
    total = query.count()
    courses = query.offset((page - 1) * pageSize).limit(pageSize).all()

    return success_response({
        "list": [{
            "id": c.id,
            "title": c.title,
            "subtitle": c.subtitle,
            "category": c.category,
            "age_group": c.age_group,
            "cover_url": c.cover_url,
            "duration_minutes": c.duration_minutes,
            "energy_reward": c.energy_reward,
            "status": c.status,
            "view_count": c.view_count
        } for c in courses],
        "page": page,
        "pageSize": pageSize,
        "total": total
    })

@router.get("/{course_id}")
def get_course_detail(
    course_id: int,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or (course.status != "PUBLISHED" and (not current_user or current_user["role_code"] != "ADMIN")):
        raise HTTPException(404, "课程不存在")
    
    # 增加浏览量
    course.view_count += 1
    db.commit()

    chapters = db.query(CourseChapter).filter(CourseChapter.course_id == course_id).order_by(CourseChapter.seq.asc()).all()

    # 用户进度
    user_progress_map = {}
    if current_user:
        progs = db.query(LearningProgress).filter(
            LearningProgress.user_id == current_user["user_id"],
            LearningProgress.course_id == course_id
        ).all()
        for p in progs:
            user_progress_map[p.chapter_id] = {
                "position_seconds": p.position_seconds,
                "completed": p.completed
            }

    chapter_list = []
    for ch in chapters:
        prog = user_progress_map.get(ch.id, {"position_seconds": 0, "completed": False})
        chapter_list.append({
            "id": ch.id,
            "seq": ch.seq,
            "title": ch.title,
            "video_url": ch.video_url,
            "duration_seconds": ch.duration_seconds,
            "key_points": ch.key_points_json or [],
            "progress": prog
        })

    # 关联测验
    quiz = db.query(Quiz).filter(Quiz.course_id == course_id).first()
    rating = db.query(func.avg(CourseRating.score)).filter(CourseRating.course_id == course_id).scalar()

    return success_response({
        "id": course.id,
        "title": course.title,
        "subtitle": course.subtitle,
        "category": course.category,
        "age_group": course.age_group,
        "cover_url": course.cover_url,
        "description": course.description,
        "duration_minutes": course.duration_minutes,
        "energy_reward": course.energy_reward,
        "view_count": course.view_count,
        "rating": round(float(rating), 1) if rating is not None else None,
        "chapters": chapter_list,
        "quiz_id": quiz.id if quiz else None
    })

def apply_progress(req: ProgressReportRequest, current_user: dict, db: Session,
                   learned_at: Optional[datetime] = None):
    db.query(SysUser).filter_by(id=current_user["user_id"]).with_for_update().one()
    chapter = db.query(CourseChapter).join(Course, Course.id == CourseChapter.course_id).filter(
        CourseChapter.id == req.chapter_id, CourseChapter.course_id == req.course_id,
        Course.status == "PUBLISHED").first()
    if not chapter:
        raise HTTPException(404, "课程章节不存在")
    user_id = current_user["user_id"]
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.chapter_id == req.chapter_id
    ).first()

    now = datetime.utcnow()
    activity_at = learned_at or now
    newly_completed = False

    if not progress:
        progress = LearningProgress(
            user_id=user_id,
            chapter_id=req.chapter_id,
            course_id=req.course_id,
            position_seconds=req.position_seconds,
            duration_seconds=req.duration_seconds,
            completed=req.completed,
            completed_at=activity_at if req.completed else None,
            last_learned_at=activity_at
        )
        db.add(progress)
        if req.completed:
            newly_completed = True
    else:
        if not progress.completed and req.completed:
            newly_completed = True
            progress.completed = True
            progress.completed_at = activity_at
        if activity_at >= progress.last_learned_at:
            progress.position_seconds = req.position_seconds
            progress.duration_seconds = req.duration_seconds
            progress.last_learned_at = activity_at

    if req.position_seconds > 0 or req.completed:
        day = activity_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).date()
        # The user row lock above serializes same-user progress reports.
        if db.get(LearningDay, (user_id, day)) is None:
            db.add(LearningDay(user_id=user_id, day=day))
    
    # 首次学完章节奖励能量
    energy_added = 0
    if newly_completed:
        # 幂等检查
        event_ref = f"ch_{req.chapter_id}"
        exist_event = db.query(GrowthEvent).filter(
            GrowthEvent.user_id == user_id,
            GrowthEvent.event_type == "COURSE_FINISH",
            GrowthEvent.ref_id == event_ref
        ).first()
        if not exist_event:
            energy_added = 10
            db.add(GrowthEvent(
                user_id=user_id,
                event_type="COURSE_FINISH",
                ref_id=event_ref,
                value=energy_added
            ))
            growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).first()
            if growth:
                growth.energy_value += energy_added
                if growth.energy_value >= 1000:
                    growth.level_code = "LV3_CRAFTSMAN"
                elif growth.energy_value >= 500:
                    growth.level_code = "LV2_JOURNEYMAN"

    return success_response({
        "chapter_id": req.chapter_id,
        "completed": bool(progress.completed),
        "energy_added": energy_added,
        "badges_unlocked": award_course_badges(db, user_id),
    })


@router.post("/progress")
def report_progress(req: ProgressReportRequest, current_user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    result = apply_progress(req, current_user, db)
    db.commit()
    return result

@router.post("/sync-offline")
def sync_offline(
    req: OfflineSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    success_ids = []
    conflict_ids = []

    for ev in req.events:
        exists = db.query(OfflineSyncEvent).filter(OfflineSyncEvent.event_id == ev.event_id).first()
        if exists:
            (success_ids if exists.user_id == user_id else conflict_ids).append(ev.event_id)
            continue
        try:
            with db.begin_nested():
                if ev.event_type != "PROGRESS_UPDATE":
                    raise ValueError("不支持的离线事件")
                progress_request = ProgressReportRequest.model_validate(ev.payload)
                event_at = datetime.fromisoformat(ev.event_time.replace("Z", "+00:00"))
                if event_at.tzinfo is None:
                    event_at = event_at.replace(tzinfo=timezone.utc)
                event_at = event_at.astimezone(timezone.utc).replace(tzinfo=None)
                now = datetime.utcnow()
                if event_at > now + timedelta(minutes=5):
                    raise ValueError("离线事件时间不能在未来")
                event_at = min(event_at, now)
                apply_progress(progress_request, current_user, db, learned_at=event_at)
                db.add(OfflineSyncEvent(event_id=ev.event_id, user_id=user_id,
                    event_type=ev.event_type, payload_json=ev.payload,
                    event_time=event_at))
                db.flush()
            success_ids.append(ev.event_id)
        except (ValueError, OverflowError, HTTPException):
            conflict_ids.append(ev.event_id)

    db.commit()
    return success_response({
        "synced_count": len(success_ids),
        "success_event_ids": success_ids,
        "synced_event_ids": success_ids,
        "conflict_event_ids": conflict_ids
    }, message="离线事件同步完成")

@router.get("/quiz/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return error_response(code=4040, message="测验不存在")
    
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.seq.asc()).all()

    return success_response({
        "id": quiz.id,
        "title": quiz.title,
        "pass_score": quiz.pass_score,
        "energy_reward": quiz.energy_reward,
        "questions": [{
            "id": q.id,
            "seq": q.seq,
            "type": q.type,
            "content": q.content,
            "options": q.options_json,
            "score": q.score
        } for q in questions]
    })

@router.post("/quiz/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int,
    req: QuizSubmitRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    db.query(SysUser).filter_by(id=user_id).with_for_update().one()
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return error_response(code=4040, message="测验不存在")
    
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
    
    total_score = 0
    details = []
    for q in questions:
        user_ans = req.answers.get(str(q.id), [])
        correct_ans = q.answer_json
        is_correct = sorted(user_ans) == sorted(correct_ans)
        item_score = q.score if is_correct else 0
        total_score += item_score
        details.append({
            "question_id": q.id,
            "is_correct": is_correct,
            "user_answers": user_ans,
            "correct_answers": correct_ans,
            "explanation": q.explanation
        })

    passed = total_score >= quiz.pass_score

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user_id,
        score=total_score,
        passed=passed,
        answer_json={"answers": req.answers, "details": details}
    )
    db.add(attempt)

    # 首次及格奖励能量
    energy_reward = 0
    if passed:
        event_ref = f"quiz_{quiz_id}"
        exist_ev = db.query(GrowthEvent).filter(
            GrowthEvent.user_id == user_id,
            GrowthEvent.event_type == "QUIZ_PASS",
            GrowthEvent.ref_id == event_ref
        ).first()
        if not exist_ev:
            energy_reward = quiz.energy_reward
            db.add(GrowthEvent(
                user_id=user_id,
                event_type="QUIZ_PASS",
                ref_id=event_ref,
                value=energy_reward
            ))
            growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).first()
            if growth:
                growth.energy_value += energy_reward

    db.commit()

    return success_response({
        "score": total_score,
        "pass_score": quiz.pass_score,
        "passed": passed,
        "energy_reward": energy_reward,
        "details": details
    })
