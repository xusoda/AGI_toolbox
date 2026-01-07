"""数据模型定义：表结构 SQL"""
from typing import Dict


def get_table_schemas() -> Dict[str, str]:
    """
    获取所有表的创建 SQL
    
    Returns:
        表名到 SQL 的字典
    """
    return {
        "pipeline_state": CREATE_PIPELINE_STATE_TABLE,
        "crawler_item": CREATE_CRAWLER_ITEM_TABLE,
        "item_change_history": CREATE_ITEM_CHANGE_HISTORY_TABLE,
    }


CREATE_PIPELINE_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS pipeline_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_state_updated_at 
    ON pipeline_state(updated_at);
"""


CREATE_CRAWLER_ITEM_TABLE = """
CREATE TABLE IF NOT EXISTS crawler_item (
    id BIGSERIAL PRIMARY KEY,
    source_uid TEXT NOT NULL UNIQUE,
    site TEXT NOT NULL,
    category TEXT NOT NULL,
    item_id TEXT NOT NULL,
    
    -- 展示字段（最新值）
    brand_name TEXT NULL,
    model_name TEXT NULL,
    model_no TEXT NULL,
    currency TEXT NOT NULL DEFAULT 'JPY',
    price INTEGER NULL,
    
    -- 图片引用（MinIO keys）
    image_sha256 TEXT NULL,
    image_original_key TEXT NULL,
    image_thumb_300_key TEXT NULL,
    image_thumb_600_key TEXT NULL,
    
    -- 状态字段
    status TEXT NOT NULL DEFAULT 'active',
    first_seen_dt DATE NOT NULL,
    last_seen_dt DATE NOT NULL,
    sold_dt DATE NULL,
    sold_reason TEXT NULL,
    
    -- 时间戳字段
    last_crawl_time TIMESTAMPTZ NOT NULL,
    last_log_id BIGINT NULL,
    price_last_changed_at TIMESTAMPTZ NULL,
    price_last_changed_dt DATE NULL,
    
    -- 版本号
    version INTEGER NOT NULL DEFAULT 1,
    
    -- 创建和更新时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 创建索引（为 APP 检索）
CREATE INDEX IF NOT EXISTS idx_crawler_item_site_category_status 
    ON crawler_item(site, category, status);
CREATE INDEX IF NOT EXISTS idx_crawler_item_brand_name 
    ON crawler_item(brand_name);
CREATE INDEX IF NOT EXISTS idx_crawler_item_model_no 
    ON crawler_item(model_no);
CREATE INDEX IF NOT EXISTS idx_crawler_item_price 
    ON crawler_item(price);
CREATE INDEX IF NOT EXISTS idx_crawler_item_last_seen_dt 
    ON crawler_item(last_seen_dt DESC);
CREATE INDEX IF NOT EXISTS idx_crawler_item_status 
    ON crawler_item(status);
"""


CREATE_ITEM_CHANGE_HISTORY_TABLE = """
-- 主表（分区表）
CREATE TABLE IF NOT EXISTS item_change_history (
    id BIGSERIAL,
    dt DATE NOT NULL,
    source_uid TEXT NOT NULL,
    change_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    change_type TEXT NOT NULL,
    old_value TEXT NULL,
    new_value TEXT NULL,
    currency TEXT NULL,
    reason TEXT NULL,
    log_id BIGINT NULL,
    item_version INTEGER NULL,
    event_key TEXT NOT NULL,
    PRIMARY KEY (dt, id),
    UNIQUE (dt, event_key)
) PARTITION BY RANGE (dt);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_item_chg_uid_time 
    ON item_change_history (source_uid, change_time DESC);
CREATE INDEX IF NOT EXISTS idx_item_chg_dt_type 
    ON item_change_history (dt, change_type);
CREATE INDEX IF NOT EXISTS idx_item_chg_source_uid 
    ON item_change_history (source_uid);
"""


def create_tables(conn):
    """
    创建所有需要的表
    
    Args:
        conn: 数据库连接对象
        
    Raises:
        Exception: 如果创建表失败
    """
    schemas = get_table_schemas()
    cursor = conn.cursor()
    
    try:
        # 创建 pipeline_state 表
        cursor.execute(CREATE_PIPELINE_STATE_TABLE)
        
        # 创建 crawler_item 表
        cursor.execute(CREATE_CRAWLER_ITEM_TABLE)
        
        # 创建 item_change_history 主表（分区表）
        cursor.execute(CREATE_ITEM_CHANGE_HISTORY_TABLE)
        
        # 创建当前月份的分区（如果不存在）
        _ensure_current_month_partition(conn, cursor)
        
        conn.commit()
        print("[models] 所有表创建成功")
        
    except Exception as e:
        conn.rollback()
        print(f"[models] 创建表失败: {e}")
        raise
    finally:
        cursor.close()


def _ensure_current_month_partition(conn, cursor):
    """
    确保当前月份的分区存在
    
    Args:
        conn: 数据库连接对象
        cursor: 游标对象
    """
    from datetime import datetime, date
    from calendar import monthrange
    
    now = datetime.now()
    year = now.year
    month = now.month
    
    # 计算月份的开始和结束日期
    start_date = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    end_date = date(year, month, days_in_month)
    
    # 计算下个月的第一天（作为分区上限）
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)
    
    # 分区名称
    partition_name = f"item_change_history_{year}_{month:02d}"
    
    # 检查分区是否存在
    check_sql = """
        SELECT EXISTS (
            SELECT 1 FROM pg_class 
            WHERE relname = %s
        )
    """
    cursor.execute(check_sql, (partition_name,))
    exists = cursor.fetchone()[0]
    
    if not exists:
        # 创建分区（使用参数化查询避免 SQL 注入）
        # 注意：PostgreSQL 的分区定义不能直接使用参数，需要使用字符串格式化
        # 但这里日期是程序生成的，不是用户输入，相对安全
        create_partition_sql = f"""
            CREATE TABLE IF NOT EXISTS {partition_name} 
            PARTITION OF item_change_history
            FOR VALUES FROM ('{start_date}') TO ('{next_month_start}')
        """
        cursor.execute(create_partition_sql)
        print(f"[models] 创建分区: {partition_name} ({start_date} 到 {next_month_start})")

