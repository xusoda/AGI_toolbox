"""变化检测逻辑：检测价格变化和状态变化"""
from typing import Optional
from .price_normalizer import is_price_changed


def detect_price_change(old_price: Optional[int], new_price: Optional[int]) -> bool:
    """
    检测价格是否变化
    
    Args:
        old_price: 旧价格
        new_price: 新价格
        
    Returns:
        如果价格变化返回 True，否则返回 False
    """
    return is_price_changed(old_price, new_price)


def should_record_price_change(old_price: Optional[int], new_price: Optional[int]) -> bool:
    """
    判断是否需要记录价格变化
    
    规则：
    - 新商品（old_price 为 None）不记录初始价格
    - 已存在商品且价格变化时才记录
    
    Args:
        old_price: 旧价格（None 表示新商品）
        new_price: 新价格
        
    Returns:
        如果需要记录返回 True，否则返回 False
    """
    # 新商品不记录初始价格
    if old_price is None:
        return False
    
    # 已存在商品，检查价格是否变化
    return detect_price_change(old_price, new_price)

