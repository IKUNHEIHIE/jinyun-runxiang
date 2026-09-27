import json
import time
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

from app.core.database import get_db
from app.core.security import require_admin, hash_password
from app.schemas.common import success_response, error_response
from app.models.entities import (
    CommunityPost, CommunityComment, CommunityReport, ContentReview,
    Course, LearningProgress, AiTask, Activity, ActivityAttendance, SysUser, AuthSession,
    SysConfig, UserProfile, UserGrowth, Badge, UserBadge, PhilanthropySupply
)

router = APIRouter(prefix="/admin", tags=["运营管理后台"])

class ReviewActionRequest(BaseModel):
    action: Literal["APPROVE", "REJECT", "OFFLINE", "FEATURE"]
    comment: Optional[str] = "审核通过"


class CommentReviewActionRequest(BaseModel):
    action: Literal["APPROVE", "REJECT", "OFFLINE"]
    comment: str = Field(min_length=1, max_length=500)


class ReportActionRequest(BaseModel):
    action: Literal["DISMISS", "RESOLVE", "OFFLINE_POST"]
    note: str = Field(min_length=1, max_length=255)

@router.get("/dashboard")
def get_dashboard_data(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    today = datetime.utcnow().date()
    first_day = today - timedelta(days=6)
    first_moment = datetime.combine(first_day, datetime.min.time())
    total_users = db.query(SysUser).count()
    total_courses = db.query(Course).count()
    total_posts = db.query(CommunityPost).filter(CommunityPost.status == "APPROVED").count()
    completed_chapters = db.query(LearningProgress).filter(LearningProgress.completed == True).count()
    ai_tasks = db.query(AiTask).count()
    pending_posts = db.query(CommunityPost).filter(CommunityPost.status == "PENDING_REVIEW").count()
    pending_comments = db.query(CommunityComment).filter(CommunityComment.status == "PENDING_REVIEW").count()
    pending_reports = db.query(CommunityReport).filter(CommunityReport.status == "PENDING").count()
    activity_count = db.query(Activity).count()
    attendance_count = db.query(ActivityAttendance).count()

    course_daily = dict(db.query(
        func.date(LearningProgress.completed_at), func.count(LearningProgress.id)
    ).filter(
        LearningProgress.completed_at >= first_moment
    ).group_by(func.date(LearningProgress.completed_at)).all())
    ai_daily = dict(db.query(
        func.date(AiTask.created_at), func.count(AiTask.task_id)
    ).filter(
        AiTask.created_at >= first_moment
    ).group_by(func.date(AiTask.created_at)).all())
    course_daily = {str(day): count for day, count in course_daily.items()}
    ai_daily = {str(day): count for day, count in ai_daily.items()}
    hot_courses = db.query(Course).filter(Course.status == "PUBLISHED").order_by(
        Course.view_count.desc()
    ).limit(5).all()

    return success_response({
        "kpi": {
            "dau": None,
            "mau": None,
            "total_users": total_users,
            "total_courses": total_courses,
            "total_posts": total_posts,
            "completed_chapters": completed_chapters,
            "ai_tasks": ai_tasks,
            "pending_reviews": pending_posts + pending_comments + pending_reports,
            "activities": activity_count,
            "attendances": attendance_count
        },
        "pending_reviews": {
            "posts": pending_posts,
            "comments": pending_comments,
            "reports": pending_reports
        },
        "hot_courses": [{
            "id": course.id,
            "title": course.title,
            "views": course.view_count or 0
        } for course in hot_courses],
        "trends": [{
            "date": (first_day + timedelta(days=offset)).strftime("%m-%d"),
            "course_completed": course_daily.get((first_day + timedelta(days=offset)).isoformat(), 0),
            "ai_tasks": ai_daily.get((first_day + timedelta(days=offset)).isoformat(), 0)
        } for offset in range(7)]
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
            "is_co_creation": bool(p.is_co_creation),
            "co_creator_name": p.co_creator_name,
            "rural_author_name": p.rural_author_name,
            "is_featured": bool(p.is_featured),
            "risk_level": rev.risk_level if rev and rev.ai_analysis_json else None,
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

    if req.action in ("APPROVE", "REJECT") and post.status not in ("PENDING_REVIEW", "MANUAL_REVIEW", "REJECTED"):
        return error_response(code=4090, message="当前作品状态不可执行审核操作")
    if req.action in ("OFFLINE", "FEATURE") and post.status != "APPROVED":
        return error_response(code=4090, message="只有已发布作品可执行此操作")

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


@router.get("/comment-reviews")
def list_comment_reviews(
    status: Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "OFFLINE"] = "PENDING_REVIEW",
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    comments = db.query(CommunityComment).filter(CommunityComment.status == status).all()
    return success_response([{
        "id": comment.id,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "status": comment.status,
        "created_at": comment.created_at
    } for comment in comments])


@router.post("/comment-reviews/{comment_id}/action")
def review_comment_action(
    comment_id: int,
    req: CommentReviewActionRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    comment = db.query(CommunityComment).filter(CommunityComment.id == comment_id).first()
    if not comment:
        return error_response(code=4040, message="评论不存在")
    post = db.query(CommunityPost).filter(CommunityPost.id == comment.post_id).first()
    if not post:
        return error_response(code=4040, message="作品不存在")
    if req.action == "APPROVE" and comment.status not in ("PENDING_REVIEW", "REJECTED"):
        return error_response(code=4090, message="当前评论状态不可通过")
    if req.action == "REJECT" and comment.status != "PENDING_REVIEW":
        return error_response(code=4090, message="当前评论状态不可驳回")
    if req.action == "OFFLINE" and comment.status != "APPROVED":
        return error_response(code=4090, message="只有已公开评论可下线")
    if req.action == "APPROVE":
        comment.status = "APPROVED"
        post.comment_count = (post.comment_count or 0) + 1
    elif req.action == "REJECT":
        comment.status = "REJECTED"
    else:
        comment.status = "OFFLINE"
        post.comment_count = max(0, (post.comment_count or 0) - 1)

    review = db.query(ContentReview).filter(
        ContentReview.target_type == "COMMUNITY_COMMENT",
        ContentReview.target_id == comment_id
    ).first()
    if not review:
        review = ContentReview(target_type="COMMUNITY_COMMENT", target_id=comment_id)
        db.add(review)
    review.result = comment.status
    review.reviewer_id = current_user["user_id"]
    review.review_comment = req.comment
    review.reviewed_at = datetime.utcnow()
    db.commit()
    return success_response({"comment_id": comment_id, "status": comment.status}, message="评论审核已完成")


@router.get("/reports")
def list_community_reports(
    status: Literal["PENDING", "HANDLED", "REJECTED"] = "PENDING",
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    reports = db.query(CommunityReport).filter(CommunityReport.status == status).all()
    return success_response([{
        "id": report.id,
        "post_id": report.post_id,
        "reporter_id": report.reporter_id,
        "reason": report.reason,
        "description": report.description,
        "status": report.status,
        "handled_by": report.handled_by,
        "handled_note": report.handled_note,
        "created_at": report.created_at,
        "handled_at": report.handled_at
    } for report in reports])


@router.post("/reports/{report_id}/action")
def handle_community_report(
    report_id: int,
    req: ReportActionRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        return error_response(code=4040, message="举报不存在")
    if report.status != "PENDING":
        return error_response(code=4090, message="举报已处理")
    post = db.query(CommunityPost).filter(CommunityPost.id == report.post_id).first()
    if not post:
        return error_response(code=4040, message="被举报作品不存在")
    if req.action == "OFFLINE_POST":
        post.status = "OFFLINE"
    report.status = "REJECTED" if req.action == "DISMISS" else "HANDLED"
    report.handled_by = current_user["user_id"]
    report.handled_note = req.note
    report.handled_at = datetime.utcnow()
    db.add(ContentReview(
        target_type="COMMUNITY_REPORT",
        target_id=report.id,
        result=report.status,
        reviewer_id=current_user["user_id"],
        review_comment=req.note,
        reviewed_at=report.handled_at,
        ai_analysis_json={"action": req.action, "post_id": report.post_id}
    ))
    db.commit()
    return success_response({"report_id": report.id, "status": report.status}, message="举报处理已完成")

# -----------------------------------------------------------------------------
# 系统设置模块 (A-08)：大模型 API 接入与全站自定义配置
# -----------------------------------------------------------------------------

class LlmSettingsDTO(BaseModel):
    provider: str = "DeepSeek"
    api_base: str = "https://api.deepseek.com/v1"
    api_key: str
    model_name: str = "deepseek-chat"
    vision_model_name: Optional[str] = "deepseek-vl"
    temperature: float = 0.7
    max_tokens: int = 4096
    enable_proxy: bool = False

class SiteSettingsDTO(BaseModel):
    site_name: str = "津韵润乡——天津非遗赋能乡村美育智能应用"
    site_logo_text: str = "津"
    site_subtitle: str = "传承津派非遗文化，点亮乡村美育之光"
    icp_filing: str = "津ICP备20260912号-1"
    contact_email: str = "heritage@jinyun.tj.edu.cn"
    enable_registration: bool = True
    maintenance_mode: bool = False
    default_energy_reward: int = 100
    fund_rate_default: float = 15.0
    sensitive_words: str = "暴力,低俗,赌博,违规,涉黄,反动,作弊"
    theme_color: str = "#8B4A2F"

class SaveSettingsRequest(BaseModel):
    llm_settings: LlmSettingsDTO
    site_settings: SiteSettingsDTO

class TestLlmRequest(BaseModel):
    provider: str
    api_base: str
    api_key: str
    model_name: str

@router.get("/settings")
def get_system_settings(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取大模型接入配置与全站自定义设置"""
    llm_cfg = db.query(SysConfig).filter(SysConfig.config_key == "llm_settings").first()
    site_cfg = db.query(SysConfig).filter(SysConfig.config_key == "site_settings").first()

    default_llm = {
        "provider": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "api_key": "sk-d7a8********************9b2c",
        "model_name": "deepseek-chat",
        "vision_model_name": "deepseek-vl",
        "temperature": 0.7,
        "max_tokens": 4096,
        "enable_proxy": False
    }

    default_site = {
        "site_name": "津韵润乡——天津非遗赋能乡村美育智能应用",
        "site_logo_text": "津",
        "site_subtitle": "传承津派非遗文化，点亮乡村美育之光",
        "icp_filing": "津ICP备20260912号-1",
        "contact_email": "heritage@jinyun.tj.edu.cn",
        "enable_registration": True,
        "maintenance_mode": False,
        "default_energy_reward": 100,
        "fund_rate_default": 15.0,
        "sensitive_words": "暴力,低俗,赌博,违规,涉黄,反动,作弊",
        "theme_color": "#8B4A2F"
    }

    llm_data = json.loads(llm_cfg.config_value) if llm_cfg else default_llm
    site_data = json.loads(site_cfg.config_value) if site_cfg else default_site

    return success_response({
        "llm_settings": llm_data,
        "site_settings": site_data,
        "supported_providers": [
            {"label": "DeepSeek (深度求索 - 推荐)", "value": "DeepSeek", "default_base": "https://api.deepseek.com/v1", "default_model": "deepseek-chat"},
            {"label": "OpenAI (GPT-4o / GPT-4o-mini)", "value": "OpenAI", "default_base": "https://api.openai.com/v1", "default_model": "gpt-4o"},
            {"label": "Google Gemini (Gemini 1.5 Pro / Flash)", "value": "Gemini", "default_base": "https://generativelanguage.googleapis.com/v1beta", "default_model": "gemini-1.5-pro"},
            {"label": "阿里云通义千问 (Qwen-Max / Plus)", "value": "Qwen", "default_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-max"},
            {"label": "百度千帆文心一言 (ERNIE-4.0)", "value": "Qianfan", "default_base": "https://aip.baidubce.com/v2", "default_model": "ernie-4.0-8k"},
            {"label": "本地私有化部署 (Ollama / vLLM)", "value": "Local_Ollama", "default_base": "http://127.0.0.1:11434/v1", "default_model": "qwen2.5:14b"}
        ]
    })

@router.post("/settings")
def save_system_settings(
    req: SaveSettingsRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """保存大模型接入配置与全站自定义设置"""
    # 1. 保存大模型配置
    llm_cfg = db.query(SysConfig).filter(SysConfig.config_key == "llm_settings").first()
    llm_val = json.dumps(req.llm_settings.dict(), ensure_ascii=False)
    if not llm_cfg:
        llm_cfg = SysConfig(config_key="llm_settings", config_value=llm_val, description="大模型及多模态API接入配置")
        db.add(llm_cfg)
    else:
        llm_cfg.config_value = llm_val

    # 2. 保存全站自定义配置
    site_cfg = db.query(SysConfig).filter(SysConfig.config_key == "site_settings").first()
    site_val = json.dumps(req.site_settings.dict(), ensure_ascii=False)
    if not site_cfg:
        site_cfg = SysConfig(config_key="site_settings", config_value=site_val, description="网站全站自定义与运营规则配置")
        db.add(site_cfg)
    else:
        site_cfg.config_value = site_val

    db.commit()
    return success_response(message="系统配置与大模型参数保存成功！")

@router.post("/settings/test-llm")
def test_llm_connection(
    req: TestLlmRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """真实大模型接口 HTTP 探测与连通性探活"""
    actual_key = (req.api_key or "").strip()
    if not actual_key or "*" in actual_key:
        cfg = db.query(SysConfig).filter(SysConfig.config_key == "llm_settings").first()
        if cfg and cfg.config_value:
            try:
                saved_val = json.loads(cfg.config_value)
                saved_key = saved_val.get("api_key", "")
                if saved_key and "*" not in saved_key:
                    actual_key = saved_key
            except Exception:
                pass

    if not actual_key or "*" in actual_key or len(actual_key) < 8:
        return error_response(code=4001, message="请先输入有效的 API Key 后再发起连通性测试")

    # 发起真实的大模型接口 HTTP 探测
    base_url = req.api_base.strip().rstrip("/")
    endpoint = f"{base_url}/chat/completions"

    start_time = time.time()
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {actual_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": req.model_name.strip(),
                    "messages": [
                        {"role": "user", "content": "你好，请仅回复【津韵润乡测试连通成功】八个字。"}
                    ],
                    "max_tokens": 30
                }
            )
            latency = int((time.time() - start_time) * 1000)

            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                return success_response({
                    "provider": req.provider,
                    "model_name": req.model_name,
                    "status": "ONLINE (LIVE)",
                    "latency_ms": latency,
                    "is_real_call": True,
                    "reply_preview": reply.strip()
                }, message=f"真实 DeepSeek 官方服务连接成功！网络往返耗时: {latency}ms")
            else:
                err_body = resp.text[:300]
                return error_response(code=4002, message=f"DeepSeek 服务商返回错误 (HTTP {resp.status_code}): {err_body}")
    except httpx.ConnectTimeout:
        return error_response(code=5004, message="连接服务商 API Base 超时，请检查网络或是否开启代理网关")
    except httpx.ConnectError as e:
        return error_response(code=5002, message=f"无法建立与 {base_url} 的网络连接: {str(e)}")
    except Exception as e:
        return error_response(code=5001, message=f"大模型连通性探测异常: {str(e)}")


# -----------------------------------------------------------------------------
# 用户系统模块 (A-04)：用户管理、增删改查、角色权限与启停
# -----------------------------------------------------------------------------

class CreateUserDTO(BaseModel):
    username: str
    password: str = Field(min_length=8, max_length=64)
    nickname: str
    phone: Optional[str] = None
    role_code: str = "STUDENT"  # ADMIN, TEACHER, STUDENT
    grade: Optional[str] = "小学四年级"
    school_name: Optional[str] = "蓟州区下营镇中心小学"

class UpdateUserDTO(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
    role_code: Optional[str] = None
    grade: Optional[str] = None
    school_name: Optional[str] = None

class StatusDTO(BaseModel):
    status: str  # ACTIVE, DISABLED

class ResetPwdDTO(BaseModel):
    new_password: str = Field(min_length=8, max_length=64)

@router.get("/users")
def list_system_users(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    role_code: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """多条件分页查询系统用户"""
    query = db.query(SysUser)
    if keyword:
        query = query.filter(
            (SysUser.username.ilike(f"%{keyword}%")) |
            (SysUser.nickname.ilike(f"%{keyword}%")) |
            (SysUser.phone.ilike(f"%{keyword}%"))
        )
    if role_code:
        query = query.filter(SysUser.role_code == role_code)
    if status:
        query = query.filter(SysUser.status == status)

    total = query.count()
    users = query.order_by(SysUser.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()

    # 聚合 profile 与 growth
    user_ids = [u.id for u in users]
    profiles = db.query(UserProfile).filter(UserProfile.user_id.in_(user_ids)).all() if user_ids else []
    growths = db.query(UserGrowth).filter(UserGrowth.user_id.in_(user_ids)).all() if user_ids else []

    prof_map = {p.user_id: p for p in profiles}
    growth_map = {g.user_id: g for g in growths}

    return success_response({
        "list": [{
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "phone": u.phone or "",
            "avatar_url": u.avatar_url or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
            "role_code": u.role_code,
            "grade": u.grade or "",
            "status": u.status,
            "school_name": prof_map.get(u.id).school_name if u.id in prof_map else "",
            "district": prof_map.get(u.id).district if u.id in prof_map else "",
            "energy_value": growth_map.get(u.id).energy_value if u.id in growth_map else 0,
            "level_code": growth_map.get(u.id).level_code if u.id in growth_map else "LV1_APPRENTICE",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
        } for u in users],
        "page": page,
        "pageSize": pageSize,
        "total": total
    })

@router.post("/users")
def create_system_user(
    req: CreateUserDTO,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理员手动创建新用户"""
    exist = db.query(SysUser).filter(SysUser.username == req.username).first()
    if exist:
        return error_response(code=4090, message=f"用户名【{req.username}】已存在")

    new_user = SysUser(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        phone=req.phone,
        role_code=req.role_code,
        grade=req.grade,
        status="ACTIVE",
        avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 建立档案与成长
    db.add(UserProfile(
        user_id=new_user.id,
        school_name=req.school_name,
        district="蓟州区",
        bio=f"由管理员分配至{req.school_name}"
    ))
    db.add(UserGrowth(
        user_id=new_user.id,
        energy_value=100,
        level_code="LV1_APPRENTICE"
    ))
    db.commit()

    return success_response({"id": new_user.id, "username": new_user.username}, message="用户创建成功")

@router.put("/users/{user_id}")
def update_system_user(
    user_id: int,
    req: UpdateUserDTO,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        return error_response(code=4040, message="用户不存在")

    if req.nickname is not None:
        user.nickname = req.nickname
    if req.phone is not None:
        user.phone = req.phone
    if req.role_code is not None:
        user.role_code = req.role_code
    if req.grade is not None:
        user.grade = req.grade

    # 更新 profile
    if req.school_name is not None:
        prof = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if prof:
            prof.school_name = req.school_name
        else:
            db.add(UserProfile(user_id=user_id, school_name=req.school_name))

    db.commit()
    return success_response(message="用户信息已更新")

@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    req: StatusDTO,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """启用或停用用户账号"""
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        return error_response(code=4040, message="用户不存在")
    if user.id == current_user["user_id"]:
        return error_response(code=4003, message="不能禁用当前正在操作的管理员账户自身")

    user.status = req.status
    db.commit()
    msg = "账号已启用" if req.status == "ACTIVE" else "账号已停用，用户将无法登录"
    return success_response({"status": user.status}, message=msg)

@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    req: ResetPwdDTO,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """重置用户密码"""
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        return error_response(code=4040, message="用户不存在")

    user.password_hash = hash_password(req.new_password)
    db.query(AuthSession).filter(AuthSession.user_id == user_id).update(
        {AuthSession.revoked_at: datetime.utcnow()}, synchronize_session=False
    )
    db.commit()
    return success_response(message=f"用户【{user.username}】的密码已重置，现有登录会话已失效")

@router.delete("/users/{user_id}")
def delete_system_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除或注销用户"""
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        return error_response(code=4040, message="用户不存在")
    if user.id == current_user["user_id"]:
        return error_response(code=4003, message="无法注销当前登录的管理员账户")

    db.delete(user)
    db.commit()
    return success_response(message="用户已从系统安全注销删除")

# -----------------------------------------------------------------------------
# 美育助农物资实体流向管理模块
# -----------------------------------------------------------------------------

class CreateSupplyRequest(BaseModel):
    school_name: str
    district: str
    materials_name: str
    quantity: int
    unit: Optional[str] = "套"
    beneficiary_students: Optional[int] = 50
    delivered_date: Optional[str] = None
    batch_no: Optional[str] = None

@router.get("/philanthropy/supplies")
def list_admin_supplies(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """运营后台：查询助农美育物资调拨实体流向明细"""
    supplies = db.query(PhilanthropySupply).order_by(PhilanthropySupply.delivered_date.desc()).all()
    return success_response([{
        "id": s.id,
        "school_name": s.school_name,
        "district": s.district,
        "materials_name": s.materials_name,
        "quantity": s.quantity,
        "unit": s.unit,
        "beneficiary_students": s.beneficiary_students,
        "delivered_date": s.delivered_date,
        "batch_no": s.batch_no,
        "photo_url": s.photo_url,
        "status": s.status,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else ""
    } for s in supplies])

@router.post("/philanthropy/supplies")
def create_admin_supply(
    req: CreateSupplyRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """运营后台：登记新增向乡村小学调拨的美育耗材批次"""
    new_supply = PhilanthropySupply(
        school_name=req.school_name,
        district=req.district,
        materials_name=req.materials_name,
        quantity=req.quantity,
        unit=req.unit or "套",
        beneficiary_students=req.beneficiary_students or 50,
        delivered_date=req.delivered_date or datetime.utcnow().strftime("%Y-%m-%d"),
        batch_no=req.batch_no or f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        status="DELIVERED"
    )
    db.add(new_supply)
    db.commit()
    db.refresh(new_supply)
    return success_response({
        "id": new_supply.id,
        "batch_no": new_supply.batch_no,
        "school_name": new_supply.school_name
    }, message="助农美育物资调拨记录已登记入库")
