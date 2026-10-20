from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from urllib.parse import urlsplit

from app.core.database import get_db
from app.core import file_urls, moderation
from app.core.task_assets import task_result_urls
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.common import success_response, error_response
from app.models.entities import (
    CommunityPost, CommunityComment, CommunityLike, CommunityTopic,
    CommunityReport, ContentReview, SysUser, Asset, AiTask
)
from app.models.mobile import CommunityPostDetail, CommunityCommentLike, UserCollection, UserFollow

router = APIRouter(prefix="/community", tags=["社区广场与内容风控"])

class ArtworkSpecification(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    label: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=128)


class AppreciationPoint(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=64)
    body: str = Field(min_length=1, max_length=2000)


class CreatePostRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=10000)
    category: str = Field("SHADOW_PUPPET", min_length=1, max_length=32)
    cover_url: str = Field(min_length=1, max_length=500)
    source_task_id: Optional[str] = Field(None, max_length=32)
    topic_id: Optional[int] = Field(None, gt=0)
    gallery: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(default_factory=list, max_length=10)
    specifications: list[ArtworkSpecification] = Field(default_factory=list, max_length=12)
    appreciation: list[AppreciationPoint] = Field(default_factory=list, max_length=10)

class CreateCommentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=1000)
    reply_to_id: Optional[int] = Field(None, gt=0)

class ReportRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    post_id: int = Field(gt=0)
    reason: str = Field(min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=500)


def visible_post(db, post_id, user=None, public_only=False, lock=False):
    query = db.query(CommunityPost).filter_by(id=post_id)
    record = (query.with_for_update() if lock else query).first()
    if not record or (record.status != "APPROVED" and (public_only or not user or
            (user["user_id"] != record.user_id and user["role_code"] != "ADMIN"))):
        raise HTTPException(404, "作品不存在")
    return record


def comment_records(db, rows, user=None):
    user_ids = {c.user_id for c in rows}
    parents = {p.id: p for p in db.query(CommunityComment).filter(
        CommunityComment.id.in_([c.reply_to_id for c in rows if c.reply_to_id]),
        CommunityComment.status == "APPROVED").all()}
    user_ids.update(p.user_id for p in parents.values())
    authors = {u.id:u for u in db.query(SysUser).filter(SysUser.id.in_(user_ids)).all()}
    liked = {r.comment_id for r in db.query(CommunityCommentLike).filter(
        CommunityCommentLike.user_id == user["user_id"], CommunityCommentLike.comment_id.in_([c.id for c in rows])).all()} if user else set()
    def nickname(uid):
        return authors[uid].nickname if uid in authors else "同学"
    result = []
    for c in rows:
        parent = parents.get(c.reply_to_id)
        result.append({"id": c.id, "content": c.content, "created_at": c.created_at.isoformat() if c.created_at else "",
            "like_count": c.like_count, "is_liked": c.id in liked,
            "reply_to": {"id":parent.id,"nickname":nickname(parent.user_id),"content":parent.content[:200]} if parent and parent.post_id == c.post_id else None,
            "user":{"id":c.user_id,"nickname":nickname(c.user_id),"avatar_url":authors[c.user_id].avatar_url if c.user_id in authors else ""}})
    return result


@router.get("/posts/{post_id}/comments")
def comments(post_id: int, page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=50),
             current_user: dict = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    visible_post(db, post_id, current_user)
    query = db.query(CommunityComment).filter_by(post_id=post_id, status="APPROVED")
    total = query.count()
    rows = query.order_by(CommunityComment.id.desc()).offset((page-1)*pageSize).limit(pageSize).all()
    return success_response({"list":comment_records(db, rows, current_user),"total":total,"page":page,"pageSize":pageSize})


@router.get("/posts/{post_id}/related")
def related(post_id: int, db: Session = Depends(get_db)):
    original = visible_post(db, post_id, public_only=True)
    rows = db.query(CommunityPost, SysUser).join(SysUser, SysUser.id == CommunityPost.user_id).filter(
        CommunityPost.status == "APPROVED", CommunityPost.id != post_id,
        CommunityPost.category == original.category).order_by(CommunityPost.like_count.desc(), CommunityPost.id.desc()).limit(6).all()
    return success_response([{"id":p.id,"title":p.title,"cover_url":p.cover_url,"author":u.nickname} for p,u in rows])

