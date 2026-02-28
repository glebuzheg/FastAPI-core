from functools import lru_cache
from typing import Optional, Literal

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    # Application
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment for the application"
    )
    APP_PORT: int = Field(default=8000, description="Port for the application")

    # PostgreSQL
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="fastapi_db", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_POOL_SIZE: int = Field(default=20, description="PostgreSQL connection pool size")
    POSTGRES_MAX_OVERFLOW: int = Field(default=10, description="PostgreSQL max overflow connections")
    POSTGRES_POOL_TIMEOUT: int = Field(default=30, description="PostgreSQL pool timeout")
    POSTGRES_ECHO: bool = Field(default=False, description="Echo PostgreSQL queries")
    POSTGRES_POOL_PRE_PING: bool = Field(default=True, description="Pre-ping PostgreSQL connections")

    # Redis
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, description="Redis max connections")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Redis socket timeout")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Redis socket connect timeout")

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens",
        min_length=32
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")

    @property
    def POSTGRES_DSN(self) -> str:
        """Создание DSN для PostgreSQL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_DSN(self) -> str:
        """Создание DSN для Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str, info):
        """Валидация секретного ключа в production"""
        environment = info.data.get('ENVIRONMENT', 'development')

        if environment == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY должен быть не менее 32 символов в production")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Получение настроек приложения (синглтон)"""
    return Settings()
