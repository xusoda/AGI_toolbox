"""PostgreSQL 搜索引擎实现"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
from search.engine import SearchEngine, SearchResult, SearchFilters, SortOption

logger = logging.getLogger(__name__)


class PostgresSearchEngine(SearchEngine):
    """PostgreSQL 全文搜索引擎实现
    
    使用 PostgreSQL 的全文搜索功能（tsvector/tsquery）实现搜索
    支持中文、英文、日文搜索
    """
    
    def __init__(self, database_url: str, session: Optional[Session] = None):
        """
        初始化 PostgreSQL 搜索引擎
        
        Args:
            database_url: 数据库连接 URL
            session: 可选的数据库会话（如果不提供，会创建新连接）
        """
        self.database_url = database_url
        self.session = session
        self._engine = None
        if not session:
            self._engine = create_engine(database_url, pool_pre_ping=True)
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session:
            return self.session
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=self._engine)
        return SessionLocal()
    
    def _close_session(self, session: Session):
        """关闭会话（如果不是外部提供的）"""
        if not self.session and session:
            session.close()
    
    def is_ready(self) -> bool:
        """检查搜索引擎是否就绪"""
        try:
            session = self._get_session()
            try:
                session.execute(text("SELECT 1"))
                return True
            finally:
                self._close_session(session)
        except Exception as e:
            logger.error(f"PostgreSQL 搜索引擎未就绪: {e}")
            return False
    
    def _build_search_vector(self, brand_name: str, model_name: str, model_no: str) -> str:
        """
        构建搜索向量（tsvector）
        
        将品牌名、型号名、型号编号组合成搜索向量
        使用 'simple' 配置，支持中英日文
        """
        # 清理并组合文本
        texts = []
        if brand_name:
            texts.append(brand_name)
        if model_name:
            texts.append(model_name)
        if model_no:
            texts.append(model_no)
        
        combined = " ".join(texts)
        if not combined.strip():
            return ""
        
        # 使用 to_tsvector 创建搜索向量
        # 'simple' 配置对中英日文都有较好的支持
        # 对于中文，PostgreSQL 需要安装 zhparser 扩展才能更好地分词
        # 但即使没有扩展，也可以进行基本的文本匹配
        return f"to_tsvector('simple', {combined!r})"
    
    def _build_tsquery(self, query: str) -> str:
        """
        构建 tsquery
        
        将搜索关键词转换为 PostgreSQL 的 tsquery 格式
        支持多关键词（用空格分隔）
        """
        if not query or not query.strip():
            return ""
        
        # 清理查询字符串
        query = query.strip()
        
        # 将多个关键词用 & 连接（AND 关系）
        # 也可以使用 | 连接（OR 关系），这里使用 AND 更严格
        keywords = query.split()
        if not keywords:
            return ""
        
        # 对每个关键词进行转义和格式化
        formatted_keywords = []
        for keyword in keywords:
            # 转义特殊字符
            keyword = keyword.replace("'", "''")
            # 使用 :* 支持前缀匹配（用于建议功能）
            formatted_keywords.append(f"{keyword}:*")
        
        # 使用 & 连接（AND 关系）
        tsquery_str = " & ".join(formatted_keywords)
        
        # 使用 plainto_tsquery 可以更好地处理自然语言查询
        return f"plainto_tsquery('simple', {tsquery_str!r})"
    
    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        sort: Optional[SortOption] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """执行搜索"""
        session = self._get_session()
        try:
            # 构建基础查询
            sql_parts = [
                "SELECT id, brand_name, model_name, model_no, price, currency,",
                "site, category, status, last_seen_dt, image_thumb_300_key,",
                "product_url, created_at",
                "FROM crawler_item",
                "WHERE 1=1"
            ]
            params = {}
            
            # 添加搜索条件
            if query and query.strip():
                # 使用全文搜索
                # 构建搜索向量（如果表中有 search_vector 列）或使用动态计算
                # 这里我们使用动态计算的方式，因为可能还没有 search_vector 列
                search_condition = """
                    (
                        to_tsvector('simple', COALESCE(brand_name, '') || ' ' || 
                                   COALESCE(model_name, '') || ' ' || 
                                   COALESCE(model_no, '')) 
                        @@ plainto_tsquery('simple', :query)
                        OR brand_name ILIKE :query_like
                        OR model_name ILIKE :query_like
                        OR model_no ILIKE :query_like
                    )
                """
                sql_parts.append(f"AND ({search_condition})")
                params['query'] = query
                params['query_like'] = f"%{query}%"
            
            # 添加过滤器
            if filters:
                if filters.status:
                    sql_parts.append("AND status = :status")
                    params['status'] = filters.status
                if filters.site:
                    sql_parts.append("AND site = :site")
                    params['site'] = filters.site
                if filters.category:
                    sql_parts.append("AND category = :category")
                    params['category'] = filters.category
                if filters.brand_name:
                    sql_parts.append("AND brand_name = :brand_name")
                    params['brand_name'] = filters.brand_name
                if filters.min_price is not None:
                    sql_parts.append("AND price >= :min_price")
                    params['min_price'] = filters.min_price
                if filters.max_price is not None:
                    sql_parts.append("AND price <= :max_price")
                    params['max_price'] = filters.max_price
                if filters.currency:
                    sql_parts.append("AND currency = :currency")
                    params['currency'] = filters.currency
            
            # 添加排序
            if sort:
                if sort.field == "price":
                    order = "ASC" if sort.order == "asc" else "DESC"
                    sql_parts.append(f"ORDER BY price {order} NULLS LAST")
                elif sort.field == "last_seen_dt":
                    order = "ASC" if sort.order == "asc" else "DESC"
                    sql_parts.append(f"ORDER BY last_seen_dt {order}")
                elif sort.field == "created_at":
                    order = "ASC" if sort.order == "asc" else "DESC"
                    sql_parts.append(f"ORDER BY created_at {order}")
                else:
                    # 默认按相关性排序（如果有搜索关键词）
                    if query and query.strip():
                        sql_parts.append("ORDER BY last_seen_dt DESC")
                    else:
                        sql_parts.append("ORDER BY last_seen_dt DESC")
            else:
                # 默认排序
                if query and query.strip():
                    # 有搜索关键词时，可以按相关性排序
                    # 这里简化处理，按最后发现时间倒序
                    sql_parts.append("ORDER BY last_seen_dt DESC")
                else:
                    sql_parts.append("ORDER BY last_seen_dt DESC")
            
            # 获取总数
            count_sql = "SELECT COUNT(*) as total FROM (" + " ".join(sql_parts) + ") as subquery"
            count_result = session.execute(text(count_sql), params).fetchone()
            total = count_result[0] if count_result else 0
            
            # 添加分页
            offset = (page - 1) * page_size
            sql_parts.append("LIMIT :limit OFFSET :offset")
            params['limit'] = page_size
            params['offset'] = offset
            
            # 执行查询
            final_sql = " ".join(sql_parts)
            result = session.execute(text(final_sql), params)
            
            # 转换为字典列表
            items = []
            for row in result:
                items.append({
                    "id": row.id,
                    "brand_name": row.brand_name,
                    "model_name": row.model_name,
                    "model_no": row.model_no,
                    "price": row.price,
                    "currency": row.currency,
                    "site": row.site,
                    "category": row.category,
                    "status": row.status,
                    "last_seen_dt": row.last_seen_dt.isoformat() if row.last_seen_dt else None,
                    "image_thumb_300_key": row.image_thumb_300_key,
                    "product_url": row.product_url,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
            
            return SearchResult(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error(f"搜索失败: {e}", exc_info=True)
            raise
        finally:
            self._close_session(session)
    
    def suggest(
        self,
        query: str,
        size: int = 5
    ) -> List[str]:
        """获取搜索建议"""
        if not query or not query.strip():
            return []
        
        session = self._get_session()
        try:
            query_clean = query.strip()
            query_like = f"{query_clean}%"
            
            # 从品牌名、型号名、型号编号中查找匹配的建议
            sql = """
                SELECT DISTINCT suggestion
                FROM (
                    SELECT brand_name as suggestion FROM crawler_item 
                    WHERE brand_name ILIKE :query_like AND brand_name IS NOT NULL
                    UNION
                    SELECT model_name as suggestion FROM crawler_item 
                    WHERE model_name ILIKE :query_like AND model_name IS NOT NULL
                    UNION
                    SELECT model_no as suggestion FROM crawler_item 
                    WHERE model_no ILIKE :query_like AND model_no IS NOT NULL
                ) as suggestions
                ORDER BY suggestion
                LIMIT :size
            """
            
            result = session.execute(
                text(sql),
                {"query_like": query_like, "size": size}
            )
            
            suggestions = [row[0] for row in result if row[0]]
            return suggestions[:size]
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}", exc_info=True)
            return []
        finally:
            self._close_session(session)
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """索引文档（对于 PostgreSQL，数据已经在表中，这里主要是更新搜索向量）"""
        # PostgreSQL 实现中，数据已经在 crawler_item 表中
        # 如果需要优化，可以在这里更新 search_vector 列
        # 目前先简单返回 True，表示成功
        return True
    
    def delete_document(self, document_id: int) -> bool:
        """删除文档（对于 PostgreSQL，数据删除由业务逻辑处理）"""
        # PostgreSQL 实现中，删除操作由业务逻辑处理
        # 这里只是标记接口，实际不需要操作
        return True
    
    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """批量索引文档"""
        # PostgreSQL 实现中，数据已经在表中
        # 这里可以用于批量更新搜索向量等优化操作
        return len(documents)
    
    def close(self):
        """关闭连接"""
        if self._engine:
            self._engine.dispose()
