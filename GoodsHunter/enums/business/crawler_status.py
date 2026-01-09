"""抓取日志状态枚举"""
from enum import Enum
from typing import List, Optional


class CrawlerLogStatus(str, Enum):
    """抓取日志状态枚举
    
    用于标识抓取日志的状态。
    """
    SUCCESS = "success"  # 成功
    FAILED = "failed"    # 失败
    
    @classmethod
    def all_values(cls) -> List[str]:
        """获取所有枚举值列表"""
        return [item.value for item in cls]
    
    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """检查值是否为有效的抓取状态"""
        if value is None:
            return False
        return value in cls.all_values()
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认状态"""
        return cls.SUCCESS.value
