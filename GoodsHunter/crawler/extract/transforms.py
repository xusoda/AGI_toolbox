"""Transform处理器：处理字段值的转换"""
import re
import os
import time
import requests
import yaml
import sys
from pathlib import Path
from typing import Any, Optional, Dict
from urllib.parse import urljoin, urlparse

# 导入 i18n 模块的 Normalizer
# 从 crawler/extract/transforms.py 到 GoodsHunter 根目录
_goodshunter_root = Path(__file__).parent.parent.parent
if str(_goodshunter_root) not in sys.path:
    sys.path.insert(0, str(_goodshunter_root))
try:
    from i18n.translation.normalizer import Normalizer
except ImportError:
    # 如果导入失败，定义一个简单的规范化函数作为后备
    import html
    import unicodedata
    
    class Normalizer:
        @staticmethod
        def normalize_for_matching(text: str) -> str:
            """规范化文本用于匹配，移除空格、逗号、点等标点符号，统一特殊符号的不同版本"""
            if not text:
                return ""
            
            # HTML实体解码
            normalized = html.unescape(text)
            
            # Unicode标准化（NFKC）
            normalized = unicodedata.normalize('NFKC', normalized)
            
            # 特殊符号映射
            symbol_mappings = {
                '\uFF06': '&',  # 全角 & (＆)
                '\u214B': '&',  # 转置符号 (&)
                '\u2013': '-',  # 短破折号 (–)
                '\u2014': '-',  # 长破折号 (—)
                '\u2015': '-',  # 水平线 (―)
                '\u2212': '-',  # 减号 (−)
                '\uFF0D': '-',  # 全角减号 (－)
                '\u2018': "'",  # 左单引号 (')
                '\u2019': "'",  # 右单引号 (')
                '\u201C': '"',  # 左双引号 (")
                '\u201D': '"',  # 右双引号 (")
                '\uFF02': '"',  # 全角双引号 (")
                '\uFF07': "'",  # 全角单引号 (')
                '\u00A0': ' ',  # 不间断空格
                '\u3000': ' ',  # 表意文字空格（全角空格）
            }
            
            for old_char, new_char in symbol_mappings.items():
                normalized = normalized.replace(old_char, new_char)
            
            # 移除标点符号和空格
            normalized = re.sub(r'[\s,\.・。、，\u00B7\u2022\u2027\u2219]', '', normalized)
            
            return normalized


