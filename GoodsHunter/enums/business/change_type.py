"""变更类型枚举"""
from enum import Enum
from typing import List, Optional


class ChangeType(str, Enum):
    """变更类型枚举
    
    用于标识商品变更历史的变更类型。
    """
    PRICE = "price"    # 价格变更
    STATUS = "status"  # 状态变更
    
    @classmethod
    def all_values(cls) -> List[str]:
        """获取所有枚举值列表"""
        return [item.value for item in cls]
    
    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """检查值是否为有效的变更类型"""
        if value is None:
            return False
        return value in cls.all_values()
