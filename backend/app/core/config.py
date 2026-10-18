import os
from pydantic import Field, field_validator
from sqlalchemy.engine import URL
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
    DATABASE_URL: str = ""
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "jinyun_runxiang"
    MYSQL_SOCKET: str = "/tmp/mysql.sock"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        query = {"charset": "utf8mb4"}
        if self.MYSQL_SOCKET and os.path.exists(self.MYSQL_SOCKET):
            query["unix_socket"] = self.MYSQL_SOCKET
        return URL.create(
            "mysql+pymysql", username=self.MYSQL_USER, password=self.MYSQL_PASSWORD,
            host=self.MYSQL_HOST, port=self.MYSQL_PORT, database=self.MYSQL_DB,
            query=query,
        ).render_as_string(hide_password=False)

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if value.startswith(("jinyun_runxiang_super_secret", "CHANGE_ME")) or len(set(value)) < 8:
            raise ValueError("JWT_SECRET_KEY 必须设置为至少32位的随机密钥")
        return value

settings = Settings()
