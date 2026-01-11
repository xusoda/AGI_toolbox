"""别名更新器：词表更新时更新索引"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from search.es_engine import ElasticsearchSearchEngine
from search.sync.index_syncer import IndexSyncer

logger = logging.getLogger(__name__)


class AliasUpdater:
    """别名更新器，负责在词表更新时更新索引"""
    
    def __init__(self, es_engine: ElasticsearchSearchEngine):
        """
        初始化别名更新器
        
        Args:
            es_engine: ES搜索引擎实例
        """
        self.es_engine = es_engine
        self.index_syncer = IndexSyncer(es_engine)
    
    def update_affected_items(
        self,
        session: Session,
        updated_brands: Optional[List[str]] = None,
        updated_models: Optional[Dict[str, List[str]]] = None
    ) -> int:
        """
        更新受影响的商品（增量更新）
        
        Args:
            session: 数据库会话
            updated_brands: 更新的品牌列表（标准品牌名）
            updated_models: 更新的型号字典 {brand: [models]}（标准品牌名和型号名）
        
        Returns:
            更新的商品数量
        """
        try:
            # 查找受影响的商品ID
            affected_item_ids = self._find_affected_items(session, updated_brands, updated_models)
            
            if not affected_item_ids:
                logger.info("没有受影响的商品，无需更新")
                return 0
            
            logger.info(f"找到 {len(affected_item_ids)} 个受影响的商品，开始更新索引")
            
            # 重新索引这些商品
            count = self.index_syncer.sync_items(session, affected_item_ids)
            
            logger.info(f"别名更新完成，更新 {count} 个商品")
            return count
        except Exception as e:
            logger.error(f"更新受影响的商品失败: {e}", exc_info=True)
            raise
    
    def rebuild_all(self, session: Session, batch_size: int = 100) -> int:
        """
        全量重建索引
        
        Args:
            session: 数据库会话
            batch_size: 批量大小
            
        Returns:
            更新的商品数量
        """
        try:
            logger.info("开始全量重建索引")
            count = self.index_syncer.sync_all(session, batch_size)
            logger.info(f"全量重建完成，更新 {count} 个商品")
            return count
        except Exception as e:
            logger.error(f"全量重建索引失败: {e}", exc_info=True)
            raise
    
    def _find_affected_items(
        self,
        session: Session,
        updated_brands: Optional[List[str]],
        updated_models: Optional[Dict[str, List[str]]]
    ) -> List[int]:
        """
        查找受影响的商品ID
        
        Args:
            session: 数据库会话
            updated_brands: 更新的品牌列表
            updated_models: 更新的型号字典 {brand: [models]}
        
        Returns:
            受影响的商品ID列表
        """
        try:
            item_ids = set()
            
            # 处理更新的品牌
            if updated_brands:
                placeholders = ",".join([f":brand_{i}" for i in range(len(updated_brands))])
                params = {f"brand_{i}": brand for i, brand in enumerate(updated_brands)}
                sql = f"""
                    SELECT id
                    FROM crawler_item
                    WHERE brand_name IN ({placeholders})
                """
                result = session.execute(text(sql), params)
                item_ids.update(row[0] for row in result)
            
            # 处理更新的型号
            if updated_models:
                for brand_name, model_names in updated_models.items():
                    if not model_names:
                        continue
                    placeholders = ",".join([f":model_{i}" for i in range(len(model_names))])
                    params = {
                        "brand_name": brand_name,
                        **{f"model_{i}": model for i, model in enumerate(model_names)}
                    }
                    sql = f"""
                        SELECT id
                        FROM crawler_item
                        WHERE brand_name = :brand_name
                          AND model_name IN ({placeholders})
                    """
                    result = session.execute(text(sql), params)
                    item_ids.update(row[0] for row in result)
            
            return sorted(list(item_ids))
        except Exception as e:
            logger.error(f"查找受影响的商品失败: {e}", exc_info=True)
            raise
