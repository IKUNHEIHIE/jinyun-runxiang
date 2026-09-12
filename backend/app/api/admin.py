from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.common import success_response, error_response
from app.models.entities import (
    OperationStatDaily, CommunityPost, ContentReview,
    Course, AiModel, SysUser, OrderMain, FundRecord, Device
)

router = APIRouter(prefix="/admin", tags=["运营管理后台"])

class ReviewActionRequest(BaseModel):
    action: str  # APPROVE, REJECT, OFFLINE, FEATURE
    comment: Optional[str] = "审核通过"

@router.get("/dashboard")
def get_dashboard_data(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # 历史日统计
    stats = db.query(OperationStatDaily).order_by(OperationStatDaily.stat_date.asc()).all()

    # 实时汇总
    total_users = db.query(SysUser).count()
    total_courses = db.query(Course).count()
    total_posts = db.query(CommunityPost).count()
    total_orders = db.query(OrderMain).count()
    
    # 汇总美育基金总额
    funds = db.query(FundRecord).all()
    fund_total_cents = sum([f.amount_cents for f in funds])

    return success_response({
        "kpi": {
            "dau": 2420,
            "mau": 9600,
            "total_users": total_users,
            "total_courses": total_courses,
            "total_posts": total_posts,
            "total_orders": total_orders,
            "fund_total_yuan": fund_total_cents / 100.0,
            "active_devices": 1
        },
        "trends": [{
            "date": s.stat_date.strftime("%m-%d") if hasattr(s.stat_date, "strftime") else str(s.stat_date),
            "dau": s.dau,
            "course_learn": s.course_learn_count,
            "ai_generations": s.ai_generate_count,
            "posts": s.community_post_count,
            "gmv_yuan": s.order_gmv_cents / 100.0,
            "fund_yuan": s.fund_added_cents / 100.0
        } for s in stats]
    })

@router.get("/reviews")
def list_pending_reviews(
    status: str = "PENDING_REVIEW",
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    posts = db.query(CommunityPost).filter(CommunityPost.status == status).all()
    res = []
    for p in posts:
        rev = db.query(ContentReview).filter(
            ContentReview.target_type == "COMMUNITY_POST",
            ContentReview.target_id == p.id
        ).first()
        author = db.query(SysUser).filter(SysUser.id == p.user_id).first()
        res.append({
            "post_id": p.id,
            "title": p.title,
            "content": p.content,
            "category": p.category,
            "cover_url": p.cover_url,
            "author_name": author.nickname if author else "学生",
            "risk_level": rev.risk_level if rev else "LOW",
            "ai_analysis": rev.ai_analysis_json if rev else {},
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else ""
        })
    return success_response(res)

@router.post("/reviews/{post_id}/action")
def review_post_action(
    post_id: int,
    req: ReviewActionRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        return error_response(code=4040, message="作品不存在")

    if req.action == "APPROVE":
        post.status = "APPROVED"
    elif req.action == "REJECT":
        post.status = "REJECTED"
    elif req.action == "OFFLINE":
        post.status = "OFFLINE"
    elif req.action == "FEATURE":
        post.is_featured = True

    # 记录审计日志
    rev = db.query(ContentReview).filter(
        ContentReview.target_type == "COMMUNITY_POST",
        ContentReview.target_id == post_id
    ).first()
    if rev:
        rev.result = post.status
        rev.reviewer_id = current_user["user_id"]
        rev.review_comment = req.comment
        rev.reviewed_at = datetime.utcnow()

    db.commit()
    return success_response({"post_id": post_id, "new_status": post.status}, message="审核处置已生效")
