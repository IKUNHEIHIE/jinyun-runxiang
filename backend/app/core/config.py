import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    PROJECT_NAME: str = "津韵润乡——天津非遗赋能乡村美育智能应用"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    API_V1_STR: str = "/api/v1"
    
    # Database
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root123456"
    MYSQL_DB: str = "jinyun_runxiang"
    MYSQL_SOCKET: str = "/tmp/mysql.sock"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Support socket connection if on local Unix machine
        if os.path.exists(self.MYSQL_SOCKET):
            return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@localhost/{self.MYSQL_DB}?unix_socket={self.MYSQL_SOCKET}&charset=utf8mb4"
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT
    JWT_SECRET_KEY: str = "jinyun_runxiang_super_secret_key_2026_tianjin_heritage"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

settings = Settings()
