"""游标状态管理：管理 pipeline_state 表"""
from typing import Optional
from .utils import get_db_connection
from .exceptions import DatabaseError


# 游标键名
CURSOR_KEY_LAST_LOG_ID = "items_sync_last_log_id"


def get_last_log_id(conn) -> Optional[int]:
    """
    获取上次处理的 log_id
    
    Args:
        conn: 数据库连接对象
        
    Returns:
        上次处理的 log_id，如果不存在则返回 None
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT value FROM pipeline_state WHERE key = %s",
            (CURSOR_KEY_LAST_LOG_ID,)
        )
        row = cursor.fetchone()
        if row:
            try:
                return int(row[0])
            except (ValueError, TypeError):
                return None
        return None
    except Exception as e:
        raise DatabaseError(f"获取 last_log_id 失败: {e}")
    finally:
        cursor.close()


def update_last_log_id(conn, log_id: int) -> None:
    """
    更新游标（last_log_id）
    
    Args:
        conn: 数据库连接对象
        log_id: 最新处理的 log_id
    """
    cursor = conn.cursor()
    try:
        # 使用 INSERT ... ON CONFLICT UPDATE
        cursor.execute(
            """
            INSERT INTO pipeline_state (key, value, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (key) 
            DO UPDATE SET value = EXCLUDED.value, updated_at = now()
            """,
            (CURSOR_KEY_LAST_LOG_ID, str(log_id))
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"更新 last_log_id 失败: {e}")
    finally:
        cursor.close()


def get_state(conn, key: str) -> Optional[str]:
    """
    获取通用状态值
    
    Args:
        conn: 数据库连接对象
        key: 状态键名
        
    Returns:
        状态值，如果不存在则返回 None
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT value FROM pipeline_state WHERE key = %s",
            (key,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        raise DatabaseError(f"获取状态 {key} 失败: {e}")
    finally:
        cursor.close()


def set_state(conn, key: str, value: str) -> None:
    """
    设置通用状态值
    
    Args:
        conn: 数据库连接对象
        key: 状态键名
        value: 状态值
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO pipeline_state (key, value, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (key) 
            DO UPDATE SET value = EXCLUDED.value, updated_at = now()
            """,
            (key, value)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"设置状态 {key} 失败: {e}")
    finally:
        cursor.close()

