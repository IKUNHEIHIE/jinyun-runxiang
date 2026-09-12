from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password, create_access_token,
    get_current_user
)
from app.schemas.common import success_response, error_response
from app.models.entities import SysUser, UserProfile, UserGrowth, Badge, UserBadge

router = APIRouter(prefix="/auth", tags=["认证与授权"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str
    role_code: Optional[str] = "STUDENT"
    grade: Optional[str] = "小学三年级"

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SysUser).filter(SysUser.username == req.username).first()
    if not user:
        return error_response(code=4010, message="用户不存在或密码错误")
    
    if not verify_password(req.password, user.password_hash):
        return error_response(code=4010, message="用户不存在或密码错误")
    
    if user.status != "ACTIVE":
        return error_response(code=4030, message="账号已被禁用，请联系管理员")
        
    growth = db.query(UserGrowth).filter(UserGrowth.user_id == user.id).first()
    energy = growth.energy_value if growth else 0
    level = growth.level_code if growth else "LV1_APPRENTICE"

    token_payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "username": user.username,
        "role_code": user.role_code,
        "nickname": user.nickname
    }
    access_token = create_access_token(token_payload)

    return success_response({
        "token": access_token,
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
        avatar_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
        status="ACTIVE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 建立默认画像与成长主表
    db.add(UserProfile(user_id=new_user.id, bio="热爱天津非遗的美育小学徒"))
    db.add(UserGrowth(user_id=new_user.id, energy_value=100, level_code="LV1_APPRENTICE"))
    db.commit()

    token_payload = {
        "sub": str(new_user.id),
        "user_id": new_user.id,
        "username": new_user.username,
        "role_code": new_user.role_code,
        "nickname": new_user.nickname
    }
    access_token = create_access_token(token_payload)

    return success_response({
        "token": access_token,
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "nickname": new_user.nickname,
            "role_code": new_user.role_code,
            "energy_value": 100,
            "level_code": "LV1_APPRENTICE"
        }
    }, message="注册成功")

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
