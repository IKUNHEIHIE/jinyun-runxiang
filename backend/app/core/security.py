import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import SysUser

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("scrypt$"):
        try:
            algorithm, n, r, p, salt, expected = hashed_password.split("$")
            if (algorithm, n, r, p) != ("scrypt", "16384", "8", "1"):
                return False
            actual = hashlib.scrypt(
                plain_password.encode("utf-8"), salt=bytes.fromhex(salt),
                n=16384, r=8, p=1
            )
            return hmac.compare_digest(actual, bytes.fromhex(expected))
        except (ValueError, TypeError):
            return False
    # Compatibility with accounts created by the original SHA-256 implementation.
    legacy_digest = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return len(hashed_password) == 64 and hmac.compare_digest(legacy_digest, hashed_password)


def password_needs_rehash(hashed_password: str) -> bool:
    return not hashed_password.startswith("scrypt$")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None

def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    if not auth or not auth.credentials:
        return None
    payload = decode_token(auth.credentials)
    return _load_active_user(payload, db) if payload else None


def _load_active_user(payload: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        return None
    user = db.query(SysUser).filter(SysUser.id == user_id).first()
    if not user or user.status != "ACTIVE":
        return None
    return {
        **payload,
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role_code": user.role_code,
    }

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(auth.credentials)
    current_user = _load_active_user(payload, db) if payload else None
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效或账号不可用，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_roles(*roles: str):
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role_code")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权访问此资源，需要角色: {','.join(roles)}"
            )
        return current_user
    return role_checker

require_admin = require_roles("ADMIN")
require_teacher = require_roles("TEACHER", "ADMIN")
