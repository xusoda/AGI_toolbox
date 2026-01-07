"""入口脚本：命令行接口和定时任务支持"""
import os
import sys
import argparse
import time
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(_project_root / ".env")
except ImportError:
    # 如果 python-dotenv 未安装，跳过（使用系统环境变量）
    pass

from item_extract.utils import get_db_connection, create_connection_pool
from item_extract.models import create_tables
from item_extract.sync_processor import run_sync
from item_extract.exceptions import DatabaseError, ItemExtractError


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def init_database(database_url: Optional[str] = None):
    """
    初始化数据库表（如果不存在）
    
    Args:
        database_url: 数据库连接URL，如果为None则从环境变量读取
    """
    try:
        conn = get_db_connection(database_url)
        try:
            create_tables(conn)
            logger.info("数据库表初始化完成")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def run_once(
    database_url: Optional[str] = None,
    batch_size: int = 100,
    max_records: Optional[int] = None
):
    """
    运行一次同步
    
    Args:
        database_url: 数据库连接URL
        batch_size: 批量大小
        max_records: 最大处理记录数
    """
    conn = None
    try:
        conn = get_db_connection(database_url)
        results = run_sync(conn, batch_size=batch_size, max_records=max_records)
        
        logger.info("=" * 60)
        logger.info("同步完成")
        logger.info(f"总处理数: {results['total_processed']}")
        logger.info(f"成功: {results['total_success']}")
        logger.info(f"失败: {results['total_failed']}")
        logger.info(f"价格变化: {results['total_price_changed']}")
        logger.info(f"历史记录: {results['total_history_written']}")
        logger.info(f"last_log_id: {results['last_log_id_before']} -> {results['last_log_id_after']}")
        
        if results['errors']:
            logger.warning(f"错误数: {len(results['errors'])}")
            for error in results['errors'][:10]:  # 只显示前10个错误
                logger.warning(f"  错误: {error}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"同步失败: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def run_continuous(
    database_url: Optional[str] = None,
    batch_size: int = 100,
    interval: int = 60
):
    """
    持续运行模式（定期轮询）
    
    Args:
        database_url: 数据库连接URL
        batch_size: 批量大小
        interval: 轮询间隔（秒）
    """
    logger.info(f"启动持续运行模式，轮询间隔: {interval} 秒")
    
    try:
        while True:
            try:
                run_once(database_url, batch_size=batch_size)
            except Exception as e:
                logger.error(f"本次同步失败: {e}", exc_info=True)
            
            logger.info(f"等待 {interval} 秒后继续...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，退出")
    except Exception as e:
        logger.error(f"持续运行模式失败: {e}", exc_info=True)
        raise


def main():
    """主函数：解析命令行参数并执行"""
    parser = argparse.ArgumentParser(
        description='Item Extract: 从 crawler_log 提取 item 到 item 表，并记录变更历史'
    )
    
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='数据库连接URL（默认从环境变量 DATABASE_URL 读取）'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='批量处理大小（默认: 100）'
    )
    
    parser.add_argument(
        '--max-records',
        type=int,
        default=None,
        help='最大处理记录数（默认: 不限制）'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='只运行一次（默认: 持续运行）'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='持续运行模式的轮询间隔（秒，默认: 60）'
    )
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='初始化数据库表（如果不存在）'
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化数据库（如果需要）
        if args.init_db:
            logger.info("初始化数据库表...")
            init_database(args.database_url)
        
        # 运行同步
        if args.once:
            run_once(
                database_url=args.database_url,
                batch_size=args.batch_size,
                max_records=args.max_records
            )
        else:
            run_continuous(
                database_url=args.database_url,
                batch_size=args.batch_size,
                interval=args.interval
            )
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，退出")
        sys.exit(0)
    except ItemExtractError as e:
        logger.error(f"Item Extract 错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"未预期的错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

