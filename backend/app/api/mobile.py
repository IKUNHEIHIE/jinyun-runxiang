"""Mobile business endpoints. All displayed counters come from stored records."""
import secrets
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.course_badges import COURSE_BADGE_CATEGORIES, course_badge_progress
from app.core.task_assets import owned_task_for_asset
from app.core.security import get_current_user, get_current_user_optional, require_admin, require_teacher
from app.schemas.common import success_response
from app.models.entities import (
    SysUser, UserProfile, UserGrowth, GrowthEvent, Course, CourseChapter,
    LearningProgress, CommunityPost, CommunityLike, Badge, UserBadge,
    TeacherClass, ClassMember, Assignment, AssignmentSubmission, AssignmentReview, Asset, AiTask,
    Contest, ContestEntry,
)
from app.models.mobile import HeritageEntry, UserCollection, UserFollow, CourseRating, UserFeedback, LearningDay

router = APIRouter(prefix="/mobile", tags=["Android 手机客户端"])


class CanvasElementInput(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=32)
    src: str = Field(min_length=1, max_length=500)
    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)
    scale: float = Field(ge=.5, le=2, allow_inf_nan=False)
    rotation: float = Field(ge=-180, le=180, allow_inf_nan=False)


class SavedDesignInput(BaseModel):
    cover_url: str = Field(min_length=1, max_length=500)
    composition: list[CanvasElementInput] = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=128)
    render_style: Literal["青铜氧化", "鎏金拓印", "彩色渲染"] = "青铜氧化"


@router.post("/workshop/designs")
def save_canvas_design(req: SavedDesignInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    asset = db.query(Asset).filter_by(file_url=req.cover_url, created_by=user["user_id"], asset_type="IMAGE").first()
    if not asset:
        raise HTTPException(404, "设计图片不存在或不属于当前用户")
    task = AiTask(task_id=uuid.uuid4().hex, user_id=user["user_id"], tool_type="BRONZE", status="SUCCESS", progress=100,
                  input_json={"title": req.title, "composition": [e.model_dump() for e in req.composition],
                              "render_style": req.render_style},
                  result_summary_json={"title": req.title, "rendered_image_url": asset.file_url,
                                       "colored_image_url": asset.file_url, "source": "user_canvas", "llm_generated": False})
    db.add(task)
    db.commit()
    return success_response({"task_id": task.task_id, "status": task.status, "input": task.input_json,
                             "result": task.result_summary_json})


@router.get("/workshop/bronze")
def bronze_workshop(db: Session = Depends(get_db)):
    query = db.query(CommunityPost).filter_by(category="BRONZE", status="APPROVED")
    works = db.query(CommunityPost, SysUser).join(SysUser, SysUser.id == CommunityPost.user_id).filter(
        CommunityPost.category == "BRONZE", CommunityPost.status == "APPROVED").order_by(
        CommunityPost.created_at.desc(), CommunityPost.id.desc()).limit(12).all()
    return success_response({
        "design_count": query.count(),
        "designer_count": db.query(func.count(func.distinct(CommunityPost.user_id))).filter(
            CommunityPost.category == "BRONZE", CommunityPost.status == "APPROVED").scalar(),
        "works": [{"id": p.id, "title": p.title, "cover_url": p.cover_url,
                   "nickname": u.nickname} for p, u in works],
    })


@router.get("/courses")
def mobile_courses(category: str | None = None, age_group: str | None = None,
                   page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=50),
                   user: dict | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    query = db.query(Course).filter(Course.status == "PUBLISHED")
    if category:
        query = query.filter(Course.category == category)
    if age_group:
        aliases = {"PRIMARY_LOW": ["PRIMARY_LOW", "小学低段"], "PRIMARY_HIGH": ["PRIMARY_HIGH", "小学高段"]}
        query = query.filter(Course.age_group.in_(aliases.get(age_group, [age_group])))
    total = query.count()
    result = []
    for c in query.order_by(Course.id).offset((page - 1) * pageSize).limit(pageSize).all():
        chapter_count = db.query(CourseChapter).filter_by(course_id=c.id).count()
        completed = db.query(LearningProgress).filter_by(course_id=c.id, user_id=user["user_id"], completed=True).count() if user else 0
        rating = db.query(func.avg(CourseRating.score)).filter_by(course_id=c.id).scalar()
        result.append({"id": c.id, "title": c.title, "subtitle": c.subtitle, "cover_url": c.cover_url,
                       "category": c.category, "age_group": c.age_group, "duration_minutes": c.duration_minutes,
                       "chapter_count": chapter_count, "progress_percent": round(completed / chapter_count * 100) if chapter_count else 0,
                       "rating": round(float(rating), 1) if rating is not None else None})
    return success_response({"list": result, "total": total, "page": page})


def lock_user(db, uid):
    return db.query(SysUser).filter(SysUser.id == uid).with_for_update().one()


def heritage_json(entry):
    return {"id": entry.id, "title": entry.title, "category": entry.category,
            "era": entry.era, "summary": entry.summary, "cover_url": entry.cover_url,
            "model_url": entry.model_url, "content": entry.content_json or {}}


HERITAGE_CATEGORY_KEYWORDS = {
    "泥人张": "CLAY_FIGURINE", "彩塑": "CLAY_FIGURINE",
    "风筝": "KITE", "风筝魏": "KITE",
    "杨柳青": "NEW_YEAR_PAINTING", "年画": "NEW_YEAR_PAINTING",
    "瓷器": "CERAMICS", "陶瓷": "CERAMICS",
    "皮影": "SHADOW_PUPPET",
    "青铜": "BRONZE",
    "刺绣": "EMBROIDERY",
}


@router.get("/heritage")
def heritage_list(keyword: str = Query("", max_length=100), category: str | None = None,
                  page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50),
                  db: Session = Depends(get_db)):
    query = db.query(HeritageEntry).filter(HeritageEntry.status == "PUBLISHED")
    if keyword:
        conditions = [HeritageEntry.title.ilike(f"%{keyword}%"),
                      HeritageEntry.summary.ilike(f"%{keyword}%"),
                      HeritageEntry.era.ilike(f"%{keyword}%")]
        matched_category = next((code for label, code in HERITAGE_CATEGORY_KEYWORDS.items()
                                 if label in keyword), None)
        if matched_category:
            conditions.append(HeritageEntry.category == matched_category)
        query = query.filter(or_(*conditions))
    if category:
        query = query.filter(HeritageEntry.category == category)
    total = query.count()
    entries = query.order_by(HeritageEntry.id).offset((page - 1) * page_size).limit(page_size).all()
    stats = {
        "heritage_projects": db.query(func.count(HeritageEntry.id))
        .filter(HeritageEntry.status == "PUBLISHED").scalar() or 0,
        "teaching_resources": db.query(func.count(Course.id))
        .filter(Course.status == "PUBLISHED").scalar() or 0,
    }
    return success_response({"list": [heritage_json(e) for e in entries], "total": total,
                             "page": page, "stats": stats})


