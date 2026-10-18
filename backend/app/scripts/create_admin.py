"""Create an administrator after applying the schema, without a shared password."""
import getpass

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.entities import SysUser, UserProfile, UserGrowth


def main():
    username = input("管理员用户名（3至32位）: ").strip()
    password = getpass.getpass("管理员密码（至少12位）: ")
    if not 3 <= len(username) <= 32 or not 12 <= len(password) <= 128:
        raise SystemExit("用户名或密码长度不符合要求")
    if password != getpass.getpass("再次输入密码: "):
        raise SystemExit("两次密码不一致")
    with SessionLocal() as db:
        if db.query(SysUser).filter(SysUser.username == username).first():
            raise SystemExit("用户名已存在")
        user = SysUser(username=username, nickname="管理员", password_hash=hash_password(password),
                       role_code="ADMIN", status="ACTIVE", token_version=0)
        db.add(user)
        db.flush()
        db.add_all([UserProfile(user_id=user.id), UserGrowth(user_id=user.id, energy_value=0)])
        db.commit()
    print("管理员已创建，请使用个人凭据登录。")


if __name__ == "__main__":
    main()
