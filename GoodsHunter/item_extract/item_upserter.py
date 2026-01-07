"""Item 表 Upsert 逻辑：从 crawler_log 记录构建并更新 item 数据"""
from typing import Dict, Optional, Tuple
from datetime import datetime, date
from .source_uid_generator import generate_source_uid
from .price_normalizer import normalize_price
from .exceptions import DatabaseError


def upsert_item(conn, log_record: Dict) -> Tuple[Dict, Optional[int]]:
    """
    Upsert item 到 crawler_item 表
    
    逻辑：
    1. 如果 item 不存在：插入新记录，返回 (item_data, None)
    2. 如果 item 存在：更新 last_seen_dt/last_crawl_time/last_log_id，返回 (item_data, old_price)
    
    使用 SELECT ... FOR UPDATE 防止并发问题
    
    Args:
        conn: 数据库连接对象
        log_record: crawler_log 记录字典
        
    Returns:
        (item_data, old_price) 元组
        - item_data: 更新后的 item 数据字典
        - old_price: 旧价格（如果是新商品则为 None）
    """
    cursor = conn.cursor()
    
    try:
        # 从 log_record 提取数据
        site = log_record.get('site', '').strip()
        category = log_record.get('category', '').strip()
        item_id = log_record.get('item_id', '').strip()
        
        if not site or not category or not item_id:
            raise ValueError(
                f"缺少必要字段: site={site}, category={category}, item_id={item_id}"
            )
        
        # 生成 source_uid
        source_uid = generate_source_uid(site, category, item_id)
        
        # 规范化价格
        raw_price = log_record.get('price')
        currency = log_record.get('currency', 'JPY')
        new_price = normalize_price(raw_price, currency)
        
        # 提取其他字段
        brand_name = log_record.get('brand_name')
        model_name = log_record.get('model_name')
        model_no = log_record.get('model_no')
        image_sha256 = log_record.get('image_sha256')
        image_original_key = log_record.get('image_original_key')
        image_thumb_300_key = log_record.get('image_thumb_300_key')
        image_thumb_600_key = log_record.get('image_thumb_600_key')
        
        # 时间字段
        crawl_time = log_record.get('crawl_time')
        if isinstance(crawl_time, str):
            # 如果是字符串，尝试解析
            try:
                crawl_time = datetime.fromisoformat(crawl_time.replace('Z', '+00:00'))
            except:
                crawl_time = datetime.now()
        elif not isinstance(crawl_time, datetime):
            crawl_time = datetime.now()
        
        dt = log_record.get('dt')
        if isinstance(dt, str):
            try:
                dt = date.fromisoformat(dt)
            except:
                dt = date.today()
        elif not isinstance(dt, date):
            dt = date.today()
        
        log_id = log_record.get('id')
        
        # 使用 SELECT ... FOR UPDATE 锁定行（如果存在）
        cursor.execute(
            """
            SELECT id, price, version
            FROM crawler_item
            WHERE source_uid = %s
            FOR UPDATE
            """,
            (source_uid,)
        )
        
        existing = cursor.fetchone()
        new_item_id = None
        
        if existing is None:
            # 新商品：插入
            old_price = None
            version = 1
            
            cursor.execute(
                """
                INSERT INTO crawler_item (
                    source_uid, site, category, item_id,
                    brand_name, model_name, model_no,
                    currency, price,
                    image_sha256, image_original_key, image_thumb_300_key, image_thumb_600_key,
                    status, first_seen_dt, last_seen_dt,
                    last_crawl_time, last_log_id, version
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    'active', %s, %s,
                    %s, %s, %s
                )
                RETURNING id
                """,
                (
                    source_uid, site, category, item_id,
                    brand_name, model_name, model_no,
                    currency, new_price,
                    image_sha256, image_original_key, image_thumb_300_key, image_thumb_600_key,
                    dt, dt,  # first_seen_dt, last_seen_dt
                    crawl_time, log_id, version
                )
            )
            new_item_id = cursor.fetchone()[0]
            
        else:
            # 已存在商品：更新
            item_db_id, old_price, current_version = existing
            
            # 更新基础字段（不论价格是否变化都更新）
            cursor.execute(
                """
                UPDATE crawler_item
                SET 
                    last_seen_dt = %s,
                    last_crawl_time = %s,
                    last_log_id = %s,
                    updated_at = now()
                WHERE id = %s
                """,
                (dt, crawl_time, log_id, item_db_id)
            )
            
            version = current_version
            new_item_id = item_db_id
        
        # 构建返回的 item_data
        item_data = {
            'id': new_item_id,
            'source_uid': source_uid,
            'site': site,
            'category': category,
            'item_id': item_id,
            'brand_name': brand_name,
            'model_name': model_name,
            'model_no': model_no,
            'currency': currency,
            'price': new_price,
            'image_sha256': image_sha256,
            'image_original_key': image_original_key,
            'image_thumb_300_key': image_thumb_300_key,
            'image_thumb_600_key': image_thumb_600_key,
            'version': version,
            'crawl_time': crawl_time,
            'dt': dt,
            'log_id': log_id
        }
        
        return item_data, old_price
        
    except Exception as e:
        raise DatabaseError(f"Upsert item 失败: {e}")
    finally:
        cursor.close()


def update_item_price(
    conn,
    source_uid: str,
    new_price: Optional[int],
    crawl_time: datetime,
    dt: date,
    new_version: int
) -> None:
    """
    更新 item 的价格相关字段（当价格变化时调用）
    
    Args:
        conn: 数据库连接对象
        source_uid: 商品唯一标识
        new_price: 新价格
        crawl_time: 抓取时间
        dt: 日期
        new_version: 新版本号
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE crawler_item
            SET 
                price = %s,
                price_last_changed_at = %s,
                price_last_changed_dt = %s,
                version = %s,
                updated_at = now()
            WHERE source_uid = %s
            """,
            (new_price, crawl_time, dt, new_version, source_uid)
        )
    except Exception as e:
        raise DatabaseError(f"更新 item 价格失败: {e}")
    finally:
        cursor.close()

