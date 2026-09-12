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
    sort: str = "latest",  # latest, hot, featured
    topic_id: Optional[int] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(CommunityPost).filter(CommunityPost.status == "APPROVED")
    if topic_id:
        query = query.filter(CommunityPost.topic_id == topic_id)
    if category:
        query = query.filter(CommunityPost.category == category)
    
    if sort == "hot":
        query = query.order_by(CommunityPost.like_count.desc())
    elif sort == "featured":
        query = query.filter(CommunityPost.is_featured == True).order_by(CommunityPost.created_at.desc())
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

    # 三级内容风控检查：简单敏感词校验模拟
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
