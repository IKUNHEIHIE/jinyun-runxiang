import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "津韵润乡——天津非遗赋能乡村美育智能应用"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Database
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "root123456")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "jinyun_runxiang")
    MYSQL_SOCKET: str = os.getenv("MYSQL_SOCKET", "/tmp/mysql.sock")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Support socket connection if on local Unix machine
        if os.path.exists(self.MYSQL_SOCKET):
            return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@localhost/{self.MYSQL_DB}?unix_socket={self.MYSQL_SOCKET}&charset=utf8mb4"
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jinyun_runxiang_super_secret_key_2026_tianjin_heritage")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

settings = Settings()
