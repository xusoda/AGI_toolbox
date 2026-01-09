"""商品状态枚举"""
from enum import Enum
from typing import List, Optional


class ItemStatus(str, Enum):
    """商品状态枚举
    
    用于标识商品的当前状态。
    """
    ACTIVE = "active"      # 在售
    SOLD = "sold"          # 已售出
    REMOVED = "removed"    # 已下架
    
    @classmethod
    def all_values(cls) -> List[str]:
        """获取所有枚举值列表"""
        return [item.value for item in cls]
    
    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """检查值是否为有效的状态"""
        if value is None:
            return False
        return value in cls.all_values()
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认状态"""
        return cls.ACTIVE.value
