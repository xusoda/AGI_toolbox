"""排序相关的枚举"""
from enum import Enum


class SortOption(str, Enum):
    """列表页排序选项枚举"""
    FIRST_SEEN_DESC = "first_seen_desc"  # 首次发现时间（降序）
    PRICE_ASC = "price_asc"               # 价格（升序）
    PRICE_DESC = "price_desc"             # 价格（降序）
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认排序选项"""
        return cls.FIRST_SEEN_DESC.value


class SortField(str, Enum):
    """搜索页排序字段枚举"""
    PRICE = "price"           # 价格
    LAST_SEEN_DT = "last_seen_dt"  # 最后发现时间
    CREATED_AT = "created_at"       # 创建时间
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认排序字段"""
        return cls.LAST_SEEN_DT.value


class SortOrder(str, Enum):
    """排序顺序枚举"""
    ASC = "asc"    # 升序
    DESC = "desc"  # 降序
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认排序顺序"""
        return cls.DESC.value
