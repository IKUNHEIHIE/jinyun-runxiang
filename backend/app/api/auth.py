from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import hmac
import uuid

from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password, password_needs_rehash, create_access_token,
    get_current_user, decode_token
)
from app.schemas.common import success_response, error_response
from app.models.entities import SysUser, AuthSession, UserProfile, UserGrowth, Badge, UserBadge

router = APIRouter(prefix="/auth", tags=["认证与授权"])

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


REFRESH_TOKEN_LIFETIME = timedelta(days=7)


def _issue_session_tokens(user: SysUser, db: Session):
    session_id = str(uuid.uuid4())
    refresh_token = create_access_token({
        "sub": str(user.id), "user_id": user.id, "sid": session_id, "typ": "refresh"
    }, expires_delta=REFRESH_TOKEN_LIFETIME)
    db.add(AuthSession(
        session_id=session_id,
        user_id=user.id,
        refresh_hash=hashlib.sha256(refresh_token.encode("utf-8")).hexdigest(),
        expires_at=datetime.utcnow() + REFRESH_TOKEN_LIFETIME
    ))
    db.commit()
    access_token = create_access_token({
        "sub": str(user.id), "user_id": user.id, "username": user.username,
        "role_code": user.role_code, "nickname": user.nickname, "sid": session_id
    })
    return access_token, refresh_token

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, description="用户名(3-32位)")
    password: str = Field(..., min_length=6, max_length=64, description="密码(至少6位)")
    nickname: str = Field(..., min_length=1, max_length=32, description="用户昵称")
    role_code: Optional[str] = "STUDENT"
    grade: Optional[str] = "小学三年级"


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nickname: Optional[str] = Field(default=None, min_length=1, max_length=32)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    grade: Optional[str] = Field(default=None, max_length=32)
    school_name: Optional[str] = Field(default=None, max_length=128)
    district: Optional[str] = Field(default=None, max_length=64)
    bio: Optional[str] = Field(default=None, max_length=255)
    avatar_config: Optional[dict] = None

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SysUser).filter(SysUser.username == req.username).first()
    if not user:
        return error_response(code=4010, message="用户不存在或密码错误")
    
    if not verify_password(req.password, user.password_hash):
        return error_response(code=4010, message="用户不存在或密码错误")
    
    if user.status != "ACTIVE":
        return error_response(code=4030, message="账号已被禁用，请联系管理员")

    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(req.password)
        db.commit()
        
    growth = db.query(UserGrowth).filter(UserGrowth.user_id == user.id).first()
    energy = growth.energy_value if growth else 0
    level = growth.level_code if growth else "LV1_APPRENTICE"

    access_token, refresh_token = _issue_session_tokens(user, db)

    return success_response({
        "token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "role_code": user.role_code,
            "grade": user.grade,
            "energy_value": energy,
            "level_code": level
        }
    }, message="登录成功")

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(SysUser).filter(SysUser.username == req.username).first()
    if existing:
        return error_response(code=4090, message="用户名已存在")
        
    # 限制开放注册角色仅限普通学员，防范越权提权漏洞 (CWE-269)
    role = "STUDENT"
    new_user = SysUser(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        role_code=role,
        grade=req.grade,
        avatar_url="/static/images/default_avatar.svg",
        status="ACTIVE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 建立默认画像与成长主表
    db.add(UserProfile(user_id=new_user.id, bio="热爱天津非遗的美育小学徒"))
    db.add(UserGrowth(user_id=new_user.id, energy_value=100, level_code="LV1_APPRENTICE"))
    db.commit()

    access_token, refresh_token = _issue_session_tokens(new_user, db)

    return success_response({
        "token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "nickname": new_user.nickname,
            "role_code": new_user.role_code,
            "energy_value": 100,
            "level_code": "LV1_APPRENTICE"
        }
    }, message="注册成功")


