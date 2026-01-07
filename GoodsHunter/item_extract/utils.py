"""工具函数：数据库连接管理等"""
import os
from typing import Optional
from datetime import datetime

try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
except ImportError:
    psycopg2 = None
    SimpleConnectionPool = None

from .exceptions import DatabaseError


def get_database_url() -> str:
    """
    获取数据库连接URL
    
    Returns:
        数据库连接URL
        
    Raises:
        ValueError: 如果未设置 DATABASE_URL 环境变量
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("环境变量 DATABASE_URL 未设置")
    return database_url


def create_connection_pool(
    database_url: Optional[str] = None,
    pool_size: int = 5,
    max_overflow: int = 10
) -> SimpleConnectionPool:
    """
    创建数据库连接池
    
    Args:
        database_url: 数据库连接URL，如果为None则从环境变量读取
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
        
    Returns:
        连接池对象
        
    Raises:
        ImportError: 如果 psycopg2 未安装
        ValueError: 如果未提供 database_url 且环境变量未设置
    """
    if psycopg2 is None:
        raise ImportError(
            "psycopg2 未安装。请运行: pip install psycopg2-binary"
        )
    
    if database_url is None:
        database_url = get_database_url()
    
    pool = SimpleConnectionPool(
        minconn=1,
        maxconn=pool_size + max_overflow,
        dsn=database_url
    )
    
    if pool is None:
        raise DatabaseError("无法创建数据库连接池")
    
    return pool


def get_db_connection(database_url: Optional[str] = None):
    """
    获取单个数据库连接（不使用连接池）
    
    Args:
        database_url: 数据库连接URL，如果为None则从环境变量读取
        
    Returns:
        数据库连接对象
        
    Raises:
        ImportError: 如果 psycopg2 未安装
        ValueError: 如果未提供 database_url 且环境变量未设置
        DatabaseError: 如果连接失败
    """
    if psycopg2 is None:
        raise ImportError(
            "psycopg2 未安装。请运行: pip install psycopg2-binary"
        )
    
    if database_url is None:
        database_url = get_database_url()
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        raise DatabaseError(f"数据库连接失败: {e}")


def format_datetime(dt: datetime) -> str:
    """
    格式化日期时间为字符串
    
    Args:
        dt: 日期时间对象
        
    Returns:
        格式化后的字符串
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_int(value, default: Optional[int] = None) -> Optional[int]:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        
    Returns:
        整数或默认值
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # 移除逗号和其他非数字字符
            cleaned = value.replace(",", "").replace("¥", "").strip()
            if not cleaned:
                return default
            return int(float(cleaned))
        return default
    except (ValueError, TypeError):
        return default