class TransformProcessor:
    """Transform处理器"""
    
    # 配置缓存
    _config_cache: Optional[Dict[str, Any]] = None
    _watch_dict_cache: Optional[Dict[str, Any]] = None
    
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
        elif transform_type == "split_watch_title":
            return TransformProcessor.split_watch_title(value, config)
        else:
            # 未知的transform类型，返回原值
            return value

    @staticmethod
    def _load_watch_dict(dict_path: Optional[str] = None) -> Dict[str, Any]:
        """加载腕表字典"""
        if TransformProcessor._watch_dict_cache is not None and not dict_path:
            return TransformProcessor._watch_dict_cache
        
        path = dict_path
        if not path:
            # 新的字典路径：从 i18n 模块加载
            # 兼容旧路径，如果新路径不存在则使用旧路径
            new_path = Path(__file__).parent.parent.parent / "i18n" / "dictionaries" / "watch.yaml"
            old_path = Path(__file__).parent / "dictionary" / "watch.yaml"
            path = new_path if new_path.exists() else old_path
        try:
            with open(path, "r", encoding="utf-8") as f:
                TransformProcessor._watch_dict_cache = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[TransformProcessor] 加载腕表字典失败: {e}")
            TransformProcessor._watch_dict_cache = {}
        return TransformProcessor._watch_dict_cache

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
    def split_watch_title(value: Any, config: dict) -> Any:
        """
        将标题拆分为品牌、型号、型号编号
        
        返回格式：
        {
            "__value__": 原始清洗后的标题,
            "__extra_fields__": {
                "brand_name": ...,
                "model_name": ...,
                "model_no": ...
            }
        }
        """
        if not isinstance(value, str):
            return value
        
        raw_value = value.strip()
        if not raw_value:
            return value

        # 清洗文本：移除【...】、替换全角空格并裁掉“腕時計/時計/ウォッチ”后的尾部
        cleaned = re.sub(r"【[^】]*】", " ", raw_value)
        cleaned = cleaned.replace("　", " ")
        cleaned = re.split(r"(腕時計|ウォッチ|時計)", cleaned, maxsplit=1)[0]
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 拆分为token，去掉常见的性别/后缀词
        tokens = [t for t in cleaned.split(" ") if t]
        suffix_tokens = set(config.get("suffix_tokens", ["メンズ", "レディース", "ユニセックス", "男女兼用", "ボーイズ", "ガールズ"]))
        while tokens and tokens[-1] in suffix_tokens:
            tokens.pop()
        if not tokens:
            return {"__value__": cleaned, "__extra_fields__": {}}

        original_tokens = tokens.copy()
        fallback_brand = original_tokens[0]

        # 加载字典
        watch_dict = TransformProcessor._load_watch_dict(config.get("dictionary_path"))

        def looks_like_model_no(token: str) -> bool:
            if not token or len(token) < 3:
                return False
            if not re.search(r"\d", token):
                return False
            if re.fullmatch(r"[0-9]{1,2}", token):
                return False
            return re.fullmatch(r"[A-Za-z0-9./-]+", token) is not None

        # 品牌匹配（优先匹配最长别名）
        brand_name = None
        matched_brand_alias = None  # 保存匹配到的原始别名
        consume_brand = 0
        alias_candidates = []
        for brand, data in (watch_dict or {}).items():
            aliases = data.get("aliases", []) if isinstance(data, dict) else []
            alias_candidates.append((brand, brand))
            for alias in aliases:
                alias_candidates.append((alias, brand))
        alias_candidates.sort(key=lambda x: len(x[0]), reverse=True)

        # 先尝试精确匹配
        for alias, canonical_brand in alias_candidates:
            alias_tokens = [t for t in alias.split(" ") if t]
            if alias_tokens and tokens[: len(alias_tokens)] == alias_tokens:
                # 匹配成功，保存原始匹配到的别名，而不是标准名称
                matched_brand_alias = " ".join(tokens[: len(alias_tokens)])
                brand_name = matched_brand_alias
                consume_brand = len(alias_tokens)
                break
            if cleaned.startswith(alias):
                # 匹配成功，保存原始匹配到的别名
                matched_brand_alias = alias
                brand_name = matched_brand_alias
                consume_brand = max(1, len(alias_tokens))
                break
        
        # 如果精确匹配失败，使用规范化匹配（忽略标点符号）
        if not brand_name:
            cleaned_normalized = Normalizer.normalize_for_matching(cleaned).lower()
            for alias, canonical_brand in alias_candidates:
                alias_normalized = Normalizer.normalize_for_matching(alias).lower()
                # 检查规范化后的文本是否以规范化后的别名开头
                if cleaned_normalized.startswith(alias_normalized):
                    # 从原始cleaned文本中提取匹配的部分
                    # 如果cleaned以alias开头，直接使用alias
                    if cleaned.startswith(alias):
                        matched_brand_alias = alias
                    else:
                        # 规范化匹配成功，但从tokens中提取对应数量的token作为匹配到的品牌名
                        # 这样可以保留原始文本的格式
                        alias_tokens = [t for t in alias.split(" ") if t]
                        if alias_tokens and len(tokens) >= len(alias_tokens):
                            matched_brand_alias = " ".join(tokens[: len(alias_tokens)])
                        else:
                            # 如果无法从tokens提取，尝试从cleaned开头提取与alias字符长度相近的部分
                            # 由于规范化可能移除标点，我们提取稍长一些的文本以确保包含完整品牌名
                            char_length = len(alias)
                            # 从cleaned开头提取，考虑可能的标点符号
                            extracted = cleaned[:min(char_length + 10, len(cleaned))].strip()
                            # 尝试找到合理的截断点（在空格或标点处）
                            for sep in [' ', '　', '・', '.', ',']:
                                idx = extracted.find(sep, char_length - 5)
                                if idx > 0:
                                    extracted = extracted[:idx].strip()
                                    break
                            matched_brand_alias = extracted if extracted else alias
                    brand_name = matched_brand_alias
                    # 尝试估算消耗的token数量
                    alias_tokens = [t for t in alias.split(" ") if t]
                    consume_brand = max(1, len(alias_tokens))
                    break
        
        if consume_brand:
            tokens = tokens[consume_brand:]
        if not brand_name:
            brand_name = fallback_brand

        # 型号名匹配（使用品牌下的model_name别名）
        model_name = None
        matched_model_alias = None  # 保存匹配到的原始别名
        consume_model = 0
        # 注意：这里brand_name可能是匹配到的别名，需要找到对应的标准品牌名用于查找model_dict
        # 如果brand_name是匹配到的别名，需要从字典中反向查找标准品牌名
        canonical_brand_for_model_search = None
        if isinstance(watch_dict, dict):
            for brand, data in watch_dict.items():
                if brand == brand_name:
                    canonical_brand_for_model_search = brand
                    break
                if isinstance(data, dict):
                    aliases = data.get("aliases", [])
                    if brand_name in aliases or brand_name == brand:
                        canonical_brand_for_model_search = brand
                        break
        
        brand_data = watch_dict.get(canonical_brand_for_model_search or brand_name, {}) if isinstance(watch_dict, dict) else {}
        model_dict = brand_data.get("model_name", {}) if isinstance(brand_data, dict) else {}
        remaining_text = " ".join(tokens)
        if isinstance(model_dict, dict):
            model_candidates = []
            for canonical_model, info in model_dict.items():
                aliases = info.get("aliases", []) if isinstance(info, dict) else []
                model_candidates.append((canonical_model, canonical_model))
                for alias in aliases:
                    model_candidates.append((alias, canonical_model))
            model_candidates.sort(key=lambda x: len(x[0]), reverse=True)

            # 先尝试精确匹配
            for alias, canonical_model in model_candidates:
                alias_tokens = [t for t in alias.split(" ") if t]
                if remaining_text.startswith(alias):
                    # 匹配成功，保存原始匹配到的别名（从原始文本中提取）
                    matched_model_alias = alias
                    model_name = matched_model_alias
                    consume_model = len(alias_tokens) if alias_tokens else 1
                    break
                elif alias_tokens and len(tokens) >= len(alias_tokens) and tokens[: len(alias_tokens)] == alias_tokens:
                    # token序列匹配，从tokens中提取
                    matched_model_alias = " ".join(tokens[: len(alias_tokens)])
                    model_name = matched_model_alias
                    consume_model = len(alias_tokens)
                    break
                elif f" {alias} " in f" {remaining_text} ":
                    # 在文本中间找到匹配，从remaining_text中提取
                    start_idx = remaining_text.find(alias)
                    if start_idx >= 0:
                        matched_model_alias = alias
                        model_name = matched_model_alias
                        consume_model = len(alias_tokens) if alias_tokens else 1
                        break
            
            # 如果精确匹配失败，使用规范化匹配（忽略标点符号）
            if not model_name:
                remaining_text_normalized = Normalizer.normalize_for_matching(remaining_text).lower()
                for alias, canonical_model in model_candidates:
                    alias_normalized = Normalizer.normalize_for_matching(alias).lower()
                    # 检查规范化后的文本是否包含规范化后的别名
                    if remaining_text_normalized.startswith(alias_normalized) or alias_normalized in remaining_text_normalized:
                        # 从原始remaining_text中提取匹配的部分
                        if remaining_text.startswith(alias):
                            matched_model_alias = alias
                        else:
                            # 规范化匹配成功，从tokens中提取对应数量的token作为匹配到的型号名
                            alias_tokens = [t for t in alias.split(" ") if t]
                            if alias_tokens and len(tokens) >= len(alias_tokens):
                                matched_model_alias = " ".join(tokens[: len(alias_tokens)])
                            else:
                                # 如果无法从tokens提取，尝试从remaining_text开头提取
                                char_length = len(alias)
                                extracted = remaining_text[:min(char_length + 10, len(remaining_text))].strip()
                                # 尝试找到合理的截断点
                                for sep in [' ', '　', '・', '.', ',']:
                                    idx = extracted.find(sep, char_length - 5)
                                    if idx > 0:
                                        extracted = extracted[:idx].strip()
                                        break
                                matched_model_alias = extracted if extracted else alias
                        model_name = matched_model_alias
                        # 尝试估算消耗的token数量
                        alias_tokens = [t for t in alias.split(" ") if t]
                        if alias_tokens and tokens[: len(alias_tokens)] == alias_tokens:
                            consume_model = len(alias_tokens)
                        else:
                            consume_model = max(1, len(alias_tokens))
                        break
        if consume_model:
            tokens = tokens[consume_model:]

        # 型号编号匹配（从尾部寻找疑似型号编号的token）
        model_no = None
        for idx in range(len(tokens) - 1, -1, -1):
            token = tokens[idx]
            if looks_like_model_no(token):
                model_no = token
                tokens.pop(idx)
                break

        if not model_name and tokens:
            model_name = " ".join(tokens).strip() or None

        extras = {}
        if brand_name:
            extras["brand_name"] = brand_name
        if model_name:
            extras["model_name"] = model_name
        if model_no:
            extras["model_no"] = model_no

        return {
            "__value__": cleaned,
            "__extra_fields__": extras
        }

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

