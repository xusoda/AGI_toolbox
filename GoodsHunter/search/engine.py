"""搜索引擎抽象接口"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """搜索结果"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


@dataclass
class SearchFilters:
    """搜索过滤器"""
    status: Optional[str] = None
    site: Optional[str] = None
    category: Optional[str] = None
    brand_name: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    currency: Optional[str] = None


@dataclass
class SortOption:
    """排序选项"""
    field: str  # price, last_seen_dt, created_at
    order: str  # asc, desc


class SearchEngine(ABC):
    """搜索引擎抽象基类
    
    定义了搜索引擎的统一接口，支持不同的实现（PostgreSQL、Elasticsearch等）
    """
    
    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        sort: Optional[SortOption] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        执行搜索
        
        Args:
            query: 搜索关键词（支持中英日文）
            filters: 搜索过滤器
            sort: 排序选项
            page: 页码（从1开始）
            page_size: 每页数量
        
        Returns:
            SearchResult: 搜索结果
        """
        pass
    
    @abstractmethod
    def suggest(
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
        pass
    
    @abstractmethod
    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        索引文档（商品）
        
        Args:
            document: 商品文档（包含 id, brand_name, model_name 等字段）
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: int) -> bool:
        """
        删除文档
        
        Args:
            document_id: 商品 ID
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        批量索引文档
        
        Args:
            documents: 商品文档列表
        
        Returns:
            int: 成功索引的数量
        """
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """
        检查搜索引擎是否就绪
        
        Returns:
            bool: 是否就绪
        """
        pass
