"""列表处理工具：提供预处理和后处理方法"""
from typing import List, Dict, Any, Optional


class ParseTool:
    """列表处理工具类，提供各种预处理和后处理方法"""
    
    @staticmethod
    def deduplicate_by_url(items: List[Dict[str, Any]], url_field: str = "product_url") -> List[Dict[str, Any]]:
        """
        基于URL字段去除重复的items
        
        Args:
            items: 待处理的items列表
            url_field: 用于去重的URL字段名，默认为"product_url"
            
        Returns:
            去重后的items列表
        """
        seen_urls = set()
        unique_items = []
        duplicates_count = 0
        
        for item in items:
            url = item.get(url_field)
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_items.append(item)
            elif url:
                duplicates_count += 1
                print(f"[ParseTool.deduplicate_by_url] 发现重复项，URL: {url}")
        
        if duplicates_count > 0:
            print(f"[ParseTool.deduplicate_by_url] 去重：移除了 {duplicates_count} 个重复项")
        
        print(f"[ParseTool.deduplicate_by_url] 去重后剩余 {len(unique_items)} 个唯一项")
        return unique_items
    
    @staticmethod
    def process(method_name: str, items: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        根据方法名调用相应的处理方法
        
        Args:
            method_name: 方法名，如 "deduplicate_by_url"
            items: 待处理的items列表
            config: 方法配置参数
            
        Returns:
            处理后的items列表
        """
        if config is None:
            config = {}
        
        if method_name == "deduplicate_by_url":
            url_field = config.get("url_field", "product_url")
            return ParseTool.deduplicate_by_url(items, url_field)
        else:
            print(f"[ParseTool.process] 未知的处理方法: {method_name}")
            return items

