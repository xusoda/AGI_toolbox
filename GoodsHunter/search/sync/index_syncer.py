"""索引同步器：从数据库同步到ES"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from search.es_engine import ElasticsearchSearchEngine
from search.data_manager import SearchDataManager

logger = logging.getLogger(__name__)


class IndexSyncer:
    """索引同步器，负责从数据库同步到ES"""
    
    def __init__(self, es_engine: ElasticsearchSearchEngine):
        """
        初始化索引同步器
        
        Args:
            es_engine: ES搜索引擎实例
        """
        self.es_engine = es_engine
        self.data_manager = SearchDataManager(es_engine)
    
    def sync_all(self, session: Session, batch_size: int = 100) -> int:
        """
        全量同步所有商品
        
        Args:
            session: 数据库会话
            batch_size: 批量大小
            
        Returns:
            同步的商品数量
        """
        try:
            logger.info(f"开始全量同步到ES (batch_size={batch_size})")
            count = self.data_manager.sync_from_database(session, batch_size=batch_size)
            # 刷新索引使数据立即可搜索
            self.es_engine.refresh_index()
            logger.info(f"全量同步完成，共同步 {count} 个商品")
            return count
        except Exception as e:
            logger.error(f"全量同步失败: {e}", exc_info=True)
            raise
    
    def sync_items(self, session: Session, item_ids: List[int]) -> int:
        """
        同步指定的商品
        
        Args:
            session: 数据库会话
            item_ids: 商品ID列表
            
        Returns:
            同步的商品数量
        """
        try:
            logger.info(f"开始同步指定商品到ES (count={len(item_ids)})")
            count = self.data_manager.sync_from_database(session, item_ids=item_ids)
            # 刷新索引
            self.es_engine.refresh_index()
            logger.info(f"同步完成，共同步 {count} 个商品")
            return count
        except Exception as e:
            logger.error(f"同步指定商品失败: {e}", exc_info=True)
            raise
    
    def sync_incremental(
        self,
        session: Session,
        last_sync_time: Optional[str] = None,
        batch_size: int = 100
    ) -> int:
        """
        增量同步（基于最后同步时间）
        
        Args:
            session: 数据库会话
            last_sync_time: 最后同步时间（ISO格式字符串），如果为None则同步所有
            batch_size: 批量大小
            
        Returns:
            同步的商品数量
        """
        try:
            if last_sync_time:
                logger.info(f"开始增量同步 (last_sync_time={last_sync_time}, batch_size={batch_size})")
                # 查询最后同步时间之后更新的商品
                sql = """
                    SELECT id
                    FROM crawler_item
                    WHERE updated_at > :last_sync_time
                       OR created_at > :last_sync_time
                    ORDER BY id
                """
                result = session.execute(text(sql), {"last_sync_time": last_sync_time})
                item_ids = [row[0] for row in result]
            else:
                # 如果没有指定时间，同步所有商品
                logger.info(f"开始全量同步 (batch_size={batch_size})")
                item_ids = None
            
            if item_ids is None:
                count = self.sync_all(session, batch_size)
            else:
                count = self.sync_items(session, item_ids)
            
            logger.info(f"增量同步完成，共同步 {count} 个商品")
            return count
        except Exception as e:
            logger.error(f"增量同步失败: {e}", exc_info=True)
            raise
