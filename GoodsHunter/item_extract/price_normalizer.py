"""价格规范化：将价格字符串转换为整数"""
from typing import Any, Optional
from .exceptions import ValidationError


def normalize_price(price: Any, currency: str = 'JPY') -> Optional[int]:
    """
    规范化价格：将各种格式的价格转换为整数
    
    Args:
        price: 价格值（可能是字符串、整数、浮点数或 None）
        currency: 货币单位（默认 JPY）
        
    Returns:
        规范化后的价格（整数），如果无法转换则返回 None
        
    Examples:
        >>> normalize_price("1,234,567")
        1234567
        >>> normalize_price("¥1,234")
        1234
        >>> normalize_price(1234.5)
        1234
        >>> normalize_price(None)
        None
        >>> normalize_price("invalid")
        None
    """
    if price is None:
        return None
    
    # 如果是整数，直接返回
    if isinstance(price, int):
        return price
    
    # 如果是浮点数，转换为整数
    if isinstance(price, float):
        return int(price)
    
    # 如果是字符串，需要清理和转换
    if isinstance(price, str):
        # 移除空白字符
        price_str = price.strip()
        if not price_str:
            return None
        
        # 移除货币符号和逗号
        price_str = price_str.replace(",", "").replace("¥", "").replace("$", "").replace("€", "").strip()
        
        # 移除其他非数字字符（保留小数点和负号）
        cleaned = ""
        for char in price_str:
            if char.isdigit() or char in ('.', '-'):
                cleaned += char
        
        if not cleaned:
            return None
        
        try:
            # 转换为浮点数再转整数（处理小数）
            return int(float(cleaned))
        except (ValueError, TypeError):
            return None
    
    # 其他类型，尝试转换
    try:
        return int(float(price))
    except (ValueError, TypeError):
        return None


def is_price_changed(old_price: Optional[int], new_price: Optional[int]) -> bool:
    """
    判断价格是否变化（正确处理 NULL）
    
    使用 PostgreSQL 的 IS DISTINCT FROM 语义：
    - NULL != NULL -> False（两个 NULL 视为相同）
    - NULL != 123 -> True
    - 123 != 456 -> True
    - 123 != 123 -> False
    
    Args:
        old_price: 旧价格
        new_price: 新价格
        
    Returns:
        如果价格变化返回 True，否则返回 False
    """
    # 两个都是 None，视为相同
    if old_price is None and new_price is None:
        return False
    
    # 一个 None 一个非 None，视为变化
    if old_price is None or new_price is None:
        return True
    
    # 两个都不为 None，直接比较
    return old_price != new_price

