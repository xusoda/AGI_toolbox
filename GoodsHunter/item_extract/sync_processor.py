"""主处理流程：协调各个模块完成同步"""
from typing import Dict, List, Optional
from datetime import datetime
from .log_reader import fetch_unprocessed_logs, get_log_count
from .item_upserter import upsert_item, update_item_price
from .change_detector import should_record_price_change
from .history_writer import write_price_change
from .state_manager import get_last_log_id, update_last_log_id
from .exceptions import DatabaseError


def process_single_log(conn, log_record: Dict) -> Dict:
    """
    处理单条 log 记录
    
    步骤：
    1. Upsert item（获取 old_price）
    2. 检测价格变化
    3. 如果变化，更新 item 价格字段并写入 history
    
    Args:
        conn: 数据库连接对象
        log_record: crawler_log 记录字典
        
    Returns:
        处理结果字典，包含：
        - success: 是否成功
        - source_uid: 商品唯一标识
        - price_changed: 价格是否变化
        - history_written: 是否写入了历史记录
        - error: 错误信息（如果有）
    """
    try:
        # 1. Upsert item（获取 old_price）
        item_data, old_price = upsert_item(conn, log_record)
        
        source_uid = item_data['source_uid']
        new_price = item_data['price']
        crawl_time = item_data['crawl_time']
        dt = item_data['dt']
        log_id = item_data['log_id']
        current_version = item_data['version']
        
        # 2. 检测价格变化
        price_changed = should_record_price_change(old_price, new_price)
        
        history_written = False
        
        if price_changed:
            # 3. 价格变化：更新 item 价格相关字段
            new_version = current_version + 1
            update_item_price(
                conn,
                source_uid,
                new_price,
                crawl_time,
                dt,
                new_version
            )
            
            # 4. 写入历史记录
            currency = item_data.get('currency', 'JPY')
            history_written = write_price_change(
                conn,
                source_uid,
                old_price,
                new_price,
                currency,
                log_id,
                crawl_time,
                dt,
                new_version
            )
        
        return {
            'success': True,
            'source_uid': source_uid,
            'price_changed': price_changed,
            'history_written': history_written,
            'old_price': old_price,
            'new_price': new_price,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'source_uid': log_record.get('source_uid', 'unknown'),
            'price_changed': False,
            'history_written': False,
            'error': str(e)
        }


def process_batch(conn, log_records: List[Dict]) -> Dict:
    """
    批量处理日志记录
    
    Args:
        conn: 数据库连接对象
        log_records: 日志记录列表
        
    Returns:
        处理结果统计字典
    """
    results = {
        'total': len(log_records),
        'success': 0,
        'failed': 0,
        'price_changed': 0,
        'history_written': 0,
        'errors': []
    }
    
    for log_record in log_records:
        result = process_single_log(conn, log_record)
        
        if result['success']:
            results['success'] += 1
            if result['price_changed']:
                results['price_changed'] += 1
            if result['history_written']:
                results['history_written'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({
                'log_id': log_record.get('id'),
                'source_uid': result.get('source_uid'),
                'error': result.get('error')
            })
    
    return results


def run_sync(
    conn,
    batch_size: int = 100,
    max_records: Optional[int] = None
) -> Dict:
    """
    主运行函数：执行完整的同步流程
    
    流程：
    1. 获取 last_log_id
    2. 读取未处理记录
    3. 批量处理
    4. 更新 last_log_id
    
    Args:
        conn: 数据库连接对象
        batch_size: 批量大小
        max_records: 最大处理记录数（None 表示不限制）
        
    Returns:
        同步结果统计字典
    """
    try:
        # 1. 获取 last_log_id
        last_log_id = get_last_log_id(conn) or 0
        
        # 获取待处理记录数
        total_pending = get_log_count(conn, last_log_id)
        
        print(f"[sync_processor] 开始同步，last_log_id={last_log_id}, 待处理记录数={total_pending}")
        
        # 2. 读取并处理记录
        total_processed = 0
        total_success = 0
        total_failed = 0
        total_price_changed = 0
        total_history_written = 0
        all_errors = []
        current_log_id = last_log_id  # 当前查询的起始 log_id（循环中会更新）
        max_log_id = last_log_id      # 已处理的最大 log_id（用于最终更新游标）
        
        while True:
            # 检查是否达到最大记录数
            if max_records and total_processed >= max_records:
                print(f"[sync_processor] 达到最大记录数限制: {max_records}")
                break
            
            # 读取一批记录（使用 current_log_id，而不是固定的 last_log_id）
            remaining = max_records - total_processed if max_records else None
            current_batch_size = min(batch_size, remaining) if remaining else batch_size
            
            log_records = fetch_unprocessed_logs(conn, current_log_id, current_batch_size)
            
            if not log_records:
                print(f"[sync_processor] 没有更多待处理记录")
                break
            
            # 处理这一批
            batch_results = process_batch(conn, log_records)
            
            # 更新统计
            total_processed += batch_results['total']
            total_success += batch_results['success']
            total_failed += batch_results['failed']
            total_price_changed += batch_results['price_changed']
            total_history_written += batch_results['history_written']
            all_errors.extend(batch_results['errors'])
            
            # 更新 current_log_id 和 max_log_id（使用这批记录中的最大 id）
            batch_max_id = max(record['id'] for record in log_records)
            current_log_id = batch_max_id  # 下次查询从这批的最大 id 开始
            max_log_id = max(max_log_id, batch_max_id)
            
            print(
                f"[sync_processor] 已处理 {total_processed}/{total_pending} 条记录, "
                f"成功={total_success}, 失败={total_failed}, "
                f"价格变化={total_price_changed}, 历史记录={total_history_written}, "
                f"current_log_id={current_log_id}"
            )
            
            # 如果这批记录数小于 batch_size，说明已经处理完所有记录
            if len(log_records) < batch_size:
                break
        
        # 3. 更新 last_log_id（只有在成功处理后才更新）
        if max_log_id > last_log_id:
            update_last_log_id(conn, max_log_id)
            print(f"[sync_processor] 更新 last_log_id: {last_log_id} -> {max_log_id}")
        
        return {
            'total_processed': total_processed,
            'total_success': total_success,
            'total_failed': total_failed,
            'total_price_changed': total_price_changed,
            'total_history_written': total_history_written,
            'last_log_id_before': last_log_id,
            'last_log_id_after': max_log_id,
            'errors': all_errors
        }
        
    except Exception as e:
        raise DatabaseError(f"同步流程失败: {e}")

