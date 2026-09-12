from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.schemas.common import success_response
from app.models.entities import BannerConfig, Course, CommunityPost, UserGrowth, SysUser

router = APIRouter(prefix="/home", tags=["首页聚合"])

@router.get("/feed")
def get_home_feed(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # 1. 轮播图
    banners = db.query(BannerConfig).filter(
        BannerConfig.status == "ACTIVE",
        BannerConfig.position == "HOME_TOP"
    ).order_by(BannerConfig.sort_no.asc()).all()

    # 2. 推荐课程
    courses = db.query(Course).filter(Course.status == "PUBLISHED").order_by(Course.view_count.desc()).limit(4).all()

    # 3. 热门非遗AI作品
    posts = db.query(CommunityPost).filter(
        CommunityPost.status == "APPROVED"
    ).order_by(CommunityPost.like_count.desc()).limit(4).all()

    # 4. 用户成长卡（若已登录）
    growth_info = None
    if current_user:
        user_id = current_user.get("user_id")
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).first()
        if user and growth:
            growth_info = {
                "nickname": user.nickname,
                "role_code": user.role_code,
                "grade": user.grade,
                "energy_value": growth.energy_value,
                "level_code": growth.level_code,
                "avatar_url": user.avatar_url
            }

    # 5. 民俗日历专题
    festival_topic = {
        "title": "津门中秋拜月与兔子王传习",
        "date": "八月十五",
        "description": "天津旧俗八月十五中秋节，家家户户供奉“泥人张兔儿爷”，品天津特色白皮月饼，寄托团圆安康的美好心愿。",
        "custom": "供兔儿爷、吃白皮月饼、赏海河明月",
        "tag": "津沽民俗专题"
    }

    return success_response({
        "banners": [{
            "id": b.id,
            "title": b.title,
            "image_url": b.image_url,
            "link_url": b.link_url
        } for b in banners],
        "growth": growth_info,
        "recommended_courses": [{
            "id": c.id,
            "title": c.title,
            "subtitle": c.subtitle,
            "category": c.category,
            "age_group": c.age_group,
            "cover_url": c.cover_url,
            "energy_reward": c.energy_reward,
            "duration_minutes": c.duration_minutes
        } for c in courses],
        "popular_artworks": [{
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "cover_url": p.cover_url,
            "like_count": p.like_count,
            "heritage_master_like": p.heritage_master_like
        } for p in posts],
        "festival_topic": festival_topic
    })
