import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import SysUser

security_scheme = HTTPBearer(auto_error=False)
PASSWORD_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith("pbkdf2_sha256$"):
            _, rounds, salt, expected = hashed_password.split("$")
            if not 100_000 <= int(rounds) <= 2_000_000:
                return False
            digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), int(rounds))
            return hmac.compare_digest(digest.hex(), expected)
        # Existing SHA256 accounts migrate on their next successful login.
        return len(hashed_password) == 64 and hmac.compare_digest(
            hashlib.sha256(plain_password.encode()).hexdigest(), hashed_password
        )
    except (ValueError, TypeError, AttributeError):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({"iat": now, "exp": now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))})
    payload.setdefault("token_version", 0)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
                          options={"require": ["exp", "iat", "sub", "token_version"]})
    except jwt.InvalidTokenError:
        return None


def authenticated_user(auth: Optional[HTTPAuthorizationCredentials], db: Session) -> Optional[dict]:
    if not auth or not auth.credentials:
        return None
    payload = decode_token(auth.credentials)
    if not payload:
        return None
    try:
        user_id = int(payload["sub"])
        if payload.get("user_id") != user_id:
            return None
        user = db.get(SysUser, user_id)
        if (not user or user.status != "ACTIVE"
                or payload["token_version"] != user.token_version
                or payload.get("role_code") != user.role_code):
            return None
        return {"sub": str(user.id), "user_id": user.id, "username": user.username,
                "role_code": user.role_code, "nickname": user.nickname,
                "token_version": user.token_version}
    except (ValueError, KeyError, TypeError):
        return None


def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    return authenticated_user(auth, db)


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> dict:
    user = authenticated_user(auth, db)
    if user is None:
        raise HTTPException(401, "请先登录或重新登录", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_roles(*roles: str):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role_code"] not in roles:
            raise HTTPException(403, "无权访问此资源")
        return current_user
    return role_checker


require_admin = require_roles("ADMIN")
require_teacher = require_roles("TEACHER", "ADMIN")
