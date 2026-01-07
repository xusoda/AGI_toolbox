"""数据库写入器：将抓取的数据写入Postgres数据库"""
import os
import json
import hashlib
import requests
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
from pathlib import Path
from io import BytesIO

try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2.pool import SimpleConnectionPool
except ImportError:
    psycopg2 = None
    execute_values = None
    SimpleConnectionPool = None

try:
    from PIL import Image
except ImportError:
    Image = None

# 导入MinIOClient
try:
    from storage.minio_client import MinIOClient
except ImportError:
    MinIOClient = None

from crawler.core.types import Record


class DBWriter:
    """数据库写入器，负责将抓取的数据写入Postgres数据库"""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        enable_image_upload: bool = True
    ):
        """
        初始化数据库写入器
        
        Args:
            database_url: 数据库连接URL，格式：postgresql://user:password@host:port/dbname
                         如果为None，则从环境变量DATABASE_URL读取
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            enable_image_upload: 是否启用图片上传到MinIO（默认True）
        """
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 未安装。请运行: pip install psycopg2-binary"
            )
        
        # 获取数据库连接URL
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError(
                    "未提供database_url且环境变量DATABASE_URL未设置"
                )
        
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.enable_image_upload = enable_image_upload
        self._pool: Optional[SimpleConnectionPool] = None
        
        # 初始化MinIO客户端（如果启用图片上传）
        self.minio_client = None
        if self.enable_image_upload:
            if MinIOClient is None:
                print("[DBWriter] 警告: MinIOClient未导入，图片上传功能将被禁用")
                self.enable_image_upload = False
            else:
                try:
                    self.minio_client = MinIOClient()
                    print("[DBWriter] MinIO客户端已初始化")
                except Exception as e:
                    print(f"[DBWriter] 警告: MinIO客户端初始化失败: {e}，图片上传功能将被禁用")
                    self.enable_image_upload = False
    
    def _get_pool(self) -> SimpleConnectionPool:
        """获取或创建连接池"""
        if self._pool is None:
            self._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=self.pool_size + self.max_overflow,
                dsn=self.database_url
            )
        return self._pool
    
    def _get_connection(self):
        """从连接池获取连接"""
        pool = self._get_pool()
        return pool.getconn()
    
    def _return_connection(self, conn):
        """归还连接到连接池"""
        pool = self._get_pool()
        pool.putconn(conn)
    
    def _extract_site_from_url(self, url: str) -> str:
        """从URL中提取站点域名"""
        try:
            parsed = urlparse(url)
            # 获取主域名，例如 commit-watch.co.jp
            hostname = parsed.netloc or parsed.path.split('/')[0]
            # 移除端口号
            if ':' in hostname:
                hostname = hostname.split(':')[0]
            return hostname
        except Exception:
            return "unknown"
    
    def _get_image_extension(self, image_url: str, image_data: Optional[bytes] = None) -> str:
        """
        获取图片扩展名
        
        Args:
            image_url: 图片URL
            image_data: 图片数据（可选）
            
        Returns:
            扩展名（jpg, png, webp等）
        """
        ext = None
        
        # 从URL获取扩展名
        if image_url:
            parsed = urlparse(image_url)
            path = parsed.path
            if '.' in path:
                ext = path.rsplit('.', 1)[1].lower()
                if len(ext) > 10:
                    ext = None
                if '?' in ext:
                    ext = ext.split('?')[0]
        
        # 从图片数据获取扩展名（如果PIL可用）
        if not ext and image_data and Image:
            try:
                img = Image.open(BytesIO(image_data))
                ext = img.format.lower() if img.format else None
                if ext == 'jpeg':
                    ext = 'jpg'
            except Exception:
                pass
        
        # 默认扩展名
        if not ext:
            ext = 'jpg'
        
        # 确保是有效的图片格式
        valid_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
        if ext not in valid_exts:
            ext = 'jpg'
        
        return ext
    
    def _download_image(self, image_url: str, max_size: int = 10 * 1024 * 1024) -> Optional[bytes]:
        """
        从URL下载图片
        
        Args:
            image_url: 图片URL
            max_size: 最大文件大小（字节），默认10MB
            
        Returns:
            图片二进制数据，失败返回None
        """
        if not image_url:
            return None
        
        try:
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 检查Content-Type
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                print(f"[DBWriter] 警告: URL返回的不是图片类型: {content_type}")
                return None
            
            # 检查文件大小
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > max_size:
                print(f"[DBWriter] 警告: 图片太大，跳过下载: {content_length} bytes")
                return None
            
            # 下载数据
            image_data = response.content
            if len(image_data) > max_size:
                print(f"[DBWriter] 警告: 图片太大，跳过下载: {len(image_data)} bytes")
                return None
            
            return image_data
            
        except Exception as e:
            print(f"[DBWriter] 下载图片失败 {image_url}: {e}")
            return None
    
    def _generate_thumbnail(self, image_data: bytes, size: int, quality: int = 85) -> Optional[bytes]:
        """
        生成缩略图
        
        Args:
            image_data: 原图二进制数据
            size: 目标尺寸（宽度，高度按比例）
            quality: JPEG/WebP质量（1-100）
            
        Returns:
            缩略图二进制数据（WebP格式），失败返回None
        """
        if Image is None:
            print("[DBWriter] 警告: PIL/Pillow未安装，无法生成缩略图")
            return None
        
        try:
            # 打开图片
            img = Image.open(BytesIO(image_data))
            
            # 转换为RGB（如果是RGBA或其他格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 计算新尺寸（保持宽高比）
            width, height = img.size
            if width > height:
                new_width = size
                new_height = int(height * size / width)
            else:
                new_height = size
                new_width = int(width * size / height)
            
            # 生成缩略图
            img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为WebP格式
            output = BytesIO()
            img.save(output, format='WEBP', quality=quality, method=6)
            output.seek(0)
            
            return output.read()
            
        except Exception as e:
            print(f"[DBWriter] 生成缩略图失败: {e}")
            return None
    
    def _process_image(
        self,
        item: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        处理图片：下载、计算SHA256、生成缩略图、上传MinIO
        
        Args:
            item: item数据字典，可能包含_image_data或image字段
            
        Returns:
            (image_original_key, image_thumb_300_key, image_thumb_600_key, image_sha256)
            如果处理失败，返回(None, None, None, None)
        """
        if not self.enable_image_upload or not self.minio_client:
            return None, None, None, None
        
        # 获取图片数据
        image_data = item.get("_image_data")
        image_url = item.get("image") or item.get("_image_url") or ""
        
        # 如果没有图片数据，尝试从URL下载
        if not image_data and image_url:
            image_data = self._download_image(image_url)
        
        if not image_data:
            return None, None, None, None
        
        try:
            # 计算SHA256
            sha256 = hashlib.sha256(image_data).hexdigest()
            
            # 获取扩展名
            ext = self._get_image_extension(image_url, image_data)
            
            # 上传原图
            try:
                original_key = self.minio_client.upload_image(
                    image_data=image_data,
                    sha256=sha256,
                    ext=ext
                )
            except Exception as e:
                print(f"[DBWriter] 上传原图失败: {e}")
                original_key = None
            
            # 生成并上传缩略图
            thumb_300_key = None
            thumb_600_key = None
            
            # 生成300px缩略图
            thumb_300_data = self._generate_thumbnail(image_data, 300)
            if thumb_300_data:
                try:
                    thumb_300_key = self.minio_client.upload_thumbnail(
                        thumbnail_data=thumb_300_data,
                        sha256=sha256,
                        size=300
                    )
                except Exception as e:
                    print(f"[DBWriter] 上传300px缩略图失败: {e}")
            
            # 生成600px缩略图
            thumb_600_data = self._generate_thumbnail(image_data, 600)
            if thumb_600_data:
                try:
                    thumb_600_key = self.minio_client.upload_thumbnail(
                        thumbnail_data=thumb_600_data,
                        sha256=sha256,
                        size=600
                    )
                except Exception as e:
                    print(f"[DBWriter] 上传600px缩略图失败: {e}")
            
            return original_key, thumb_300_key, thumb_600_key, sha256
            
        except Exception as e:
            print(f"[DBWriter] 处理图片失败: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None
    
    def _normalize_item_data(self, item: Dict[str, Any], site: str) -> Dict[str, Any]:
        """
        规范化item数据，提取所需字段
        
        Args:
            item: 原始item数据
            site: 站点名称
            
        Returns:
            规范化后的数据字典
        """
        # 提取字段（兼容不同的字段名）
        item_id = item.get("item_id") or item.get("id") or ""
        brand_name = item.get("brand_name") or None
        model_name = item.get("model_name") or None
        model_no = item.get("model_no") or item.get("model") or None
        price = item.get("price_jpy") or item.get("price") or None
        currency = item.get("currency") or "JPY"
        
        # 处理价格：如果是字符串，尝试转换为整数
        if price is not None:
            if isinstance(price, str):
                # 移除逗号和其他非数字字符
                price_str = price.replace(",", "").replace("¥", "").strip()
                try:
                    price = int(float(price_str))
                except (ValueError, TypeError):
                    price = None
            elif isinstance(price, (int, float)):
                price = int(price)
            else:
                price = None
        
        # 确定category（可以根据site或其他字段判断，这里先设为"watch"）
        category = item.get("category") or "watch"
        
        return {
            "item_id": item_id,
            "brand_name": brand_name,
            "model_name": model_name,
            "model_no": model_no,
            "price": price,
            "currency": currency,
            "category": category,
            "site": site,
            "raw_item": item  # 保留原始item数据用于raw_json
        }
    
    def write_record(self, record: Record, site: Optional[str] = None, run_id: int = -1) -> int:
        """
        写入单条记录到数据库
        
        Args:
            record: Record对象
            site: 站点名称，如果为None则从record.url提取
            run_id: 关联一次crawl run，手动调用时默认为-1
            
        Returns:
            成功写入的记录数
        """
        if not record:
            return 0
        
        # 确定站点名称
        if site is None:
            site = self._extract_site_from_url(record.url)
        
        # 处理items列表
        items = []
        if "items" in record.data:
            items = record.data["items"]
        else:
            # 如果没有items，将整个data作为一个item处理
            items = [record.data]
        
        if not items:
            print(f"[DBWriter] 警告: 记录中没有items数据，跳过写入")
            return 0
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            inserted_count = 0
            crawl_time = datetime.now()
            crawl_date = date.today()
            
            for item in items:
                # 规范化数据
                normalized = self._normalize_item_data(item, site)
                
                # 处理图片（上传到MinIO）
                image_original_key, image_thumb_300_key, image_thumb_600_key, image_sha256 = \
                    self._process_image(item)
                
                # 构建raw_json（包含原始item数据，但排除图片二进制数据）
                raw_item = normalized["raw_item"].copy()
                # 移除图片二进制数据，避免JSON过大
                if "_image_data" in raw_item:
                    raw_item["_image_data"] = f"<binary data, {len(raw_item['_image_data'])} bytes>"
                raw_json = json.dumps(raw_item, ensure_ascii=False, default=str)
                
                # 生成新字段
                # source_uid: {site}:{item_id}
                source_uid = f"{normalized['site']}:{normalized['item_id']}"
                
                # raw_hash: raw_json的SHA256哈希值
                raw_hash = hashlib.sha256(raw_json.encode('utf-8')).hexdigest()
                
                # status: 默认'success'，如果有错误可以设置为'failed'
                status = 'success'
                error = None
                if record.errors:
                    # 如果有错误，可以设置为failed（但这里先保持success，因为可能只是部分字段提取失败）
                    # 如果需要更严格的错误处理，可以根据业务逻辑调整
                    pass
                
                # http_status: 从record.status_code获取
                http_status = record.status_code
                
                # fetch_url: 实际抓取的URL
                fetch_url = record.url
                
                # 插入数据
                insert_sql = """
                    INSERT INTO crawler_log (
                        category, site, item_id, raw_json,
                        brand_name, model_name, model_no,
                        currency, price,
                        image_original_key, image_thumb_300_key, image_thumb_600_key, image_sha256,
                        source_uid, raw_hash, status, error, http_status, fetch_url, run_id,
                        crawl_time, dt
                    ) VALUES (
                        %s, %s, %s, %s::jsonb,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    )
                """
                
                cursor.execute(insert_sql, (
                    normalized["category"],
                    normalized["site"],
                    normalized["item_id"],
                    raw_json,
                    normalized["brand_name"],
                    normalized["model_name"],
                    normalized["model_no"],
                    normalized["currency"],
                    normalized["price"],
                    image_original_key,
                    image_thumb_300_key,
                    image_thumb_600_key,
                    image_sha256,
                    source_uid,
                    raw_hash,
                    status,
                    error,
                    http_status,
                    fetch_url,
                    run_id,
                    crawl_time,
                    crawl_date
                ))
                
                inserted_count += 1
            
            conn.commit()
            print(f"[DBWriter] 成功写入 {inserted_count} 条记录到数据库")
            return inserted_count
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[DBWriter] 写入数据库失败: {str(e)}")
            raise
        finally:
            if conn:
                cursor.close()
                self._return_connection(conn)
    
    def write_records(self, records: List[Record], site: Optional[str] = None, run_id: int = -1) -> int:
        """
        批量写入记录到数据库
        
        Args:
            records: Record对象列表
            site: 站点名称，如果为None则从record.url提取
            run_id: 关联一次crawl run，手动调用时默认为-1
            
        Returns:
            成功写入的记录总数
        """
        total_count = 0
        for record in records:
            count = self.write_record(record, site, run_id)
            total_count += count
        return total_count
    
    def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.closeall()
            self._pool = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

