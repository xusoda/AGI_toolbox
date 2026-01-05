"""Transform处理器：处理字段值的转换"""
import re
from typing import Any, Optional
from urllib.parse import urljoin, urlparse


class TransformProcessor:
    """Transform处理器"""

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