@router.post("/refresh")
def refresh_login(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("typ") != "refresh":
        return error_response(code=4010, message="刷新令牌无效或已过期")
    user_id, session_id = payload.get("user_id"), payload.get("sid")
    if not isinstance(user_id, int) or not isinstance(session_id, str):
        return error_response(code=4010, message="刷新令牌无效")
    session = db.query(AuthSession).filter(
        AuthSession.session_id == session_id,
        AuthSession.user_id == user_id
    ).with_for_update().first()
    if (not session or session.revoked_at or session.expires_at <= datetime.utcnow()
            or not hmac.compare_digest(
                session.refresh_hash, hashlib.sha256(req.refresh_token.encode("utf-8")).hexdigest()
            )):
        return error_response(code=4010, message="刷新令牌已失效，请重新登录")
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user or user.status != "ACTIVE":
        return error_response(code=4030, message="账号不可用")
    new_refresh = create_access_token({
        "sub": str(user.id), "user_id": user.id, "sid": session_id, "typ": "refresh"
    }, expires_delta=REFRESH_TOKEN_LIFETIME)
    session.refresh_hash = hashlib.sha256(new_refresh.encode("utf-8")).hexdigest()
    session.expires_at = datetime.utcnow() + REFRESH_TOKEN_LIFETIME
    db.commit()
    access_token = create_access_token({
        "sub": str(user.id), "user_id": user.id, "username": user.username,
        "role_code": user.role_code, "nickname": user.nickname, "sid": session_id
    })
    return success_response({
        "token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }, message="令牌已刷新")


@router.post("/logout")
def logout(user_dict: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    session_id = user_dict.get("sid")
    if not session_id:
        return error_response(code=4000, message="旧版令牌没有会话记录，请重新登录后再退出")
    session = db.query(AuthSession).filter(
        AuthSession.session_id == session_id,
        AuthSession.user_id == user_dict["user_id"]
    ).with_for_update().first()
    if not session:
        return error_response(code=4010, message="会话不存在")
    session.revoked_at = datetime.utcnow()
    db.commit()
    return success_response(message="已退出登录")

@router.get("/me")
def get_me(user_dict: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user_dict["user_id"]
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user:
        return error_response(code=4040, message="用户不存在")
    
    growth = db.query(UserGrowth).filter(UserGrowth.user_id == user.id).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    badges = db.query(Badge).join(UserBadge, UserBadge.badge_id == Badge.id).filter(UserBadge.user_id == user.id).all()

    return success_response({
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "role_code": user.role_code,
        "grade": user.grade,
        "school_name": profile.school_name if profile else "",
        "district": profile.district if profile else "",
        "bio": profile.bio if profile else "",
        "avatar_config": profile.avatar_config_json if profile else {},
        "energy_value": growth.energy_value if growth else 0,
        "level_code": growth.level_code if growth else "LV1_APPRENTICE",
        "badges": [{
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "icon_url": b.icon_url
        } for b in badges]
    })

@router.get("/permissions")
def get_permissions(user_dict: dict = Depends(get_current_user)):
    role = user_dict.get("role_code", "STUDENT")
    if role == "ADMIN":
        perms = ["admin:dashboard", "admin:content", "admin:models", "admin:users", "admin:community", "admin:activity", "admin:mall", "admin:stats"]
    elif role == "TEACHER":
        perms = ["teacher:workspace", "teacher:lesson_plan", "teacher:assignment", "teacher:analytics", "teacher:live_class"]
    else:
        perms = ["student:course", "student:ai_workshop", "student:community", "student:profile", "student:checkin"]
    return success_response({"role": role, "permissions": perms})


@router.put("/me")
def update_me(
    req: UpdateProfileRequest,
    user_dict: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(SysUser).filter(SysUser.id == user_dict["user_id"]).first()
    if not user or user.status != "ACTIVE":
        return error_response(code=4040, message="用户不存在或已停用")

    updates = req.model_dump(exclude_unset=True, exclude_none=True)
    for field in ("nickname", "avatar_url", "grade"):
        if field in updates:
            setattr(user, field, updates[field])

    profile_fields = {"school_name", "district", "bio", "avatar_config"}
    if profile_fields.intersection(updates):
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        for field in ("school_name", "district", "bio"):
            if field in updates:
                setattr(profile, field, updates[field])
        if "avatar_config" in updates:
            profile.avatar_config_json = updates["avatar_config"]

    db.commit()
    return success_response({
        "id": user.id,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "grade": user.grade
    }, message="个人资料已更新")
