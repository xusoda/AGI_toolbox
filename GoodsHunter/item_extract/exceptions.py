"""自定义异常类"""


class ItemExtractError(Exception):
    """Item Extract 模块基础异常"""
    pass


class DatabaseError(ItemExtractError):
    """数据库相关错误"""
    pass


class ValidationError(ItemExtractError):
    """数据验证错误"""
    pass

