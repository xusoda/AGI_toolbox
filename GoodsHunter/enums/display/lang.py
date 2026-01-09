"""语言代码枚举"""
from enum import Enum
from typing import List, Optional


class LanguageCode(str, Enum):
    """语言代码枚举
    
    用于标识系统支持的语言。
    """
    EN = "en"  # 英语
    ZH = "zh"  # 中文（简体）
    JA = "ja"  # 日语
    
    @classmethod
    def all_values(cls) -> List[str]:
        """获取所有枚举值列表"""
        return [item.value for item in cls]
    
    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """检查值是否为有效的语言代码"""
        if value is None:
            return False
        return value in cls.all_values()
    
    @classmethod
    def get_default(cls) -> str:
        """获取默认语言代码"""
        return cls.EN.value
