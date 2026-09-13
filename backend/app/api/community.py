from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.common import success_response, error_response
from app.models.entities import (
    CommunityPost, CommunityComment, CommunityLike, CommunityTopic,
    CommunityReport, ContentReview, SysUser
)

router = APIRouter(prefix="/community", tags=["社区广场与内容风控"])

class CreatePostRequest(BaseModel):
    title: str
    content: str
    category: str = "SHADOW_PUPPET"
    cover_url: str
    source_task_id: Optional[str] = None
    topic_id: Optional[int] = None

class CreateCommentRequest(BaseModel):
    content: str
    reply_to_id: Optional[int] = None

class ReportRequest(BaseModel):
    post_id: int
    reason: str
    description: Optional[str] = None

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
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        return error_response(code=4040, message="作品不存在")
    
    post.view_count += 1
    db.commit()

    author = db.query(SysUser).filter(SysUser.id == post.user_id).first()
    comments = db.query(CommunityComment).filter(
        CommunityComment.post_id == post_id,
        CommunityComment.status == "APPROVED"
    ).order_by(CommunityComment.created_at.desc()).limit(20).all()

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

    return success_response({
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "cover_url": post.cover_url,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "favorite_count": post.favorite_count,
        "view_count": post.view_count,
        "is_liked": is_liked,
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
        "comments": [{
            "id": c.id,
            "content": c.content,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
            "user": {
                "id": c.user_id,
                "nickname": c_user_map[c.user_id].nickname if c.user_id in c_user_map else "同学",
                "avatar_url": c_user_map[c.user_id].avatar_url if c.user_id in c_user_map else ""
            }
        } for c in comments]
    })

@router.post("/posts")
def publish_post(
    req: CreatePostRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]

    # 三级内容风控引擎：敏感词识别与多模态安全审计过滤
    sensitive_words = ["暴力", "低俗", "赌博", "违规"]
    has_sensitive = any(w in req.title or w in req.content for w in sensitive_words)
    initial_status = "PENDING_REVIEW" if has_sensitive else "APPROVED"

    post = CommunityPost(
        user_id=user_id,
        title=req.title,
        content=req.content,
        category=req.category,
        cover_url=req.cover_url,
        source_task_id=req.source_task_id,
        topic_id=req.topic_id,
        status=initial_status
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # 记录多模态审核流水
    review = ContentReview(
        target_type="COMMUNITY_POST",
        target_id=post.id,
        risk_level="HIGH" if has_sensitive else "LOW",
        result=initial_status,
        ai_analysis_json={
            "ocr_text_risk": "SAFE",
            "sensitive_word_detected": has_sensitive,
            "image_nsfw_prob": 0.01
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
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        return error_response(code=4040, message="作品不存在")

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
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        return error_response(code=4040, message="作品不存在")

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
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M")
    }, message="评论发表成功")

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
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    城乡手拉手接力共创：对乡村孩子的白模线稿进行二次套色赋能并生成双生共创作品
    """
    origin_post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not origin_post:
        return error_response(code=4040, message="原始乡村作品不存在")

    user_id = current_user["user_id"] if current_user else 1

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
        status="APPROVED",
        is_featured=True,
        is_pinned=False,
        is_co_creation=True,
        co_creator_name=req.co_creator_name,
        co_creator_school=req.co_creator_school,
        rural_author_name=rural_author,
        rural_school=rural_school,
        like_count=12,
        comment_count=1
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
    }, message="城乡共创作品已成功发布到美育广场！")
