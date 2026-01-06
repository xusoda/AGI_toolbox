"""正则表达式抽取策略"""
import re
from typing import Any, Dict, Optional


class RegexStrategy:
    """正则表达式抽取策略"""

    @staticmethod
    def extract(page_html: str, config: Dict[str, Any]) -> Optional[str]:
        """
        使用正则表达式从HTML中提取内容
        
        Args:
            page_html: 页面HTML内容
            config: 配置字典，必须包含：
                - pattern: 正则表达式模式
                可选：
                - flags: 正则标志（如 "i" 表示忽略大小写）
                - group: 捕获组索引（默认0，表示整个匹配）
                - strip: 是否去除首尾空白（默认True）
                
        Returns:
            提取的文本内容，如果未找到则返回None
        """
        if "pattern" not in config:
            return None

        try:
            pattern = config["pattern"]
            flags = 0

            # 处理flags
            if "flags" in config:
                flag_str = config["flags"]
                if "i" in flag_str or "I" in flag_str:
                    flags |= re.IGNORECASE
                if "m" in flag_str or "M" in flag_str:
                    flags |= re.MULTILINE
                if "s" in flag_str or "S" in flag_str:
                    flags |= re.DOTALL

            match = re.search(pattern, page_html, flags)
            if not match:
                return None

            # 获取指定捕获组
            group = config.get("group", 0)
            if group < len(match.groups()) + 1:
                result = match.group(group)
            else:
                result = match.group(0)

            if result:
                result = result.strip() if config.get("strip", True) else result
                return result

            return None

        except Exception:
            return None

