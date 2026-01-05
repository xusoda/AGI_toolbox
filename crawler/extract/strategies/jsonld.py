"""JSON-LD抽取策略"""
import json
import re
from typing import Any, Dict, Optional


class JSONLDStrategy:
    """JSON-LD抽取策略"""

    @staticmethod
    def extract(page_html: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从页面HTML中提取JSON-LD数据
        
        Args:
            page_html: 页面HTML内容
            config: 配置字典，可能包含：
                - selector: 选择器（默认查找所有script[type=application/ld+json]）
                - path: JSON路径（如 "name" 或 "offers.price"）
                
        Returns:
            提取的JSON数据，如果未找到则返回None
        """
        # 查找所有JSON-LD脚本标签
        pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, page_html, re.DOTALL | re.IGNORECASE)

        if not matches:
            return None

        # 尝试解析每个JSON-LD块
        for match in matches:
            try:
                data = json.loads(match.strip())
                
                # 如果配置了path，则提取特定路径的值
                if "path" in config:
                    value = JSONLDStrategy._get_nested_value(data, config["path"])
                    return value if value is not None else data
                
                return data
            except json.JSONDecodeError:
                continue

        return None

    @staticmethod
    def _get_nested_value(data: Any, path: str) -> Any:
        """
        从嵌套字典中获取值
        
        Args:
            data: 数据字典
            path: 路径，如 "name" 或 "offers.price"
            
        Returns:
            路径对应的值，如果不存在则返回None
        """
        keys = path.split(".")
        current = data

        # 如果data是列表，尝试在列表中查找
        if isinstance(current, list):
            for item in current:
                result = JSONLDStrategy._get_nested_value(item, path)
                if result is not None:
                    return result
            return None

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None

        return current

