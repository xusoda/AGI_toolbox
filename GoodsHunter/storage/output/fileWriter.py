"""文件写入器：保存图片和文本内容到本地文件"""
import re
import time
import requests
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from crawler.core.types import Record


class FileWriter:
    """文件写入器，负责保存图片和文本内容"""
    
    # 配置缓存
    _config_cache: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def _load_config() -> Dict[str, Any]:
        """加载配置文件"""
        if FileWriter._config_cache is not None:
            return FileWriter._config_cache
        
        config_path = Path(__file__).parent.parent / "config.yaml"
        default_config = {
            "image": {
                "base_dir": "/Users/xushuda/WorkSpace/GoodsHunter/storage/file_storage/image",
                "max_retries": 3
            },
            "text": {
                "base_dir": "/Users/xushuda/WorkSpace/GoodsHunter/storage/file_storage/text"
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    # 合并默认配置
                    image_config = {**default_config.get("image", {}), **config.get("image", {})}
                    text_config = {**default_config.get("text", {}), **config.get("text", {})}
                    FileWriter._config_cache = {
                        "image": image_config,
                        "text": text_config
                    }
                    return FileWriter._config_cache
            except Exception as e:
                print(f"[FileWriter] 加载配置文件失败: {e}，使用默认配置")
        
        FileWriter._config_cache = default_config
        return FileWriter._config_cache
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清理文件名，移除不允许的字符"""
        invalid_chars = '<>:"/\\|?*'
        safe_name = name
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name
    
    @staticmethod
    def _get_site_dir_name(site: str) -> str:
        """获取站点目录名"""
        # 将域名转换为目录名，例如 commit-watch.co.jp -> commit-watch
        site_dir_name = site.split('.')[0] if '.' in site else site
        return FileWriter._sanitize_filename(site_dir_name)
    
    @staticmethod
    def _get_image_extension(image_url: str, image_data: bytes, content_type: Optional[str] = None) -> str:
        """获取图片扩展名"""
        ext = None
        
        # 先尝试从URL中获取
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        if '.' in path:
            ext = path.rsplit('.', 1)[1].lower()
            # 限制扩展名长度，避免异常情况
            if len(ext) > 10:
                ext = None
            # 移除查询参数等
            if '?' in ext:
                ext = ext.split('?')[0]
        
        # 如果没有从URL获取到，尝试从Content-Type获取
        if not ext and content_type:
            if 'image/' in content_type:
                ext = content_type.split('/')[-1].split(';')[0].strip()
                if ext == 'jpeg':
                    ext = 'jpg'
        
        # 如果还是没有扩展名，使用默认扩展名
        if not ext:
            ext = 'jpg'  # 默认使用jpg
        
        # 确保扩展名是常见的图片格式
        valid_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
        if ext not in valid_exts:
            ext = 'jpg'
        
        return ext
    
    @staticmethod
    def save_image(image_data: bytes, item_id: str, site: str, image_url: str = "", base_dir: Optional[str] = None) -> Optional[str]:
        """
        保存图片到本地目录
        
        Args:
            image_data: 图片的二进制数据
            item_id: 商品ID，用作文件名
            site: 站点名称，用作目录名
            image_url: 图片URL（用于获取扩展名）
            base_dir: 基础目录路径，如果为None则从配置文件读取
            
        Returns:
            保存后的文件路径，如果失败则返回None
        """
        if not image_data or len(image_data) == 0 or not item_id or not site:
            return None
        
        try:
            # 加载配置
            config = FileWriter._load_config()
            if base_dir is None:
                base_dir = config.get("image", {}).get("base_dir", "/Users/xushuda/WorkSpace/GoodsHunter/storage/file_storage/image")
            
            # 创建目录路径
            site_dir_name = FileWriter._get_site_dir_name(site)
            site_dir = Path(base_dir) / site_dir_name
            site_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理item_id
            safe_item_id = FileWriter._sanitize_filename(item_id)
            
            # 获取扩展名
            ext = FileWriter._get_image_extension(image_url, image_data)
            
            # 构建文件路径
            filename = f"{safe_item_id}.{ext}"
            file_path = site_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            print(f"[FileWriter] 图片已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"[FileWriter] 保存图片失败: {item_id}, 错误: {str(e)}")
            return None
    
    @staticmethod
    def save_text(text_data: Dict[str, Any], item_id: str, site: str, base_dir: Optional[str] = None) -> Optional[str]:
        """
        保存文本内容到本地文件
        
        Args:
            text_data: 要保存的文本数据字典（字段名 -> 值）
            item_id: 商品ID，用作文件名
            site: 站点名称，用作目录名
            base_dir: 基础目录路径，如果为None则从配置文件读取
            
        Returns:
            保存后的文件路径，如果失败则返回None
        """
        if not text_data or not item_id or not site:
            return None
        
        try:
            # 加载配置
            config = FileWriter._load_config()
            if base_dir is None:
                base_dir = config.get("text", {}).get("base_dir", "/Users/xushuda/WorkSpace/GoodsHunter/storage/file_storage/text")
            
            # 创建目录路径
            site_dir_name = FileWriter._get_site_dir_name(site)
            site_dir = Path(base_dir) / site_dir_name
            site_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理item_id
            safe_item_id = FileWriter._sanitize_filename(item_id)
            
            # 构建文件路径（使用.txt扩展名）
            filename = f"{safe_item_id}.txt"
            file_path = site_dir / filename
            
            # 格式化文本内容
            lines = []
            for key, value in text_data.items():
                if value is not None:
                    # 将值转换为字符串
                    value_str = str(value)
                    # 如果值包含换行符，进行格式化
                    if '\n' in value_str:
                        lines.append(f"{key}:\n{value_str}\n")
                    else:
                        lines.append(f"{key}: {value_str}\n")
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"[FileWriter] 文本已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"[FileWriter] 保存文本失败: {item_id}, 错误: {str(e)}")
            return None
    
    @staticmethod
    def save_record(record: Record, site: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, int]:
        """
        保存记录：包括JSONL格式的数据和图片/文本文件
        
        Args:
            record: Record对象
            site: 站点名称，如果提供则保存图片和文本文件
            output_path: JSONL输出文件路径，如果为None则不保存JSONL
            
        Returns:
            保存统计信息字典，包含 saved_images, saved_texts, saved_jsonl
        """
        stats = {
            "saved_images": 0,
            "saved_texts": 0,
            "saved_jsonl": 0
        }
        
        # 保存JSONL格式数据
        if output_path:
            try:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 将Record转换为可序列化的字典
                record_dict = {
                    "url": record.url,
                    "data": record.data,
                    "errors": [
                        {
                            "field": err.field,
                            "error": err.error,
                            "strategy": err.strategy,
                        }
                        for err in record.errors
                    ],
                }
                
                # 追加写入JSONL格式（每行一个JSON对象）
                with open(output_file, "a", encoding="utf-8") as f:
                    json.dump(record_dict, f, ensure_ascii=False)
                    f.write("\n")
                
                stats["saved_jsonl"] = 1
                print(f"[FileWriter] JSONL已保存: {output_path}")
            except Exception as e:
                print(f"[FileWriter] 保存JSONL失败: {str(e)}")
        
        # 保存图片和文本文件（如果存在）
        if site:
            if "items" in record.data:
                items = record.data["items"]
                print(f"[FileWriter] 开始保存图片和文本文件...")
                
                for item in items:
                    item_id = item.get("item_id")
                    if item_id:
                        # 保存图片
                        image_data = item.get("_image_data")
                        image_url = item.get("_image_url") or item.get("image", "")
                        if image_data:
                            saved_path = FileWriter.save_image(
                                image_data=image_data,
                                item_id=item_id,
                                site=site,
                                image_url=image_url
                            )
                            if saved_path:
                                stats["saved_images"] += 1
                        
                        # 保存文本（排除图片相关字段和内部字段）
                        text_fields = {}
                        for key, value in item.items():
                            # 排除图片数据、内部字段和空值
                            if not key.startswith("_") and key != "image" and value is not None:
                                text_fields[key] = value
                        
                        if text_fields:
                            saved_path = FileWriter.save_text(
                                text_data=text_fields,
                                item_id=item_id,
                                site=site
                            )
                            if saved_path:
                                stats["saved_texts"] += 1
                
                print(f"[FileWriter] 文件保存完成: {stats['saved_images']} 个图片, {stats['saved_texts']} 个文本文件")
        
        return stats

