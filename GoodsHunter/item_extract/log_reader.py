"""Crawler Log 读取：从 crawler_log 表读取未处理的记录"""
from typing import List, Dict, Optional
from .exceptions import DatabaseError


def fetch_unprocessed_logs(
    conn,
    last_log_id: int,
    batch_size: int = 100
) -> List[Dict]:
    """
    获取未处理的日志记录
    
    Args:
        conn: 数据库连接对象
        last_log_id: 上次处理的 log_id
        batch_size: 批量大小
        
    Returns:
        日志记录列表，每个记录是一个字典
    """
    cursor = conn.cursor()
    try:
        # 查询未处理的记录，按 id 升序排列
        cursor.execute(
            """
            SELECT 
                id, category, site, item_id, raw_json,
                brand_name, model_name, model_no,
                currency, price,
                image_original_key, image_thumb_300_key, image_thumb_600_key, image_sha256,
                source_uid, crawl_time, dt
            FROM crawler_log
            WHERE id > %s 
                AND status = 'success'
            ORDER BY id ASC
            LIMIT %s
            """,
            (last_log_id, batch_size)
        )
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        
        # 转换为字典列表
        records = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            records.append(record)
        
        return records
        
    except Exception as e:
        raise DatabaseError(f"读取 crawler_log 失败: {e}")
    finally:
        cursor.close()


def get_log_count(conn, last_log_id: int) -> int:
    """
    获取待处理记录数（用于进度显示）
    
    Args:
        conn: 数据库连接对象
        last_log_id: 上次处理的 log_id
        
    Returns:
        待处理记录数
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM crawler_log
            WHERE id > %s 
                AND status = 'success'
            """,
            (last_log_id,)
        )
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        raise DatabaseError(f"获取待处理记录数失败: {e}")
    finally:
        cursor.close()

