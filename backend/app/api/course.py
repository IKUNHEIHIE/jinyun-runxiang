from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing import Optional, List, Any, Literal
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional, require_admin
from app.schemas.common import success_response, error_response
from app.models.entities import (
    Course, CourseChapter, LearningProgress, OfflineSyncEvent,
    Quiz, QuizQuestion, QuizAttempt, UserGrowth, GrowthEvent, Badge, UserBadge
)

router = APIRouter(prefix="/courses", tags=["非遗小课堂"])
learning_router = APIRouter(prefix="/learning", tags=["学习进度"])

class ProgressReportRequest(BaseModel):
    course_id: int
    chapter_id: int
    position_seconds: int = Field(ge=0)
    duration_seconds: int = Field(ge=0)
    completed: bool = False

class OfflineEventItem(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=32)
    payload: dict
    event_time: str

class OfflineSyncRequest(BaseModel):
    events: List[OfflineEventItem] = Field(max_length=100)

class QuizSubmitRequest(BaseModel):
    answers: dict[str, list[str]]  # {"1": ["B"], "2": ["C"]}

class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    subtitle: Optional[str] = "传承津沽非遗文化"
    category: str = "SHADOW_PUPPET"
    age_group: str = "小学低段"
    duration_minutes: int = Field(default=45, ge=0)
    energy_reward: int = Field(default=50, ge=0)
    cover_url: Optional[str] = None
    description: Optional[str] = "非遗美育专业微课"
    status: Literal["DRAFT", "PUBLISHED", "OFFLINE"] = "PUBLISHED"


class UpdateCourseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(default=None, min_length=1, max_length=128)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, min_length=1, max_length=32)
    age_group: Optional[str] = Field(default=None, min_length=1, max_length=32)
    cover_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    energy_reward: Optional[int] = Field(default=None, ge=0)
    status: Optional[Literal["DRAFT", "PUBLISHED", "OFFLINE"]] = None


class CreateChapterRequest(BaseModel):
    seq: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=128)
    video_url: Optional[str] = Field(default=None, max_length=500)
    duration_seconds: int = Field(default=0, ge=0)
    key_points: list[str] = Field(default_factory=list)


class UpdateChapterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seq: Optional[int] = Field(default=None, ge=1)
    title: Optional[str] = Field(default=None, min_length=1, max_length=128)
    video_url: Optional[str] = Field(default=None, max_length=500)
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    key_points: Optional[list[str]] = None


