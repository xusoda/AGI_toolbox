"""商品类别枚举"""
from enum import Enum
from typing import List, Optional


class Category(str, Enum):
    """商品类别枚举
    
    用于标识商品的类别，如手表、珠宝、箱包等。
    这个枚举值在抓取配置（profile）和筛选展示时都会使用。
    """
    WATCH = "watch"        # 手表
    BAG = "bag"            # 箱包
    JEWELRY = "jewelry"    # 珠宝/首饰
    CLOTHING = "clothing"  # 衣服
    CAMERA = "camera"      # 相机
    
    @classmethod
    def all_values(cls) -> List[str]:
        """获取所有枚举值列表"""
        return [item.value for item in cls]
    
    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """检查值是否为有效的类别"""
        if value is None:
            return False
        return value in cls.all_values()
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认类别"""
        return cls.WATCH.value
