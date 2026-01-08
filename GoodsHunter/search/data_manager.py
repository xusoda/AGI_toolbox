"""搜索数据管理器"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from search.engine import SearchEngine

logger = logging.getLogger(__name__)


class SearchDataManager:
    """搜索数据管理器
    
    负责将商品数据同步到搜索引擎，提供增量更新和删除功能
    """
    
    def __init__(self, search_engine: SearchEngine):
        """
        初始化搜索数据管理器
        
        Args:
            search_engine: 搜索引擎实例
        """
        self.search_engine = search_engine
    
    def sync_item(self, item_data: Dict[str, Any]) -> bool:
        """
        同步单个商品到搜索引擎
        
        Args:
            item_data: 商品数据字典，包含 id, brand_name, model_name 等字段
        
        Returns:
            bool: 是否成功
        """
        try:
            return self.search_engine.index_document(item_data)
        except Exception as e:
            logger.error(f"同步商品到搜索引擎失败 (item_id={item_data.get('id')}): {e}", exc_info=True)
            return False
    
    def sync_items(self, items_data: List[Dict[str, Any]]) -> int:
        """
        批量同步商品到搜索引擎
        
        Args:
            items_data: 商品数据列表
        
        Returns:
            int: 成功同步的数量
        """
        try:
            return self.search_engine.bulk_index_documents(items_data)
        except Exception as e:
            logger.error(f"批量同步商品到搜索引擎失败: {e}", exc_info=True)
            return 0
    
    def sync_from_database(
        self,
        session: Session,
        batch_size: int = 100,
        item_ids: Optional[List[int]] = None
    ) -> int:
        """
        从数据库同步商品到搜索引擎
        
        Args:
            session: 数据库会话
            item_ids: 可选，指定要同步的商品 ID 列表。如果为 None，则同步所有商品
        
        Returns:
            int: 成功同步的数量
        """
        from sqlalchemy import text
        
        try:
            total_synced = 0
            
            if item_ids:
                # 同步指定的商品
                for item_id in item_ids:
                    item = self._get_item_from_db(session, item_id)
                    if item:
                        item_data = self._item_to_dict(item)
                        if self.sync_item(item_data):
                            total_synced += 1
            else:
                # 批量同步所有商品
                offset = 0
                while True:
                    items = self._get_items_batch(session, offset, batch_size)
                    if not items:
                        break
                    
                    items_data = [self._item_to_dict(item) for item in items]
                    synced = self.sync_items(items_data)
                    total_synced += synced
                    
                    if len(items) < batch_size:
                        break
                    offset += batch_size
                    
                    logger.info(f"已同步 {total_synced} 个商品到搜索引擎")
            
            logger.info(f"同步完成，共同步 {total_synced} 个商品")
            return total_synced
        except Exception as e:
            logger.error(f"从数据库同步商品失败: {e}", exc_info=True)
            return 0
    
    def update_item(self, item_id: int, updated_data: Dict[str, Any]) -> bool:
        """
        更新商品数据
        
        Args:
            item_id: 商品 ID
            updated_data: 更新后的商品数据
        
        Returns:
            bool: 是否成功
        """
        updated_data['id'] = item_id
        return self.sync_item(updated_data)
    
    def delete_item(self, item_id: int) -> bool:
        """
        从搜索引擎中删除商品
        
        Args:
            item_id: 商品 ID
        
        Returns:
            bool: 是否成功
        """
        try:
            return self.search_engine.delete_document(item_id)
        except Exception as e:
            logger.error(f"从搜索引擎删除商品失败 (item_id={item_id}): {e}", exc_info=True)
            return False
    
    def _get_item_from_db(self, session: Session, item_id: int) -> Optional[Any]:
        """从数据库获取单个商品"""
        from sqlalchemy import text
        
        sql = """
            SELECT id, brand_name, model_name, model_no, price, currency,
                   site, category, status, last_seen_dt, image_thumb_300_key,
                   product_url, created_at
            FROM crawler_item
            WHERE id = :item_id
        """
        result = session.execute(text(sql), {"item_id": item_id}).fetchone()
        return result
    
    def _get_items_batch(self, session: Session, offset: int, limit: int) -> List[Any]:
        """批量获取商品"""
        from sqlalchemy import text
        
        sql = """
            SELECT id, brand_name, model_name, model_no, price, currency,
                   site, category, status, last_seen_dt, image_thumb_300_key,
                   product_url, created_at
            FROM crawler_item
            ORDER BY id
            LIMIT :limit OFFSET :offset
        """
        result = session.execute(text(sql), {"limit": limit, "offset": offset})
        return list(result)
    
    def _item_to_dict(self, item: Any) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        return {
            "id": item.id,
            "brand_name": item.brand_name,
            "model_name": item.model_name,
            "model_no": item.model_no,
            "price": item.price,
            "currency": item.currency,
            "site": item.site,
            "category": item.category,
            "status": item.status,
            "last_seen_dt": item.last_seen_dt.isoformat() if item.last_seen_dt else None,
            "image_thumb_300_key": item.image_thumb_300_key,
            "product_url": item.product_url,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
