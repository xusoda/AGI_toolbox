"""货币代码枚举"""
from enum import Enum
from typing import List, Optional


class CurrencyCode(str, Enum):
    """货币代码枚举
    
    用于标识商品价格的货币单位。
    """
    JPY = "JPY"  # 日元
    USD = "USD"  # 美元
    CNY = "CNY"  # 人民币
    
    @classmethod
    def all_values(cls) -> List[str]:
        """获取所有枚举值列表"""
        return [item.value for item in cls]
    
    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """检查值是否为有效的货币代码"""
        if value is None:
            return False
        return value in cls.all_values()
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认货币代码"""
        return cls.JPY.value
