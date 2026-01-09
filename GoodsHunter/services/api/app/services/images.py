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
        """初始化图片服务（延迟连接，避免启动时阻塞）"""
        self.mode = settings.IMAGE_URL_MODE
        self.cdn_base_url = settings.CDN_BASE_URL
        self.minio_client = None
        self.presign_client = None  # 专门用于生成 presigned URL 的客户端
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保客户端已初始化（延迟初始化，避免启动时阻塞）"""
        if self._initialized:
            return
        
        if self.mode == "presign":
            try:
                # 使用内部端点初始化客户端（用于检查 bucket 等操作）
                # 添加超时处理，避免启动时阻塞
                if MinIOClient is not None:
                    internal_client = MinIOClient(
                        endpoint=settings.MINIO_ENDPOINT,
                        access_key=settings.MINIO_ACCESS_KEY,
                        secret_key=settings.MINIO_SECRET_KEY,
                        bucket=settings.MINIO_BUCKET,
                        use_ssl=settings.MINIO_USE_SSL
                    )
                    self.minio_client = internal_client
                    
                    # 如果配置了外部端点，创建专门用于生成 presigned URL 的客户端
                    # 使用外部端点，这样生成的 URL 浏览器可以访问
                    external_endpoint = settings.MINIO_EXTERNAL_ENDPOINT
                    if external_endpoint:
                        try:
                            # 创建一个轻量级的客户端用于生成 presigned URL
                            # 直接使用 minio 库，跳过 bucket 检查（因为可能无法连接）
                            from minio import Minio
                            endpoint_clean = external_endpoint.replace("http://", "").replace("https://", "")
                            minio_client = Minio(
                                endpoint=endpoint_clean,
                                access_key=settings.MINIO_ACCESS_KEY,
                                secret_key=settings.MINIO_SECRET_KEY,
                                secure=settings.MINIO_USE_SSL
                            )
                            
                            # 创建一个包装类，只提供 get_presigned_url 方法
                            class PresignOnlyClient:
                                def __init__(self, client, bucket):
                                    self.client = client
                                    self.bucket = bucket
                                
                                def get_presigned_url(self, key, expires_seconds=3600):
                                    from datetime import timedelta
                                    return self.client.presigned_get_object(
                                        self.bucket,
                                        key,
                                        expires=timedelta(seconds=expires_seconds)
                                    )
                            
                            self.presign_client = PresignOnlyClient(minio_client, settings.MINIO_BUCKET)
                        except Exception as e:
                            # 初始化失败不影响启动，只记录日志
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"[ImageService] 创建外部端点客户端失败: {e}，将使用内部端点")
                            self.presign_client = None
            except Exception as e:
                # MinIO 初始化失败不影响启动，只记录日志
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[ImageService] MinIO 客户端初始化失败: {e}，将使用降级方案")
                self.minio_client = None
        
        self._initialized = True
    
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
        
        # 延迟初始化 MinIO 客户端（避免启动时阻塞）
        self._ensure_initialized()
        
        if self.mode == "cdn" and self.cdn_base_url:
            # CDN 模式：直接拼接 URL
            return f"{self.cdn_base_url.rstrip('/')}/{key}"
        elif self.mode == "presign" and self.minio_client:
            # 如果启用了图片代理，使用代理端点
            if settings.USE_IMAGE_PROXY:
                api_base = settings.API_BASE_URL.rstrip('/')
                return f"{api_base}/api/images/{key}"
            
            # Presign 模式：生成预签名 URL
            try:
                # 优先使用外部端点客户端生成 URL（浏览器可访问）
                client_to_use = self.presign_client if self.presign_client else self.minio_client
                url = client_to_use.get_presigned_url(
                    key,
                    expires_seconds=settings.PRESIGN_EXPIRES_SECONDS
                )
                return url
            except Exception as e:
                print(f"[ImageService] 生成 presign URL 失败: {e}，尝试使用代理端点")
                import traceback
                traceback.print_exc()
                # 降级到代理端点
                api_base = settings.API_BASE_URL.rstrip('/')
                return f"{api_base}/api/images/{key}"
        else:
            # 降级：直接返回 key（可能需要前端处理）
            return key


# 全局实例（延迟初始化，避免启动时阻塞）
_image_service_instance = None

def get_image_service() -> ImageService:
    """获取图片服务实例（延迟初始化）"""
    global _image_service_instance
    if _image_service_instance is None:
        _image_service_instance = ImageService()
    return _image_service_instance

# 为了向后兼容，提供 image_service 属性
# 但注意：只有在实际使用时才会初始化
class ImageServiceProxy:
    """图片服务代理类，延迟初始化"""
    def __getattr__(self, name):
        return getattr(get_image_service(), name)

image_service = ImageServiceProxy()

