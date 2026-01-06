"""Transform处理器：处理字段值的转换"""
import re
import os
import time
import requests
import yaml
from pathlib import Path
from typing import Any, Optional, Dict
from urllib.parse import urljoin, urlparse


class TransformProcessor:
    """Transform处理器"""
    
    # 配置缓存
    _config_cache: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def _load_config() -> Dict[str, Any]:
        """加载配置文件"""
        if TransformProcessor._config_cache is not None:
            return TransformProcessor._config_cache
        
        config_path = Path(__file__).parent.parent / "config.yaml"
        default_config = {
            "image": {
                "base_dir": "/Users/xushuda/WorkSpace/GoodsHunter/storage/file_storage/image",
                "max_retries": 3
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    # 合并默认配置
                    image_config = {**default_config.get("image", {}), **config.get("image", {})}
                    TransformProcessor._config_cache = {"image": image_config}
                    return TransformProcessor._config_cache
            except Exception as e:
                print(f"[TransformProcessor] 加载配置文件失败: {e}，使用默认配置")
        
        TransformProcessor._config_cache = default_config
        return TransformProcessor._config_cache

    @staticmethod
    def apply_transforms(value: Any, transforms: list) -> Any:
        """
        应用一系列transforms
        
        Args:
            value: 原始值
            transforms: TransformSpec列表
            
        Returns:
            转换后的值
        """
        result = value
        for transform in transforms:
            if result is None:
                break
            result = TransformProcessor.apply_transform(result, transform)
        return result

    @staticmethod
    def apply_transform(value: Any, transform) -> Any:
        """
        应用单个transform
        
        Args:
            value: 输入值
            transform: TransformSpec对象
            
        Returns:
            转换后的值
        """
        transform_type = transform.type
        config = transform.config

        if transform_type == "url_join":
            return TransformProcessor.url_join(value, config)
        elif transform_type == "strip":
            return TransformProcessor.strip(value)
        elif transform_type == "regex_capture":
            return TransformProcessor.regex_capture(value, config)
        elif transform_type == "replace":
            return TransformProcessor.replace(value, config)
        elif transform_type == "to_int":
            return TransformProcessor.to_int(value)
        elif transform_type == "pick_best_srcset":
            return TransformProcessor.pick_best_srcset(value)
        else:
            # 未知的transform类型，返回原值
            return value

    @staticmethod
    def url_join(value: Any, config: dict) -> Optional[str]:
        """URL拼接"""
        if not isinstance(value, str) or not value:
            return value
        
        base = config.get("base", "")
        if not base:
            return value
        
        # 如果已经是绝对URL，直接返回
        parsed = urlparse(value)
        if parsed.scheme:
            return value
        
        return urljoin(base, value)

    @staticmethod
    def strip(value: Any) -> Optional[str]:
        """去除首尾空白"""
        if isinstance(value, str):
            return value.strip()
        return value

    @staticmethod
    def regex_capture(value: Any, config: dict) -> Optional[str]:
        """正则表达式捕获"""
        if not isinstance(value, str) or not value:
            return value
        
        pattern = config.get("pattern")
        if not pattern:
            return value
        
        group = config.get("group", 1)
        flags = 0
        if config.get("flags"):
            flag_str = config.get("flags", "")
            if "i" in flag_str or "I" in flag_str:
                flags |= re.IGNORECASE
            if "m" in flag_str or "M" in flag_str:
                flags |= re.MULTILINE
            if "s" in flag_str or "S" in flag_str:
                flags |= re.DOTALL
        
        match = re.search(pattern, value, flags)
        if match:
            if group < len(match.groups()) + 1:
                return match.group(group)
            return match.group(0)
        
        return None

    @staticmethod
    def replace(value: Any, config: dict) -> Optional[str]:
        """字符串替换"""
        if not isinstance(value, str) or not value:
            return value
        
        from_str = config.get("from")
        to_str = config.get("to", "")
        
        if from_str is None:
            return value
        
        return value.replace(from_str, to_str)

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        """转换为整数"""
        if value is None:
            return None
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            # 移除逗号等分隔符
            cleaned = re.sub(r"[,\s]", "", value)
            try:
                return int(cleaned)
            except ValueError:
                return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def pick_best_srcset(value: Any) -> Optional[str]:
        """从srcset中选择最佳图片URL"""
        if not isinstance(value, str) or not value:
            return value
        
        # 如果不是srcset格式，直接返回
        if "," not in value and " " not in value:
            return value
        
        # 解析srcset格式：url1 width1x, url2 width2x, ...
        # 或：url1 width1w, url2 width2w, ...
        candidates = []
        for item in value.split(","):
            item = item.strip()
            parts = item.split()
            if len(parts) >= 1:
                url = parts[0]
                # 尝试提取宽度
                width = 0
                for part in parts[1:]:
                    # 移除x或w后缀
                    num_str = part.rstrip("xw")
                    try:
                        width = max(width, int(num_str))
                    except ValueError:
                        pass
                candidates.append((width, url))
        
        if not candidates:
            return value
        
        # 选择宽度最大的
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    @staticmethod
    def get_image_data(image_url: str, page_resources: Optional[Dict[str, bytes]] = None) -> Optional[bytes]:
        """
        获取图片数据到内存（不写文件）
        
        Args:
            image_url: 图片URL
            page_resources: 页面已加载的资源字典（URL -> 内容），如果图片已加载则直接使用
            
        Returns:
            图片的二进制数据，如果失败则返回None
        """
        if not image_url:
            return None
        
        # 加载配置
        config = TransformProcessor._load_config()
        max_retries = config.get("image", {}).get("max_retries", 3)
        
        try:
            # 尝试从已加载的资源中获取图片
            image_data = None
            if page_resources:
                parsed_url = urlparse(image_url)
                # 尝试精确匹配
                if image_url in page_resources:
                    image_data = page_resources[image_url]
                    print(f"[GetImageData] 从已加载资源中获取图片: {image_url}")
                else:
                    # 尝试匹配URL（去除查询参数和锚点）
                    base_image_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    for resource_url, resource_data in page_resources.items():
                        resource_parsed = urlparse(resource_url)
                        resource_base = f"{resource_parsed.scheme}://{resource_parsed.netloc}{resource_parsed.path}"
                        if base_image_url == resource_base:
                            image_data = resource_data
                            print(f"[GetImageData] 从已加载资源中获取图片（匹配基础URL）: {resource_url}")
                            break
            
            # 如果没有从已加载资源中获取到，则下载图片（带重试）
            if image_data is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                last_error = None
                for attempt in range(1, max_retries + 1):
                    try:
                        print(f"[GetImageData] 尝试下载图片 (第 {attempt}/{max_retries} 次): {image_url}")
                        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
                        response.raise_for_status()
                        
                        # 读取响应内容
                        image_data = b''
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                image_data += chunk
                        
                        print(f"[GetImageData] 图片下载成功，大小: {len(image_data)} 字节")
                        break
                        
                    except Exception as e:
                        last_error = e
                        print(f"[GetImageData] 下载失败 (第 {attempt}/{max_retries} 次): {str(e)}")
                        if attempt < max_retries:
                            # 等待后重试（指数退避）
                            wait_time = 2 ** (attempt - 1)
                            print(f"[GetImageData] 等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                        else:
                            print(f"[GetImageData] 达到最大重试次数，放弃下载")
                            return None
            
            if image_data is None or len(image_data) == 0:
                print(f"[GetImageData] 图片数据为空")
                return None
            
            return image_data
            
        except Exception as e:
            print(f"[GetImageData] 获取图片数据失败: {image_url}, 错误: {str(e)}")
            return None

    @staticmethod
    def save_image(image_url: str, item_id: str, site: str, page_resources: Optional[Dict[str, bytes]] = None, base_dir: Optional[str] = None) -> Optional[str]:
        """
        保存图片到本地目录（已废弃）
        
        注意：此方法已废弃，请使用 output.fileWriter.FileWriter.save_image() 代替。
        此方法保留仅用于向后兼容。
        
        Args:
            image_url: 图片URL
            item_id: 商品ID，用作文件名
            site: 站点名称，用作目录名
            page_resources: 页面已加载的资源字典（URL -> 内容），如果图片已加载则直接使用
            base_dir: 基础目录路径，如果为None则从配置文件读取
            
        Returns:
            保存后的文件路径，如果失败则返回None
        """
        if not image_url or not item_id or not site:
            return None
        
        # 加载配置
        config = TransformProcessor._load_config()
        if base_dir is None:
            base_dir = config.get("image", {}).get("base_dir", "/Users/xushuda/WorkSpace/GoodsHunter/storage/file_storage/image")
        max_retries = config.get("image", {}).get("max_retries", 3)
        
        try:
            # 清理站点名称，移除不允许的字符
            # 将域名转换为目录名，例如 commit-watch.co.jp -> commit-watch
            site_dir_name = site.split('.')[0] if '.' in site else site
            # 移除不允许的字符（Windows和Unix都不允许的字符）
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                site_dir_name = site_dir_name.replace(char, '_')
            
            # 创建目录路径
            site_dir = Path(base_dir) / site_dir_name
            site_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理item_id，移除不允许的字符
            safe_item_id = item_id
            for char in invalid_chars:
                safe_item_id = safe_item_id.replace(char, '_')
            
            # 先尝试从URL中获取文件扩展名
            parsed_url = urlparse(image_url)
            path = parsed_url.path
            ext = None
            if '.' in path:
                ext = path.rsplit('.', 1)[1].lower()
                # 限制扩展名长度，避免异常情况
                if len(ext) > 10:
                    ext = None
                # 移除查询参数等
                if '?' in ext:
                    ext = ext.split('?')[0]
            
            # 尝试从已加载的资源中获取图片
            image_data = None
            if page_resources:
                # 尝试精确匹配
                if image_url in page_resources:
                    image_data = page_resources[image_url]
                    print(f"[SaveImage] 从已加载资源中获取图片: {image_url}")
                else:
                    # 尝试匹配URL（去除查询参数和锚点）
                    base_image_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    for resource_url, resource_data in page_resources.items():
                        resource_parsed = urlparse(resource_url)
                        resource_base = f"{resource_parsed.scheme}://{resource_parsed.netloc}{resource_parsed.path}"
                        if base_image_url == resource_base:
                            image_data = resource_data
                            print(f"[SaveImage] 从已加载资源中获取图片（匹配基础URL）: {resource_url}")
                            break
            
            # 如果没有从已加载资源中获取到，则下载图片（带重试）
            if image_data is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                last_error = None
                for attempt in range(1, max_retries + 1):
                    try:
                        print(f"[SaveImage] 尝试下载图片 (第 {attempt}/{max_retries} 次): {image_url}")
                        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
                        response.raise_for_status()
                        
                        # 如果没有从URL获取到扩展名，尝试从响应头获取Content-Type
                        if not ext:
                            content_type = response.headers.get('Content-Type', '')
                            if 'image/' in content_type:
                                # 从 Content-Type 提取扩展名，例如 image/jpeg -> jpeg
                                ext = content_type.split('/')[-1].split(';')[0].strip()
                                if ext == 'jpeg':
                                    ext = 'jpg'
                        
                        # 读取响应内容
                        image_data = b''
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                image_data += chunk
                        
                        print(f"[SaveImage] 图片下载成功，大小: {len(image_data)} 字节")
                        break
                        
                    except Exception as e:
                        last_error = e
                        print(f"[SaveImage] 下载失败 (第 {attempt}/{max_retries} 次): {str(e)}")
                        if attempt < max_retries:
                            # 等待后重试（指数退避）
                            wait_time = 2 ** (attempt - 1)
                            print(f"[SaveImage] 等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                        else:
                            print(f"[SaveImage] 达到最大重试次数，放弃下载")
                            raise last_error
            
            if image_data is None or len(image_data) == 0:
                print(f"[SaveImage] 图片数据为空")
                return None
            
            # 如果还是没有扩展名，使用默认扩展名
            if not ext:
                ext = 'jpg'  # 默认使用jpg
            
            # 确保扩展名是常见的图片格式
            valid_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
            if ext not in valid_exts:
                ext = 'jpg'
            
            # 构建文件路径
            filename = f"{safe_item_id}.{ext}"
            file_path = site_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            print(f"[SaveImage] 图片已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"[SaveImage] 保存图片失败: {image_url} -> {item_id}, 错误: {str(e)}")
            return None

