"""搜索服务层"""
import logging
from typing import List, Optional, Dict, Any
from search.engine import SearchEngine, SearchResult, SearchFilters, SortOption
from search.data_manager import SearchDataManager

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务层
    
    封装搜索业务逻辑，提供统一的搜索接口
    """
    
    def __init__(self, search_engine: SearchEngine):
        """
        初始化搜索服务
        
        Args:
            search_engine: 搜索引擎实例
        """
        self.search_engine = search_engine
        self.data_manager = SearchDataManager(search_engine)
    
    def search_products(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        sort: Optional[SortOption] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        搜索商品
        
        Args:
            query: 搜索关键词（支持中英日文）
            filters: 搜索过滤器
            sort: 排序选项
            page: 页码（从1开始）
            page_size: 每页数量
        
        Returns:
            SearchResult: 搜索结果
        """
        try:
            return self.search_engine.search(
                query=query,
                filters=filters,
                sort=sort,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error(f"搜索商品失败: {e}", exc_info=True)
            raise
    
    def suggest_products(
        self,
        query: str,
        size: int = 5
    ) -> List[str]:
        """
        获取搜索建议（SUG）
        
        Args:
            query: 搜索关键词前缀
            size: 返回建议数量
        
        Returns:
            List[str]: 建议列表
        """
        try:
            return self.search_engine.suggest(query=query, size=size)
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}", exc_info=True)
            return []
    
    def update_product(self, item_id: int, updated_data: Dict[str, Any]) -> bool:
        """
        更新商品数据
        
        Args:
            item_id: 商品 ID
            updated_data: 更新后的商品数据
        
        Returns:
            bool: 是否成功
        """
        return self.data_manager.update_item(item_id, updated_data)
    
    def delete_product(self, item_id: int) -> bool:
        """
        删除商品数据
        
        Args:
            item_id: 商品 ID
        
        Returns:
            bool: 是否成功
        """
        return self.data_manager.delete_item(item_id)
    
    def sync_product(self, item_data: Dict[str, Any]) -> bool:
        """
        同步商品到搜索引擎
        
        Args:
            item_data: 商品数据
        
        Returns:
            bool: 是否成功
        """
        return self.data_manager.sync_item(item_data)
