"""
集中式配置管理，带有验证
"""
from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets
import os
from functools import lru_cache


class Settings(BaseSettings):
    """应用程序设置，带有验证"""

    # 应用程序
    app_name: str = "Education AI Assistant"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = Field(default=False)

    # 安全设置
    secret_key: SecretStr = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 数据库设置
    database_url: str = Field(...)
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")

    # CORS
    cors_origins: List[str] = Field(default_factory=list)

    # 文件上传
    max_upload_size: int = Field(default=10 * 1024 * 1024, le=50 * 1024 * 1024)
    # 最大50MB
    allowed_upload_extensions: List[str] = Field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"]
    )

    # API速率限制
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)
    # 秒

    # LLM配置
    llm_provider: str = Field(default="qwen", pattern="^(deepseek|qwen|openai)$")
    # deepseek已移除，只使用千问
    qwen_api_key: Optional[SecretStr] = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # DashScope API配置（用于嵌入）
    dashscope_api_key: Optional[SecretStr] = None

    # Milvus向量数据库
    milvus_host: str = Field(default="localhost")
    milvus_port: int = Field(default=19530, ge=1, le=65535)
    milvus_collection: str = Field(default="education_knowledge")

    # 监控
    prometheus_enabled: bool = Field(default=True)
    sentry_dsn: Optional[str] = None

    # 日志设置
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_format: str = Field(default="json")
    # JSON或文本

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v):
        if isinstance(v, SecretStr):
            v = v.get_secret_value()

        # 检查弱默认值
        weak_keys = [
            "your-secret-key-here-change-in-production",
            "secret-key",
            "change-me",
            "development"
        ]

        if v.lower() in weak_keys:
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("在生产环境中检测到弱SECRET_KEY！请生成强密钥。")
            else:
                # 为开发环境生成安全密钥
                v = secrets.token_urlsafe(32)

        return SecretStr(v)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v, info):
        environment = info.data.get("environment", "development")

        # 不允许在生产环境中使用SQLite
        if environment == "production" and v.startswith("sqlite"):
            raise ValueError("不允许在生产环境中使用SQLite")

        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v, info):
        environment = info.data.get("environment", "development")

        # 在生产环境中强制debug=False
        if environment == "production" and v:
            return False

        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
        # 允许.env中有额外字段
    }


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的设置实例"""
    return Settings()


def generate_secret_key() -> str:
    """生成加密强度高的密钥"""
    # token_urlsafe(32)生成约43个字符
    return secrets.token_urlsafe(32)


# 工具函数，用于在启动时校验配置
def validate_configuration():
    """验证配置，如果无效则抛出错误"""
    try:
        settings = get_settings()

        # 额外的运行时验证
        if settings.environment == "production":
            # 确保关键的生产设置
            if not settings.sentry_dsn:
                print("警告: 生产环境未配置Sentry DSN")

            if settings.cors_origins == ["*"]:
                raise ValueError("生产环境中CORS不能设置为允许所有来源")

            if not settings.qwen_api_key:
                raise ValueError("必须配置QWEN_API_KEY")

        return settings

    except Exception as e:
        print(f"配置验证失败: {e}")
        raise


# 延迟导出设置实例以避免启动错误
# settings = get_settings()
# 为了方便，创建延迟属性
class LazySettings:
    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_settings()
        return getattr(self._instance, name)

settings = LazySettings()