class CreateQuizRequest(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    chapter_id: Optional[int] = None
    pass_score: int = Field(default=60, ge=0)
    energy_reward: int = Field(default=20, ge=0)


class CreateQuestionRequest(BaseModel):
    seq: int = Field(ge=1)
    type: Literal["SINGLE", "MULTIPLE", "JUDGE"] = "SINGLE"
    content: str = Field(min_length=1)
    options: list[dict[str, str]] = Field(min_length=2)
    answers: list[str] = Field(min_length=1)
    explanation: Optional[str] = None
    score: int = Field(default=10, gt=0)


class UpdateQuizRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(default=None, min_length=1, max_length=128)
    chapter_id: Optional[int] = None
    pass_score: Optional[int] = Field(default=None, ge=0)
    energy_reward: Optional[int] = Field(default=None, ge=0)


class UpdateQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seq: Optional[int] = Field(default=None, ge=1)
    type: Optional[Literal["SINGLE", "MULTIPLE", "JUDGE"]] = None
    content: Optional[str] = Field(default=None, min_length=1)
    options: Optional[list[dict[str, str]]] = Field(default=None, min_length=2)
    answers: Optional[list[str]] = Field(default=None, min_length=1)
    explanation: Optional[str] = None
    score: Optional[int] = Field(default=None, gt=0)


def _question_error(req: CreateQuestionRequest):
    keys = [option.get("key", "") for option in req.options]
    if (not all(keys) or any(not option.get("text") for option in req.options)
            or len(set(keys)) != len(keys) or len(set(req.answers)) != len(req.answers)
            or not set(req.answers).issubset(keys)
            or (req.type in ("SINGLE", "JUDGE") and len(req.answers) != 1)):
        return error_response(code=4000, message="题目选项或正确答案无效")
    return None

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
        status=req.status,
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


@router.put("/{course_id}")
def update_course(
    course_id: int,
    req: UpdateCourseRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return error_response(code=4040, message="课程不存在")
    for field, value in req.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(course, field, value)
    db.commit()
    return success_response({"id": course.id, "status": course.status}, message="课程已更新")


@router.post("/{course_id}/chapters")
def create_chapter(
    course_id: int,
    req: CreateChapterRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if not db.query(Course).filter(Course.id == course_id).first():
        return error_response(code=4040, message="课程不存在")
    if db.query(CourseChapter).filter(
        CourseChapter.course_id == course_id, CourseChapter.seq == req.seq
    ).first():
        return error_response(code=4090, message="章节序号已存在")
    chapter = CourseChapter(
        course_id=course_id, seq=req.seq, title=req.title,
        video_url=req.video_url, duration_seconds=req.duration_seconds,
        key_points_json=req.key_points
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return success_response({"id": chapter.id, "course_id": course_id}, message="章节已创建")


@router.put("/{course_id}/chapters/{chapter_id}")
def update_chapter(
    course_id: int,
    chapter_id: int,
    req: UpdateChapterRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    chapter = db.query(CourseChapter).filter(
        CourseChapter.id == chapter_id, CourseChapter.course_id == course_id
    ).first()
    if not chapter:
        return error_response(code=4040, message="章节不存在")
    updates = req.model_dump(exclude_unset=True, exclude_none=True)
    if "seq" in updates and updates["seq"] != chapter.seq and db.query(CourseChapter).filter(
        CourseChapter.course_id == course_id, CourseChapter.seq == updates["seq"]
    ).first():
        return error_response(code=4090, message="章节序号已存在")
    for field, value in updates.items():
        setattr(chapter, "key_points_json" if field == "key_points" else field, value)
    db.commit()
    return success_response({"id": chapter.id, "course_id": course_id}, message="章节已更新")


@router.post("/{course_id}/quizzes")
def create_quiz(
    course_id: int,
    req: CreateQuizRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if not db.query(Course).filter(Course.id == course_id).first():
        return error_response(code=4040, message="课程不存在")
    if req.chapter_id is not None and not db.query(CourseChapter).filter(
        CourseChapter.id == req.chapter_id, CourseChapter.course_id == course_id
    ).first():
        return error_response(code=4040, message="章节不属于该课程")
    quiz = Quiz(
        course_id=course_id, chapter_id=req.chapter_id, title=req.title,
        pass_score=req.pass_score, energy_reward=req.energy_reward
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return success_response({"id": quiz.id, "course_id": course_id}, message="测验已创建")


@router.put("/quiz/{quiz_id}")
def update_quiz(
    quiz_id: int,
    req: UpdateQuizRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return error_response(code=4040, message="测验不存在")
    updates = req.model_dump(exclude_unset=True)
    if "chapter_id" in updates and updates["chapter_id"] is not None and not db.query(CourseChapter).filter(
        CourseChapter.id == updates["chapter_id"], CourseChapter.course_id == quiz.course_id
    ).first():
        return error_response(code=4040, message="章节不属于该课程")
    for field, value in updates.items():
        setattr(quiz, field, value)
    db.commit()
    return success_response({"id": quiz.id}, message="测验已更新")


@router.post("/quiz/{quiz_id}/questions")
def create_quiz_question(
    quiz_id: int,
    req: CreateQuestionRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return error_response(code=4040, message="测验不存在")
    invalid = _question_error(req)
    if invalid:
        return invalid
    if db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id, QuizQuestion.seq == req.seq).first():
        return error_response(code=4090, message="题目序号已存在")
    question = QuizQuestion(
        quiz_id=quiz_id, seq=req.seq, type=req.type, content=req.content,
        options_json=req.options, answer_json=req.answers,
        explanation=req.explanation, score=req.score
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return success_response({"id": question.id, "quiz_id": quiz_id}, message="题目已创建")


@router.put("/quiz/{quiz_id}/questions/{question_id}")
def update_quiz_question(
    quiz_id: int,
    question_id: int,
    req: UpdateQuestionRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    question = db.query(QuizQuestion).filter(
        QuizQuestion.id == question_id, QuizQuestion.quiz_id == quiz_id
    ).first()
    if not question:
        return error_response(code=4040, message="题目不存在")
    updates = req.model_dump(exclude_unset=True, exclude_none=True)
    merged = CreateQuestionRequest.model_validate({
        "seq": question.seq,
        "type": question.type,
        "content": question.content,
        "options": question.options_json,
        "answers": question.answer_json,
        "explanation": question.explanation,
        "score": question.score,
        **updates
    })
    invalid = _question_error(merged)
    if invalid:
        return invalid
    if "seq" in updates and updates["seq"] != question.seq and db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id, QuizQuestion.seq == updates["seq"]
    ).first():
        return error_response(code=4090, message="题目序号已存在")
    for field, value in updates.items():
        setattr(question, {"options": "options_json", "answers": "answer_json"}.get(field, field), value)
    db.commit()
    return success_response({"id": question.id}, message="题目已更新")


@router.delete("/quiz/{quiz_id}/questions/{question_id}")
def delete_quiz_question(
    quiz_id: int,
    question_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    question = db.query(QuizQuestion).filter(
        QuizQuestion.id == question_id, QuizQuestion.quiz_id == quiz_id
    ).first()
    if not question:
        return error_response(code=4040, message="题目不存在")
    if db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).first():
        return error_response(code=4090, message="已有测验记录，不能删除题目")
    db.delete(question)
    db.commit()
    return success_response(message="题目已删除")

@router.get("")
def list_courses(
    category: Optional[str] = None,
    age_group: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    query = db.query(Course)
    if status is not None and status != "PUBLISHED" and (not current_user or current_user.get("role_code") != "ADMIN"):
        return error_response(code=4030, message="无权查看未发布课程")
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
    if not course or (course.status != "PUBLISHED" and (not current_user or current_user.get("role_code") != "ADMIN")):
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


@router.get("/{course_id}/chapters")
def list_course_chapters(
    course_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or (course.status != "PUBLISHED" and (not current_user or current_user.get("role_code") != "ADMIN")):
        return error_response(code=4040, message="课程不存在")

    chapters = db.query(CourseChapter).filter(
        CourseChapter.course_id == course_id
    ).order_by(CourseChapter.seq.asc()).all()
    return success_response([{
        "id": chapter.id,
        "course_id": chapter.course_id,
        "seq": chapter.seq,
        "title": chapter.title,
        "video_url": chapter.video_url,
        "duration_seconds": chapter.duration_seconds,
        "key_points": chapter.key_points_json or []
    } for chapter in chapters])


@learning_router.get("/progress")
def list_my_progress(
    course_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user["user_id"]
    )
    if course_id is not None:
        query = query.filter(LearningProgress.course_id == course_id)
    records = query.order_by(LearningProgress.last_learned_at.desc()).all()
    return success_response([{
        "course_id": record.course_id,
        "chapter_id": record.chapter_id,
        "position_seconds": record.position_seconds,
        "duration_seconds": record.duration_seconds,
        "completed": record.completed,
        "completed_at": record.completed_at,
        "last_learned_at": record.last_learned_at
    } for record in records])


@learning_router.post("/progress")
@router.post("/progress")
def report_progress(
    req: ProgressReportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    course = db.query(Course).filter(
        Course.id == req.course_id,
        Course.status == "PUBLISHED"
    ).first()
    if not course:
        return error_response(code=4040, message="课程不存在或尚未发布")
    chapter = db.query(CourseChapter).filter(
        CourseChapter.id == req.chapter_id,
        CourseChapter.course_id == req.course_id
    ).first()
    if not chapter:
        return error_response(code=4040, message="课程章节不存在或不属于该课程")

    progress, energy_added = _merge_progress(db, user_id, req)
    db.commit()

    return success_response({
        "chapter_id": req.chapter_id,
        "completed": progress.completed,
        "energy_added": energy_added
    })


def _merge_progress(
    db: Session,
    user_id: int,
    req: ProgressReportRequest,
    progress_cache: Optional[dict] = None,
    rewarded_chapters: Optional[set] = None,
):
    """Merge one report; callers commit only after the whole operation succeeds."""
    if progress_cache is not None and req.chapter_id in progress_cache:
        progress = progress_cache[req.chapter_id]
    else:
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.chapter_id == req.chapter_id
        ).first()

    now = datetime.utcnow()
    newly_completed = bool(req.completed and not (progress and progress.completed))
    if progress is None:
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
    else:
        progress.position_seconds = max(progress.position_seconds or 0, req.position_seconds)
        progress.duration_seconds = max(progress.duration_seconds or 0, req.duration_seconds)
        if newly_completed:
            progress.completed = True
            progress.completed_at = now
        progress.last_learned_at = max(progress.last_learned_at or now, now)
    if progress_cache is not None:
        progress_cache[req.chapter_id] = progress

    energy_added = 0
    if newly_completed:
        event_ref = f"ch_{req.chapter_id}"
        exist_event = db.query(GrowthEvent).filter(
            GrowthEvent.user_id == user_id,
            GrowthEvent.event_type == "COURSE_FINISH",
            GrowthEvent.ref_id == event_ref
        ).first()
        if not exist_event and (rewarded_chapters is None or req.chapter_id not in rewarded_chapters):
            energy_added = 10
            db.add(GrowthEvent(
                user_id=user_id,
                event_type="COURSE_FINISH",
                ref_id=event_ref,
                value=energy_added
            ))
            if rewarded_chapters is not None:
                rewarded_chapters.add(req.chapter_id)
            growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).first()
            if growth:
                growth.energy_value += energy_added
                if growth.energy_value >= 1000:
                    growth.level_code = "LV3_CRAFTSMAN"
                elif growth.energy_value >= 500:
                    growth.level_code = "LV2_JOURNEYMAN"
    return progress, energy_added


@router.post("/sync-offline")
def sync_offline(
    req: OfflineSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    success_ids = []
    conflict_ids = []
    seen_ids = set()
    batch_events = {}
    conflicting_ids = set()
    progress_cache = {}
    rewarded_chapters = set()

    for ev in req.events:
        signature = (ev.event_type, ev.payload, ev.event_time)
        if ev.event_id in batch_events and batch_events[ev.event_id] != signature:
            conflicting_ids.add(ev.event_id)
        batch_events[ev.event_id] = signature

    for ev in req.events:
        if ev.event_id in seen_ids:
            continue
        seen_ids.add(ev.event_id)
        if ev.event_id in conflicting_ids:
            conflict_ids.append(ev.event_id)
            continue
        try:
            event_time = datetime.fromisoformat(ev.event_time.replace("Z", "+00:00"))
            if event_time.tzinfo is not None:
                event_time = event_time.astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            conflict_ids.append(ev.event_id)
            continue
        exists = db.query(OfflineSyncEvent).filter(OfflineSyncEvent.event_id == ev.event_id).first()
        if exists:
            if (exists.user_id == user_id and exists.event_type == ev.event_type
                    and exists.payload_json == ev.payload and exists.event_time == event_time):
                success_ids.append(ev.event_id)
            else:
                conflict_ids.append(ev.event_id)
            continue

        if ev.event_type != "PROGRESS_UPDATE":
            conflict_ids.append(ev.event_id)
            continue
        try:
            progress_req = ProgressReportRequest.model_validate(ev.payload)
        except ValidationError:
            conflict_ids.append(ev.event_id)
            continue

        course = db.query(Course).filter(
            Course.id == progress_req.course_id,
            Course.status == "PUBLISHED"
        ).first()
        chapter = db.query(CourseChapter).filter(
            CourseChapter.id == progress_req.chapter_id,
            CourseChapter.course_id == progress_req.course_id
        ).first()
        if not course or not chapter:
            conflict_ids.append(ev.event_id)
            continue

        _merge_progress(db, user_id, progress_req, progress_cache, rewarded_chapters)
        db.add(OfflineSyncEvent(
            event_id=ev.event_id,
            user_id=user_id,
            event_type=ev.event_type,
            payload_json=ev.payload,
            event_time=event_time
        ))
        success_ids.append(ev.event_id)

    db.commit()
    return success_response({
        "synced_count": len(success_ids),
        "success_event_ids": success_ids,
        "synced_event_ids": success_ids,
        "conflict_event_ids": conflict_ids
    }, message="离线事件同步完成")

@router.get("/quiz/{quiz_id}")
def get_quiz(
    quiz_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return error_response(code=4040, message="测验不存在")
    course = db.query(Course).filter(Course.id == quiz.course_id).first()
    if not course or (course.status != "PUBLISHED" and
                      (not current_user or current_user.get("role_code") != "ADMIN")):
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
    course = db.query(Course).filter(Course.id == quiz.course_id, Course.status == "PUBLISHED").first()
    if not course:
        return error_response(code=4040, message="测验所属课程未发布")
    
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
    if not questions:
        return error_response(code=4090, message="测验尚未配置题目")
    question_ids = {str(q.id) for q in questions}
    if set(req.answers) - question_ids:
        return error_response(code=4000, message="提交了不属于该测验的题目")
    
    total_score = 0
    details = []
    for q in questions:
        user_ans = req.answers.get(str(q.id), [])
        correct_ans = q.answer_json
        is_correct = sorted(set(user_ans)) == sorted(correct_ans)
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
