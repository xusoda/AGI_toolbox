"""应用配置"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter"
    )
    
    # MinIO 配置
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    # 外部可访问的 MinIO 端点（用于生成 presigned URL，浏览器需要能访问）
    MINIO_EXTERNAL_ENDPOINT: Optional[str] = os.getenv("MINIO_EXTERNAL_ENDPOINT", None)
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "watch-images")
    MINIO_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
    
    # 图片 URL 策略
    IMAGE_URL_MODE: str = os.getenv("IMAGE_URL_MODE", "presign")  # presign 或 cdn
    CDN_BASE_URL: Optional[str] = os.getenv("CDN_BASE_URL", None)
    
    # Presign 过期时间（秒）
    PRESIGN_EXPIRES_SECONDS: int = int(os.getenv("PRESIGN_EXPIRES_SECONDS", "1800"))  # 30分钟
    
    # 是否使用图片代理（当 presigned URL 有问题时使用）
    USE_IMAGE_PROXY: bool = os.getenv("USE_IMAGE_PROXY", "false").lower() == "true"
    
    # API 基础 URL（用于生成代理 URL）
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

