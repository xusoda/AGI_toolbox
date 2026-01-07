"""Event Key 生成：用于幂等性保证"""
import hashlib
from datetime import date
from typing import Optional


def generate_price_event_key(source_uid: str, log_id: int, new_price: Optional[int] = None) -> str:
    """
    生成价格变化事件的 event_key
    
    格式：sha256(source_uid + ':price:' + log_id + ':' + new_price)
    如果 new_price 为 None，则只使用 source_uid + ':price:' + log_id
    
    Args:
        source_uid: 商品唯一标识
        log_id: crawler_log 的 id
        new_price: 新价格（可选，用于更严格的去重）
        
    Returns:
        SHA256 哈希值（64 字符的十六进制字符串）
        
    Examples:
        >>> key = generate_price_event_key("site:cat:123", 456, 1000)
        >>> len(key)
        64
    """
    # 构建基础字符串
    base_str = f"{source_uid}:price:{log_id}"
    
    # 如果提供了 new_price，添加到字符串中（用于更严格的去重）
    if new_price is not None:
        base_str += f":{new_price}"
    
    # 计算 SHA256 哈希
    return hashlib.sha256(base_str.encode('utf-8')).hexdigest()


def generate_status_event_key(source_uid: str, sold_dt: date, status: str) -> str:
    """
    生成状态变化事件的 event_key（预留）
    
    格式：sha256(source_uid + ':status:' + sold_dt + ':' + status)
    
    Args:
        source_uid: 商品唯一标识
        sold_dt: 判定为已售的日期
        status: 新状态（通常是 'sold'）
        
    Returns:
        SHA256 哈希值（64 字符的十六进制字符串）
    """
    base_str = f"{source_uid}:status:{sold_dt}:{status}"
    return hashlib.sha256(base_str.encode('utf-8')).hexdigest()

