"""Source UID 生成：生成标准化的 source_uid"""
from typing import Tuple


def generate_source_uid(site: str, category: str, item_id: str) -> str:
    """
    生成标准化的 source_uid
    
    格式：{site}:{category}:{item_id}
    
    Args:
        site: 站点名称
        category: 商品类别
        item_id: 商品ID
        
    Returns:
        source_uid 字符串
        
    Examples:
        >>> generate_source_uid("commit-watch.co.jp", "watch", "12345")
        'commit-watch.co.jp:watch:12345'
    """
    # 确保所有参数都是字符串且不为空
    site = str(site).strip() if site else ""
    category = str(category).strip() if category else ""
    item_id = str(item_id).strip() if item_id else ""
    
    if not site or not category or not item_id:
        raise ValueError(
            f"source_uid 生成失败：site={site}, category={category}, item_id={item_id}"
        )
    
    return f"{site}:{category}:{item_id}"


def parse_source_uid(source_uid: str) -> Tuple[str, str, str]:
    """
    解析 source_uid（用于调试）
    
    Args:
        source_uid: source_uid 字符串
        
    Returns:
        (site, category, item_id) 元组
        
    Raises:
        ValueError: 如果 source_uid 格式不正确
        
    Examples:
        >>> parse_source_uid("commit-watch.co.jp:watch:12345")
        ('commit-watch.co.jp', 'watch', '12345')
    """
    if not source_uid:
        raise ValueError("source_uid 不能为空")
    
    parts = source_uid.split(":", 2)
    if len(parts) != 3:
        raise ValueError(f"source_uid 格式不正确: {source_uid}")
    
    site, category, item_id = parts
    return site, category, item_id