@router.get("/posts")
def list_posts(
    sort: str = "latest",  # latest, hot, featured, co_creation
    topic_id: Optional[int] = None,
    category: Optional[str] = None,
    is_co_creation: Optional[bool] = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(CommunityPost).filter(CommunityPost.status == "APPROVED")
    if topic_id:
        query = query.filter(CommunityPost.topic_id == topic_id)
    if category:
        query = query.filter(CommunityPost.category == category)
    if is_co_creation is not None:
        query = query.filter(CommunityPost.is_co_creation == is_co_creation)
    
    if sort == "hot":
        query = query.order_by(CommunityPost.like_count.desc())
    elif sort == "featured":
        query = query.filter(CommunityPost.is_featured == True).order_by(CommunityPost.created_at.desc())
    elif sort == "co_creation":
        query = query.filter(CommunityPost.is_co_creation == True).order_by(CommunityPost.created_at.desc())
    else:
        query = query.order_by(CommunityPost.created_at.desc())

    total = query.count()
    posts = query.offset((page - 1) * pageSize).limit(pageSize).all()

    # 获取作者信息
    user_ids = [p.user_id for p in posts]
    users = db.query(SysUser).filter(SysUser.id.in_(user_ids)).all() if user_ids else []
    user_map = {u.id: u for u in users}

    return success_response({
        "list": [{
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "category": p.category,
            "cover_url": p.cover_url,
            "like_count": p.like_count,
            "comment_count": p.comment_count,
            "favorite_count": p.favorite_count,
            "is_featured": p.is_featured,
            "heritage_master_like": p.heritage_master_like,
            "is_co_creation": bool(p.is_co_creation),
            "co_creator_name": p.co_creator_name,
            "co_creator_school": p.co_creator_school,
            "rural_author_name": p.rural_author_name,
            "rural_school": p.rural_school,
            "rural_original_url": p.rural_original_url,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            "author": {
                "id": p.user_id,
                "nickname": user_map[p.user_id].nickname if p.user_id in user_map else "非遗学员",
                "avatar_url": user_map[p.user_id].avatar_url if p.user_id in user_map else ""
            }
        } for p in posts],
        "page": page,
        "pageSize": pageSize,
        "total": total
    })

@router.get("/posts/{post_id}")
def get_post_detail(
    post_id: int,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    post = visible_post(db, post_id, current_user, lock=True)
    
    post.view_count += 1
    db.commit()

    author = db.query(SysUser).filter(SysUser.id == post.user_id).first()
    comments = db.query(CommunityComment).filter(
        CommunityComment.post_id == post_id,
        CommunityComment.status == "APPROVED"
    ).order_by(CommunityComment.id.desc()).limit(20).all()

    # 查评论者
    c_user_ids = [c.user_id for c in comments]
    c_users = db.query(SysUser).filter(SysUser.id.in_(c_user_ids)).all() if c_user_ids else []
    c_user_map = {u.id: u for u in c_users}

    is_liked = False
    if current_user:
        exist_like = db.query(CommunityLike).filter(
            CommunityLike.post_id == post_id,
            CommunityLike.user_id == current_user["user_id"]
        ).first()
        is_liked = exist_like is not None

    details = db.get(CommunityPostDetail, post_id)
    gallery = list(dict.fromkeys([post.cover_url] + (details.gallery_json if details else [])))
    return success_response({
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "cover_url": post.cover_url,
        "status": post.status,
        "gallery": [url for url in gallery if url],
        "specifications": details.specifications_json if details else [],
        "appreciation": details.appreciation_json if details else [],
        "like_count": post.like_count,
        "comment_count": db.query(CommunityComment).filter_by(post_id=post_id, status="APPROVED").count(),
        "favorite_count": post.favorite_count,
        "view_count": post.view_count,
        "is_liked": is_liked,
        "is_collected": bool(current_user and db.get(UserCollection, (current_user["user_id"], "POST", post_id))),
        "is_following": bool(current_user and db.get(UserFollow, (current_user["user_id"], post.user_id))),
        "is_featured": post.is_featured,
        "heritage_master_like": post.heritage_master_like,
        "is_co_creation": getattr(post, "is_co_creation", False),
        "co_creator_name": getattr(post, "co_creator_name", None),
        "co_creator_school": getattr(post, "co_creator_school", None),
        "rural_author_name": getattr(post, "rural_author_name", None),
        "rural_school": getattr(post, "rural_school", None),
        "rural_original_url": getattr(post, "rural_original_url", None),
        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M") if post.created_at else "",
        "author": {
            "id": author.id if author else post.user_id,
            "nickname": author.nickname if author else "津门工匠",
            "avatar_url": author.avatar_url if author else "",
            "role_code": author.role_code if author else "STUDENT"
        },
        "comments": comment_records(db, comments, current_user)
    })

@router.post("/posts")
def publish_post(
    req: CreatePostRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]

    db.query(SysUser).filter_by(id=user_id).with_for_update().one()
    task = db.query(AiTask).filter_by(task_id=req.source_task_id, user_id=user_id, status="SUCCESS").first() if req.source_task_id else None
    if req.source_task_id and not task:
        raise HTTPException(404, "创作任务不存在或不属于当前用户")
    task_urls = task_result_urls(task) if task else set()
    cover_url = file_urls.split_signature(req.cover_url)[0]
    gallery = list(dict.fromkeys([cover_url] + [file_urls.split_signature(url)[0] for url in req.gallery]))
    if len(gallery) > 10:
        raise HTTPException(422, "作品图集最多包含10张图片")
    for url in gallery:
        parsed = urlsplit(url)
        if url in task_urls:
            continue
        if url.startswith("/static/"):
            if not db.query(Asset).filter_by(file_url=url, created_by=user_id, asset_type="IMAGE").first():
                raise HTTPException(404, "图片不存在或不属于当前用户")
        elif parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise HTTPException(422, "作品图片必须为本人上传的资源或HTTPS图片地址")
    if req.topic_id and not db.query(CommunityTopic).filter_by(id=req.topic_id, status="ACTIVE").first():
        raise HTTPException(404, "话题不存在")

    # Keyword screening only. No image model has been configured here.
    sensitive_words = moderation.screening_words(db)
    submitted_text = req.title + req.content + " ".join(s.label+s.value for s in req.specifications) + " ".join(p.title+p.body for p in req.appreciation)
    # Same rule set as the workshop: hidden characters and injection phrasing route the post to a
    # human review queue instead of slipping through a raw substring match.
    has_sensitive = moderation.find_blocked_text(submitted_text, sensitive_words) is not None
    initial_status = "PENDING_REVIEW" if has_sensitive else "APPROVED"

    post = CommunityPost(
        user_id=user_id,
        title=req.title,
        content=req.content,
        category=req.category,
        cover_url=cover_url,
        source_task_id=req.source_task_id,
        topic_id=req.topic_id,
        status=initial_status
    )
    db.add(post)
    db.flush()
    db.add(CommunityPostDetail(post_id=post.id, gallery_json=gallery,
        specifications_json=[s.model_dump() for s in req.specifications],
        appreciation_json=[p.model_dump() for p in req.appreciation]))

    # 记录多模态审核流水
    review = ContentReview(
        target_type="COMMUNITY_POST",
        target_id=post.id,
        risk_level="HIGH" if has_sensitive else "LOW",
        result=initial_status,
        ai_analysis_json={
            "sensitive_word_detected": has_sensitive,
            "screening_method": "keyword_rules",
            "ocr_status": "NOT_CONFIGURED",
            "image_review_status": "NOT_CONFIGURED"
        }
    )
    db.add(review)
    db.commit()

    msg = "作品发布成功，已提交人工复审" if has_sensitive else "作品发布成功"
    return success_response({
        "id": post.id,
        "title": post.title,
        "status": post.status
    }, message=msg)

@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    db.query(SysUser).filter_by(id=user_id).with_for_update().one()
    post = visible_post(db, post_id, public_only=True, lock=True)

    like = db.query(CommunityLike).filter(
        CommunityLike.post_id == post_id,
        CommunityLike.user_id == user_id
    ).first()

    if like:
        db.delete(like)
        post.like_count = max(0, post.like_count - 1)
        db.commit()
        return success_response({"is_liked": False, "like_count": post.like_count}, message="已取消点赞")
    else:
        db.add(CommunityLike(post_id=post_id, user_id=user_id))
        post.like_count += 1
        db.commit()
        return success_response({"is_liked": True, "like_count": post.like_count}, message="点赞成功")

@router.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int,
    req: CreateCommentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    db.query(SysUser).filter_by(id=user_id).with_for_update().one()
    post = visible_post(db, post_id, public_only=True, lock=True)
    if req.reply_to_id and not db.query(CommunityComment).filter_by(
            id=req.reply_to_id, post_id=post_id, status="APPROVED").first():
        raise HTTPException(422, "回复的评论不存在或不属于该作品")

    comment = CommunityComment(
        post_id=post_id,
        user_id=user_id,
        reply_to_id=req.reply_to_id,
        content=req.content,
        status="APPROVED"
    )
    db.add(comment)
    post.comment_count += 1
    db.commit()
    db.refresh(comment)

    return success_response({
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat()
    }, message="评论发表成功")


@router.post("/comments/{comment_id}/like")
def like_comment(comment_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SysUser).filter_by(id=current_user["user_id"]).with_for_update().one()
    comment = db.query(CommunityComment).filter_by(id=comment_id, status="APPROVED").with_for_update().first()
    if not comment:
        raise HTTPException(404, "评论不存在")
    visible_post(db, comment.post_id, public_only=True)
    like = db.get(CommunityCommentLike, (comment_id, current_user["user_id"]))
    if like:
        db.delete(like); comment.like_count = max(0, comment.like_count - 1)
    else:
        db.add(CommunityCommentLike(comment_id=comment_id, user_id=current_user["user_id"]))
        comment.like_count += 1
    db.commit()
    return success_response({"is_liked":not bool(like),"like_count":comment.like_count})

@router.get("/topics")
def list_topics(db: Session = Depends(get_db)):
    topics = db.query(CommunityTopic).filter(CommunityTopic.status == "ACTIVE").all()
    return success_response([{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "cover_url": t.cover_url,
        "post_count": t.post_count
    } for t in topics])

@router.post("/reports")
def report_post(
    req: ReportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    visible_post(db, req.post_id, public_only=True)
    rep = CommunityReport(
        post_id=req.post_id,
        reporter_id=current_user["user_id"],
        reason=req.reason,
        description=req.description,
        status="PENDING"
    )
    db.add(rep)
    db.commit()
    return success_response(message="举报已提交，运营团队将尽快处理")

class SubmitCoCreateRequest(BaseModel):
    co_creator_name: str
    co_creator_school: Optional[str] = "城市美育共创志愿者"
    colored_cover_url: str
    co_note: str

@router.post("/posts/{post_id}/co-create")
def submit_co_creation(
    post_id: int,
    req: SubmitCoCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    城乡手拉手接力共创：对乡村孩子的白模线稿进行二次套色赋能并生成双生共创作品
    """
    origin_post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not origin_post or origin_post.status != "APPROVED":
        raise HTTPException(404, "原始公开作品不存在")

    user_id = current_user["user_id"]

    # 获取原作者昵称与学校
    origin_user = db.query(SysUser).filter(SysUser.id == origin_post.user_id).first()
    rural_author = origin_user.nickname if origin_user else (origin_post.rural_author_name or "乡村小匠人")
    rural_school = origin_post.rural_school or "乡村非遗美育教学点"

    co_post = CommunityPost(
        user_id=user_id,
        title=f"《{origin_post.title}》· 城乡手拉手联名共创",
        content=f"【乡村原作者·{rural_author}（{rural_school}）】：创作了初始非遗线稿。\n【城市接力赋能·{req.co_creator_name}（{req.co_creator_school}）】：{req.co_note}",
        category=origin_post.category,
        cover_url=req.colored_cover_url,
        rural_original_url=origin_post.rural_original_url or origin_post.cover_url,
        source_task_id=origin_post.source_task_id,
        status="PENDING_REVIEW",
        is_featured=False,
        is_pinned=False,
        is_co_creation=True,
        co_creator_name=req.co_creator_name,
        co_creator_school=req.co_creator_school,
        rural_author_name=rural_author,
        rural_school=rural_school,
        like_count=0,
        comment_count=0
    )
    db.add(co_post)
    db.commit()
    db.refresh(co_post)

    return success_response({
        "co_post_id": co_post.id,
        "title": co_post.title,
        "cover_url": co_post.cover_url,
        "co_creator_name": co_post.co_creator_name,
        "rural_author_name": co_post.rural_author_name
    }, message="共创作品已提交审核")
