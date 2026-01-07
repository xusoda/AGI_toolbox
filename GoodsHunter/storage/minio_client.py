"""MinIO客户端：用于上传和下载图片"""
import os
import hashlib
from typing import Optional, BinaryIO
from pathlib import Path

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    Minio = None
    S3Error = None


class MinIOClient:
    """MinIO客户端封装"""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        use_ssl: bool = False
    ):
        """
        初始化MinIO客户端
        
        Args:
            endpoint: MinIO端点，例如 http://localhost:9000
            access_key: 访问密钥
            secret_key: 秘密密钥
            bucket: 存储桶名称
            use_ssl: 是否使用SSL
        """
        if Minio is None:
            raise ImportError(
                "minio 未安装。请运行: pip install minio"
            )
        
        # 从环境变量读取配置
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.bucket = bucket or os.getenv("MINIO_BUCKET", "watch-images")
        self.use_ssl = use_ssl or (os.getenv("MINIO_USE_SSL", "false").lower() == "true")
        
        # 初始化MinIO客户端
        self.client = Minio(
            endpoint=self.endpoint.replace("http://", "").replace("https://", ""),
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.use_ssl
        )
        
        # 确保bucket存在
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保bucket存在，如果不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"[MinIOClient] 创建bucket: {self.bucket}")
        except S3Error as e:
            print(f"[MinIOClient] 检查bucket失败: {e}")
            raise
    
    def _calculate_sha256(self, data: bytes) -> str:
        """计算数据的SHA256哈希值"""
        return hashlib.sha256(data).hexdigest()
    
    def _get_object_key(self, sha256: str, ext: str, size: Optional[int] = None) -> str:
        """
        根据SHA256生成对象key
        
        Args:
            sha256: SHA256哈希值
            ext: 文件扩展名
            size: 缩略图尺寸（300或600），如果为None则是原图
            
        Returns:
            对象key，格式：original/{sha256[0:2]}/{sha256}.{ext} 或 thumb/{size}/{sha256[0:2]}/{sha256}.webp
        """
        prefix = sha256[:2]
        if size:
            # 缩略图统一使用webp格式
            return f"thumb/{size}/{prefix}/{sha256}.webp"
        else:
            # 原图保留原始格式
            return f"original/{prefix}/{sha256}.{ext}"
    
    def upload_image(
        self,
        image_data: bytes,
        sha256: Optional[str] = None,
        ext: str = "jpg"
    ) -> str:
        """
        上传图片到MinIO
        
        Args:
            image_data: 图片二进制数据
            sha256: SHA256哈希值，如果为None则自动计算
            ext: 文件扩展名
            
        Returns:
            对象key
        """
        if sha256 is None:
            sha256 = self._calculate_sha256(image_data)
        
        key = self._get_object_key(sha256, ext)
        
        try:
            # 检查对象是否已存在
            try:
                self.client.stat_object(self.bucket, key)
                print(f"[MinIOClient] 对象已存在，跳过上传: {key}")
                return key
            except S3Error as e:
                if e.code != "NoSuchKey":
                    raise
            
            # 上传对象
            from io import BytesIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=BytesIO(image_data),
                length=len(image_data),
                content_type=f"image/{ext}" if ext != "jpg" else "image/jpeg"
            )
            print(f"[MinIOClient] 上传成功: {key}")
            return key
            
        except S3Error as e:
            print(f"[MinIOClient] 上传失败: {e}")
            raise
    
    def upload_thumbnail(
        self,
        thumbnail_data: bytes,
        sha256: str,
        size: int
    ) -> str:
        """
        上传缩略图到MinIO
        
        Args:
            thumbnail_data: 缩略图二进制数据
            sha256: 原图的SHA256哈希值
            size: 缩略图尺寸（300或600）
            
        Returns:
            对象key
        """
        key = self._get_object_key(sha256, "webp", size=size)
        
        try:
            # 检查对象是否已存在
            try:
                self.client.stat_object(self.bucket, key)
                print(f"[MinIOClient] 缩略图已存在，跳过上传: {key}")
                return key
            except S3Error as e:
                if e.code != "NoSuchKey":
                    raise
            
            # 上传缩略图
            from io import BytesIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=BytesIO(thumbnail_data),
                length=len(thumbnail_data),
                content_type="image/webp"
            )
            print(f"[MinIOClient] 缩略图上传成功: {key}")
            return key
            
        except S3Error as e:
            print(f"[MinIOClient] 缩略图上传失败: {e}")
            raise
    
    def download_image(self, key: str) -> bytes:
        """
        从MinIO下载图片
        
        Args:
            key: 对象key
            
        Returns:
            图片二进制数据
        """
        try:
            response = self.client.get_object(self.bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"[MinIOClient] 下载失败: {e}")
            raise
    
    def list_objects(self, prefix: Optional[str] = None) -> list:
        """
        列出bucket中的对象
        
        Args:
            prefix: 对象key前缀，例如 "original/" 或 "thumb/300/"
            
        Returns:
            对象列表
        """
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"[MinIOClient] 列出对象失败: {e}")
            return []
    
    def object_exists(self, key: str) -> bool:
        """
        检查对象是否存在
        
        Args:
            key: 对象key
            
        Returns:
            如果存在返回True，否则返回False
        """
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except S3Error:
            return False
    
    def get_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        """
        生成预签名URL
        
        Args:
            key: 对象key
            expires_seconds: 过期时间（秒）
            
        Returns:
            预签名URL
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket,
                key,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
        except S3Error as e:
            print(f"[MinIOClient] 生成预签名URL失败: {e}")
            raise

