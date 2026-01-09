"""变更历史写入：写入 item_change_history 表"""
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, date
from .event_key_generator import generate_price_event_key, generate_status_event_key
from .exceptions import DatabaseError

# 添加项目根目录到路径（如果还未添加）
if not any('enums' in str(p) or Path(str(p)).name == 'GoodsHunter' for p in sys.path):
    current_file = Path(__file__)
    possible_roots = [
        current_file.parent.parent.parent,  # 从 item_extract/history_writer.py 向上3级
        Path("/app/..").resolve(),  # Docker 容器中的项目根目录
        Path("/app").parent,  # Docker 容器中，/app 的父目录
    ]
    for root in possible_roots:
        enums_path = root / "enums"
        if enums_path.exists() and enums_path.is_dir():
            sys.path.insert(0, str(root))
            break

from enums.business.change_type import ChangeType


def write_price_change(
    conn,
    source_uid: str,
    old_price: Optional[int],
    new_price: Optional[int],
    currency: str,
    log_id: int,
    crawl_time: datetime,
    dt: date,
    item_version: int
) -> bool:
    """
    写入价格变化记录到 item_change_history
    
    Args:
        conn: 数据库连接对象
        source_uid: 商品唯一标识
        old_price: 旧价格
        new_price: 新价格
        currency: 货币单位
        log_id: crawler_log 的 id
        crawl_time: 抓取时间
        dt: 变更日期
        item_version: item 的版本号
        
    Returns:
        如果写入成功返回 True，如果因为唯一约束冲突（已存在）返回 False
    """
    cursor = conn.cursor()
    
    try:
        # 生成 event_key
        event_key = generate_price_event_key(source_uid, log_id, new_price)
        
        # 转换为字符串（处理 None）
        old_value_str = str(old_price) if old_price is not None else None
        new_value_str = str(new_price) if new_price is not None else None
        
        # 插入历史记录
        # 使用 ON CONFLICT DO NOTHING 处理幂等性（如果 event_key 已存在，不插入）
        cursor.execute(
            """
            INSERT INTO item_change_history (
                dt, source_uid, change_time, change_type,
                old_value, new_value, currency,
                reason, log_id, item_version, event_key
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                'crawler_update', %s, %s, %s
            )
            ON CONFLICT (event_key) DO NOTHING
            """,
            (
                dt, source_uid, crawl_time, ChangeType.PRICE.value,
                old_value_str, new_value_str, currency,
                log_id, item_version, event_key
            )
        )
        
        # 检查是否实际插入了行
        inserted = cursor.rowcount > 0
        
        conn.commit()
        return inserted
        
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"写入价格变化历史失败: {e}")
    finally:
        cursor.close()


def write_status_change(
    conn,
    source_uid: str,
    old_status: str,
    new_status: str,
    sold_dt: date,
    reason: str,
    item_version: int
) -> bool:
    """
    写入状态变化记录到 item_change_history（预留）
    
    Args:
        conn: 数据库连接对象
        source_uid: 商品唯一标识
        old_status: 旧状态
        new_status: 新状态
        sold_dt: 判定为已售的日期
        reason: 原因（如 'not_seen_for_N_days'）
        item_version: item 的版本号
        
    Returns:
        如果写入成功返回 True，如果因为唯一约束冲突（已存在）返回 False
    """
    cursor = conn.cursor()
    
    try:
        # 生成 event_key
        event_key = generate_status_event_key(source_uid, sold_dt, new_status)
        
        # 插入历史记录
        cursor.execute(
            """
            INSERT INTO item_change_history (
                dt, source_uid, change_time, change_type,
                old_value, new_value,
                reason, item_version, event_key
            ) VALUES (
                %s, %s, now(), %s,
                %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (event_key) DO NOTHING
            """,
            (
                sold_dt, source_uid, ChangeType.STATUS.value,
                old_status, new_status,
                reason, item_version, event_key
            )
        )
        
        # 检查是否实际插入了行
        inserted = cursor.rowcount > 0
        
        conn.commit()
        return inserted
        
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"写入状态变化历史失败: {e}")
    finally:
        cursor.close()

