"""图片 URL 生成服务"""
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径，以便导入 storage 模块
# services/api/app/services/images.py -> GoodsHunter/
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.settings import settings

# 尝试导入 MinIOClient，如果失败则使用备用实现
try:
    from storage.minio_client import MinIOClient
except ImportError:
    # 如果无法导入，使用 minio 库直接实现
    try:
        from minio import Minio
        from datetime import timedelta
        
        class MinIOClient:
            def __init__(self, endpoint, access_key, secret_key, bucket, use_ssl=False):
                self.bucket = bucket
                endpoint_clean = endpoint.replace("http://", "").replace("https://", "")
                self.client = Minio(
                    endpoint=endpoint_clean,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=use_ssl
                )
            
            def get_presigned_url(self, key, expires_seconds=3600):
                from datetime import timedelta
                return self.client.presigned_get_object(
                    self.bucket,
                    key,
                    expires=timedelta(seconds=expires_seconds)
                )
    except ImportError:
        MinIOClient = None


class ImageService:
    """图片 URL 生成服务"""
    
    def __init__(self):
        """初始化图片服务"""
        self.mode = settings.IMAGE_URL_MODE
        self.cdn_base_url = settings.CDN_BASE_URL
        self.minio_client = None
        
        if self.mode == "presign":
            self.minio_client = MinIOClient(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                bucket=settings.MINIO_BUCKET,
                use_ssl=settings.MINIO_USE_SSL
            )
    
    def get_image_url(self, key: Optional[str]) -> Optional[str]:
        """
        根据 MinIO key 生成可访问的 URL
        
        Args:
            key: MinIO 对象 key
        
        Returns:
            可访问的 URL，如果 key 为空返回 None
        """
        if not key:
            return None
        
        if self.mode == "cdn" and self.cdn_base_url:
            # CDN 模式：直接拼接 URL
            return f"{self.cdn_base_url.rstrip('/')}/{key}"
        elif self.mode == "presign" and self.minio_client:
            # Presign 模式：生成预签名 URL
            try:
                return self.minio_client.get_presigned_url(
                    key,
                    expires_seconds=settings.PRESIGN_EXPIRES_SECONDS
                )
            except Exception as e:
                print(f"[ImageService] 生成 presign URL 失败: {e}")
                return None
        else:
            # 降级：直接返回 key（可能需要前端处理）
            return key


# 全局实例
image_service = ImageService()