@router.get("/heritage/{entry_id}")
def heritage_detail(entry_id: int, user: dict | None = Depends(get_current_user_optional),
                    db: Session = Depends(get_db)):
    entry = db.get(HeritageEntry, entry_id)
    if not entry or (entry.status != "PUBLISHED" and (not user or user["role_code"] != "ADMIN")):
        raise HTTPException(404, "非遗条目不存在")
    data = heritage_json(entry)
    data["collected"] = bool(
        user and db.get(UserCollection, (user["user_id"], "HERITAGE", entry_id))
    )
    return success_response(data)


class HeritageInput(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    category: str = Field(min_length=1, max_length=64)
    era: str = Field("", max_length=128)
    summary: str = Field("", max_length=1000)
    cover_url: str = Field("", max_length=500)
    model_url: str = Field("", max_length=500)
    content: dict = Field(default_factory=dict)
    status: Literal["PUBLISHED", "DRAFT"] = "PUBLISHED"


@router.post("/heritage")
def create_heritage(req: HeritageInput, user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    values = req.model_dump(exclude={"content"})
    entry = HeritageEntry(**values, content_json=req.content)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return success_response(heritage_json(entry))


@router.put("/heritage/{entry_id}")
def update_heritage(entry_id: int, req: HeritageInput, user: dict = Depends(require_admin),
                   db: Session = Depends(get_db)):
    entry = db.get(HeritageEntry, entry_id)
    if not entry:
        raise HTTPException(404, "非遗条目不存在")
    for name, value in req.model_dump(exclude={"content"}).items():
        setattr(entry, name, value)
    entry.content_json = req.content
    db.commit()
    return success_response(heritage_json(entry))


@router.post("/me/checkin")
def daily_checkin(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = user["user_id"]
    lock_user(db, uid)
    day = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    event = db.query(GrowthEvent).filter_by(user_id=uid, event_type="DAILY_SIGNIN", ref_id=day).first()
    growth = db.get(UserGrowth, uid)
    if not growth:
        growth = UserGrowth(user_id=uid, energy_value=0)
        db.add(growth)
    if not event:
        db.add(GrowthEvent(user_id=uid, event_type="DAILY_SIGNIN", ref_id=day, value=10))
        growth.energy_value += 10
    db.commit()
    return success_response({"date": day, "already_checked_in": bool(event),
                             "energy_added": 0 if event else 10, "energy_value": growth.energy_value})


class ProfileInput(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    grade: str = Field("", max_length=32)
    bio: str = Field("", max_length=255)
    school_name: str = Field("", max_length=128)
    district: str = Field("", max_length=64)


@router.put("/me/profile")
def update_profile(req: ProfileInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    record = lock_user(db, user["user_id"])
    record.nickname, record.grade = req.nickname, req.grade
    profile = db.get(UserProfile, record.id)
    if not profile:
        profile = UserProfile(user_id=record.id)
        db.add(profile)
    for key in ("bio", "school_name", "district"):
        setattr(profile, key, getattr(req, key))
    db.commit()
    return success_response(req.model_dump(), message="个人资料已保存")


@router.get("/me/summary")
def profile_summary(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = user["user_id"]
    growth = db.get(UserGrowth, uid)
    day = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    progresses = db.query(LearningProgress).filter_by(user_id=uid).all()
    posts = db.query(CommunityPost).filter_by(user_id=uid)
    return success_response({
        "energy_value": growth.energy_value if growth else 0,
        "post_count": posts.count(),
        "like_count": int(db.query(func.coalesce(func.sum(CommunityPost.like_count), 0)).filter_by(user_id=uid).scalar()),
        "following_count": db.query(UserFollow).filter_by(follower_id=uid).count(),
        "follower_count": db.query(UserFollow).filter_by(followed_id=uid).count(),
        "collection_count": db.query(UserCollection).filter_by(user_id=uid).count(),
        "badge_count": db.query(UserBadge).filter_by(user_id=uid).count(),
        "learning_seconds": sum(p.position_seconds for p in progresses),
        "completed_chapters": sum(bool(p.completed) for p in progresses),
        "learning_days": db.query(LearningDay).filter_by(user_id=uid).count(),
        "checked_in": db.query(GrowthEvent).filter_by(user_id=uid, event_type="DAILY_SIGNIN", ref_id=day).first() is not None,
        "data_source": "database",
    })


@router.get("/badges")
def badge_catalog(user: dict | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    owned = {b.badge_id: b for b in db.query(UserBadge).filter_by(user_id=user["user_id"]).all()} if user else {}
    course_progress = course_badge_progress(db, user["user_id"] if user else None)
    order = {code: i for i, code in enumerate(COURSE_BADGE_CATEGORIES)}
    catalog = sorted(db.query(Badge).all(), key=lambda b: (order.get(b.code, len(order)), b.id))
    return success_response([{"id": b.id, "code": b.code, "name": b.name, "description": b.description,
                              "icon_url": b.icon_url, "unlocked": b.id in owned,
                              "unlocked_at": owned[b.id].unlocked_at.isoformat() if b.id in owned and owned[b.id].unlocked_at else None,
                              **({"course_progress": {**course_progress[COURSE_BADGE_CATEGORIES[b.code]], "required_courses": 1,
                                                        "completed_courses": course_progress[COURSE_BADGE_CATEGORIES[b.code]]["completed_courses"] if user else None}}
                                 if b.code in COURSE_BADGE_CATEGORIES else {})}
                             for b in catalog])


@router.get("/me/reviews")
def my_reviews(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(CourseRating, Course).join(Course, Course.id == CourseRating.course_id).filter(
        CourseRating.user_id == user["user_id"]).order_by(CourseRating.updated_at.desc()).all()
    return success_response([{"id": course.id, "course_id": course.id, "title": course.title,
                              "cover_url": course.cover_url, "rating": rating.score,
                              "comment": rating.comment, "created_at": rating.updated_at.isoformat() if rating.updated_at else None} for rating, course in rows])


def collection_target(db, kind, target_id, user_id=None):
    if kind == "ASSET":
        asset = db.get(Asset, target_id)
        if not asset:
            raise HTTPException(404, "创作内容不存在")
        owned_task_for_asset(db, asset, user_id)
        return asset
    model, status_field, status = {
        "COURSE": (Course, "status", "PUBLISHED"),
        "POST": (CommunityPost, "status", "APPROVED"),
        "HERITAGE": (HeritageEntry, "status", "PUBLISHED"),
    }[kind]
    target = db.get(model, target_id)
    if not target or getattr(target, status_field) != status:
        raise HTTPException(404, "内容不存在或尚未公开")
    return target


@router.post("/collections/{kind}/{target_id}")
def toggle_collection(kind: Literal["COURSE", "POST", "HERITAGE", "ASSET"], target_id: int,
                      user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    lock_user(db, user["user_id"])
    target = collection_target(db, kind, target_id, user["user_id"])
    key = (user["user_id"], kind, target_id)
    record = db.get(UserCollection, key)
    active = record is None
    if record:
        db.delete(record)
    else:
        db.add(UserCollection(user_id=key[0], target_type=kind, target_id=target_id))
    if kind == "POST":
        db.flush()
        target.favorite_count = db.query(UserCollection).filter_by(target_type=kind, target_id=target_id).count()
    db.commit()
    return success_response({"collected": active})


@router.get("/me/collections")
def collections(kind: Literal["COURSE", "POST", "HERITAGE", "ASSET"] | None = None,
                user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(UserCollection).filter_by(user_id=user["user_id"])
    if kind:
        query = query.filter_by(target_type=kind)
    result = []
    for record in query.order_by(UserCollection.created_at.desc()).all():
        try:
            target = collection_target(db, record.target_type, record.target_id, user["user_id"])
        except HTTPException:
            continue
        if record.target_type == "ASSET":
            task = owned_task_for_asset(db, target, user["user_id"])
            summary = task.result_summary_json
            result.append({"type":"ASSET", "id":target.id, "task_id":task.task_id, "tool_type":task.tool_type,
                           "title":summary.get("title") or summary.get("role_type") or "我的皮影创作",
                           "cover_url":target.file_url, "created_at":record.created_at.isoformat()})
            continue
        result.append({"type": record.target_type, "id": target.id, "title": target.title,
                       "cover_url": target.cover_url, "created_at": record.created_at.isoformat()})
    return success_response(result)


@router.post("/users/{target_id}/follow")
def follow_user(target_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = user["user_id"]
    lock_user(db, uid)
    target = db.get(SysUser, target_id)
    if target_id == uid:
        raise HTTPException(422, "不能关注自己")
    if not target or target.status != "ACTIVE":
        raise HTTPException(404, "用户不存在")
    follow = db.get(UserFollow, (uid, target_id))
    active = follow is None
    if follow:
        db.delete(follow)
    else:
        db.add(UserFollow(follower_id=uid, followed_id=target_id))
    db.commit()
    return success_response({"following": active})


@router.get("/me/follows")
def follows(direction: Literal["following", "followers"] = "following",
            user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = user["user_id"]
    if direction == "following":
        query = db.query(SysUser).join(UserFollow, UserFollow.followed_id == SysUser.id).filter(UserFollow.follower_id == uid)
    else:
        query = db.query(SysUser).join(UserFollow, UserFollow.follower_id == SysUser.id).filter(UserFollow.followed_id == uid)
    return success_response([{"id": u.id, "nickname": u.nickname, "avatar_url": u.avatar_url} for u in query.all()])


@router.get("/me/posts")
def my_posts(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.query(CommunityPost).filter_by(user_id=user["user_id"]).order_by(CommunityPost.created_at.desc()).all()
    return success_response([{"id": p.id, "title": p.title, "cover_url": p.cover_url,
                              "status": p.status, "like_count": p.like_count} for p in posts])


@router.get("/me/learning")
def learning_history(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(LearningProgress, Course, CourseChapter).join(Course, Course.id == LearningProgress.course_id).join(
        CourseChapter, CourseChapter.id == LearningProgress.chapter_id).filter(
        LearningProgress.user_id == user["user_id"], Course.status == "PUBLISHED").order_by(
        LearningProgress.last_learned_at.desc()).all()
    return success_response([{"course_id": c.id, "chapter_id": ch.id, "title": c.title,
                              "chapter_title": ch.title, "cover_url": c.cover_url,
                              "position_seconds": p.position_seconds, "duration_seconds": ch.duration_seconds,
                              "completed": p.completed, "last_learned_at": p.last_learned_at.isoformat()}
                             for p, c, ch in rows])


class RatingInput(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: str = Field("", max_length=1000)


@router.put("/courses/{course_id}/rating")
def rate_course(course_id: int, req: RatingInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    lock_user(db, user["user_id"])
    collection_target(db, "COURSE", course_id)
    record = db.get(CourseRating, (user["user_id"], course_id))
    if not record:
        record = CourseRating(user_id=user["user_id"], course_id=course_id)
        db.add(record)
    record.score, record.comment = req.score, req.comment
    db.commit()
    return success_response({"score": record.score, "comment": record.comment})


class FeedbackInput(BaseModel):
    content: str = Field(min_length=5, max_length=5000)
    contact: str = Field("", max_length=128)


@router.post("/feedback")
def send_feedback(req: FeedbackInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    content = req.content.strip()
    if len(content) < 5:
        raise HTTPException(422, "反馈内容至少需要5个字")
    record = UserFeedback(user_id=user["user_id"], content=content, contact=req.contact.strip())
    db.add(record)
    db.commit()
    return success_response({"id": record.id, "status": record.status}, message="反馈已提交")


def feedback_data(record: UserFeedback, admin: bool = False):
    result = {"id": record.id, "content": record.content, "status": record.status,
              "reply_text": record.reply_text or "", "created_at": record.created_at.isoformat(),
              "handled_at": record.handled_at.isoformat() if record.handled_at else None}
    if admin:
        result.update(user_id=record.user_id, contact=record.contact, handled_by=record.handled_by)
    return result


@router.get("/me/feedback")
def my_feedback(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return success_response([feedback_data(record) for record in db.query(UserFeedback).filter_by(
        user_id=user["user_id"]).order_by(UserFeedback.id.desc()).all()])


@router.get("/admin/feedback")
def admin_feedback(status: Literal["PENDING", "PROCESSING", "RESOLVED"] | None = None,
                   page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                   user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    query = db.query(UserFeedback)
    if status:
        query = query.filter_by(status=status)
    total = query.count()
    records = query.order_by(UserFeedback.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success_response({"items": [feedback_data(record, admin=True) for record in records],
                             "total": total, "page": page, "page_size": page_size})


class FeedbackAction(BaseModel):
    status: Literal["PROCESSING", "RESOLVED"]
    reply_text: str = Field("", max_length=5000)


@router.put("/admin/feedback/{feedback_id}")
def handle_feedback(feedback_id: int, req: FeedbackAction, user: dict = Depends(require_admin),
                    db: Session = Depends(get_db)):
    reply = req.reply_text.strip()
    if req.status == "RESOLVED" and not reply:
        raise HTTPException(422, "请填写给用户的回复")
    if req.status == "PROCESSING" and reply:
        raise HTTPException(422, "填写回复后请选择回复并完成")
    record = db.query(UserFeedback).filter_by(id=feedback_id).with_for_update().first()
    if not record:
        raise HTTPException(404, "反馈不存在")
    if record.status == req.status and (record.reply_text or "") == reply:
        return success_response(feedback_data(record, admin=True))
    if record.status not in ("PENDING", "PROCESSING"):
        raise HTTPException(409, "该反馈已回复，请刷新列表查看结果")
    record.status, record.reply_text = req.status, reply
    record.handled_by, record.handled_at = user["user_id"], datetime.utcnow()
    db.commit()
    return success_response(feedback_data(record, admin=True))


class ClassInput(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    grade: str = Field(min_length=1, max_length=32)


@router.post("/teacher/classes")
def create_class(req: ClassInput, user: dict = Depends(require_teacher), db: Session = Depends(get_db)):
    record = TeacherClass(teacher_id=user["user_id"], name=req.name, grade=req.grade,
                          invite_code=secrets.token_hex(4).upper())
    db.add(record)
    db.commit()
    return success_response({"id": record.id, "name": record.name, "invite_code": record.invite_code})


class JoinInput(BaseModel):
    invite_code: str = Field(min_length=4, max_length=16)


@router.post("/classes/join")
def join_class(req: JoinInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user["role_code"] != "STUDENT":
        raise HTTPException(403, "仅学生可加入班级")
    lock_user(db, user["user_id"])
    record = db.query(TeacherClass).filter_by(invite_code=req.invite_code.strip().upper(), status="ACTIVE").first()
    if not record:
        raise HTTPException(404, "班级邀请码不存在")
    member = db.query(ClassMember).filter_by(class_id=record.id, student_id=user["user_id"]).first()
    if not member:
        db.add(ClassMember(class_id=record.id, student_id=user["user_id"]))
    else:
        member.status = "ACTIVE"
    db.flush()
    record.student_count = db.query(ClassMember).filter_by(class_id=record.id, status="ACTIVE").count()
    db.commit()
    return success_response({"id": record.id, "name": record.name})


@router.get("/me/assignments")
def student_assignments(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    assignments = db.query(Assignment).join(ClassMember, ClassMember.class_id == Assignment.class_id).filter(
        ClassMember.student_id == user["user_id"], ClassMember.status == "ACTIVE", Assignment.status == "PUBLISHED").all()
    results = []
    for a in assignments:
        contest = db.get(Contest, a.contest_id) if a.contest_id else None
        if contest and not db.query(ContestEntry).filter_by(
                contest_id=contest.id, student_id=user["user_id"]).first():
            continue
        sub = db.query(AssignmentSubmission).filter_by(assignment_id=a.id, student_id=user["user_id"]).first()
        review = db.query(AssignmentReview).filter_by(submission_id=sub.id).first() if sub else None
        scores_visible = contest is None or contest.status == "PUBLISHED"
        results.append({"id": a.id, "title": a.title, "description": a.description, "class_id": a.class_id,
                        "deadline": a.deadline.isoformat(), "tool_type": a.tool_type, "type": a.type,
                        "contest": {"id": contest.id, "status": contest.status,
                                    "round_no": contest.round_no} if contest else None,
                        "submission": {"id": sub.id, "status": sub.status, "content": sub.content,
                                       "score": review.score if review and scores_visible else None,
                                       "comment": review.comment if review and scores_visible else None} if sub else None})
    return success_response(results)


class SubmissionInput(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    asset_id: int | None = Field(None, gt=0)
    source_task_id: str | None = Field(None, max_length=32)


@router.post("/assignments/{assignment_id}/submit")
def submit_assignment(assignment_id: int, req: SubmissionInput,
                      user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user["role_code"] != "STUDENT":
        raise HTTPException(403, "仅学生可提交作业")
    lock_user(db, user["user_id"])
    a = db.get(Assignment, assignment_id)
    if not a or a.status != "PUBLISHED" or not db.query(ClassMember).filter_by(
            class_id=a.class_id, student_id=user["user_id"], status="ACTIVE").first():
        raise HTTPException(404, "作业不存在或您未加入该班级")
    if a.contest_id:
        contest = db.get(Contest, a.contest_id)
        if not contest or contest.status != "OPEN":
            raise HTTPException(409, "对抗赛已截止提交")
        if not db.query(ContestEntry).filter_by(
                contest_id=a.contest_id, student_id=user["user_id"]).first():
            raise HTTPException(404, "您不在本轮参赛名单中")
    if a.deadline < datetime.utcnow():
        raise HTTPException(409, "作业已截止")
    if req.asset_id:
        asset = db.get(Asset, req.asset_id)
        if not asset or asset.created_by != user["user_id"]:
            raise HTTPException(404, "作品资源不存在")
    if req.source_task_id and not db.query(AiTask).filter_by(
            task_id=req.source_task_id, user_id=user["user_id"], status="SUCCESS").first():
        raise HTTPException(404, "创作任务不存在或尚未完成")
    sub = db.query(AssignmentSubmission).filter_by(assignment_id=a.id, student_id=user["user_id"]).first()
    if sub and sub.status == "REVIEWED":
        raise HTTPException(409, "作业已经批改，不能覆盖提交")
    if not sub:
        sub = AssignmentSubmission(assignment_id=a.id, student_id=user["user_id"])
        db.add(sub)
    sub.content, sub.asset_id, sub.source_task_id = req.content, req.asset_id, req.source_task_id
    sub.submitted_at, sub.status = datetime.utcnow(), "SUBMITTED"
    db.commit()
    return success_response({"id": sub.id, "status": sub.status}, message="作业已提交")
