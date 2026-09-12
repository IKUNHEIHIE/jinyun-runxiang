from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.common import success_response, error_response
from app.models.entities import (
    Course, CourseChapter, LearningProgress, OfflineSyncEvent,
    Quiz, QuizQuestion, QuizAttempt, UserGrowth, GrowthEvent, Badge, UserBadge
)

router = APIRouter(prefix="/courses", tags=["非遗小课堂"])

class ProgressReportRequest(BaseModel):
    course_id: int
    chapter_id: int
    position_seconds: int
    duration_seconds: int
    completed: bool = False

class OfflineEventItem(BaseModel):
    event_id: str
    event_type: str
    payload: dict
    event_time: str

class OfflineSyncRequest(BaseModel):
    events: List[OfflineEventItem]

class QuizSubmitRequest(BaseModel):
    answers: dict  # {"1": ["B"], "2": ["C"]}

@router.get("")
def list_courses(
    category: Optional[str] = None,
    age_group: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Course).filter(Course.status == "PUBLISHED")
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
    if not course:
        return error_response(code=4040, message="课程不存在")
    
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
        "chapters": chapter_list,
        "quiz_id": quiz.id if quiz else None
    })

@router.post("/progress")
def report_progress(
    req: ProgressReportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.chapter_id == req.chapter_id
    ).first()

    now = datetime.utcnow()
    newly_completed = False

    if not progress:
        progress = LearningProgress(
            user_id=user_id,
            chapter_id=req.chapter_id,
            course_id=req.course_id,
            position_seconds=req.position_seconds,
            duration_seconds=req.duration_seconds,
            completed=req.completed,
            completed_at=now if req.completed else None,
            last_learned_at=now
        )
        db.add(progress)
        if req.completed:
            newly_completed = True
    else:
        if not progress.completed and req.completed:
            newly_completed = True
            progress.completed = True
            progress.completed_at = now
        progress.position_seconds = req.position_seconds
        progress.duration_seconds = req.duration_seconds
        progress.last_learned_at = now
    
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
    db.commit()

    return success_response({
        "chapter_id": req.chapter_id,
        "completed": req.completed,
        "energy_added": energy_added
    })

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
        # 幂等查重
        exists = db.query(OfflineSyncEvent).filter(OfflineSyncEvent.event_id == ev.event_id).first()
        if exists:
            success_ids.append(ev.event_id)
            continue
        
        try:
            db.add(OfflineSyncEvent(
                event_id=ev.event_id,
                user_id=user_id,
                event_type=ev.event_type,
                payload_json=ev.payload,
                event_time=datetime.fromisoformat(ev.event_time) if "T" in ev.event_time else datetime.utcnow()
            ))
            
            # 合并学习进度
            if ev.event_type == "PROGRESS_UPDATE":
                ch_id = ev.payload.get("chapter_id")
                c_id = ev.payload.get("course_id")
                pos = ev.payload.get("position_seconds", 0)
                dur = ev.payload.get("duration_seconds", 0)
                comp = ev.payload.get("completed", False)

                prog = db.query(LearningProgress).filter(
                    LearningProgress.user_id == user_id,
                    LearningProgress.chapter_id == ch_id
                ).first()
                if not prog:
                    db.add(LearningProgress(
                        user_id=user_id,
                        chapter_id=ch_id,
                        course_id=c_id,
                        position_seconds=pos,
                        duration_seconds=dur,
                        completed=comp,
                        last_learned_at=datetime.utcnow()
                    ))
                else:
                    if pos > prog.position_seconds:
                        prog.position_seconds = pos
                    if comp and not prog.completed:
                        prog.completed = True
            
            success_ids.append(ev.event_id)
        except Exception:
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
