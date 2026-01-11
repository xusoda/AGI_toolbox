"""Elasticsearch 搜索引擎实现"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import NotFoundError, RequestError
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    Elasticsearch = None
    NotFoundError = Exception
    RequestError = Exception

from search.engine import SearchEngine, SearchResult, SearchFilters, SortOption
from search.i18n.index_builder import IndexBuilder

logger = logging.getLogger(__name__)


class ElasticsearchSearchEngine(SearchEngine):
    """Elasticsearch 搜索引擎实现
    
    支持多语言搜索，通过别名数组实现跨语言匹配
    """
    
    def __init__(
        self,
        es_host: str = "localhost",
        es_port: int = 9200,
        index_name: str = "products",
        category: str = "watch"
    ):
        """
        初始化 Elasticsearch 搜索引擎
        
        Args:
            es_host: Elasticsearch 主机地址
            es_port: Elasticsearch 端口
            index_name: 索引名称
            category: 商品类别
        """
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("elasticsearch 库未安装，请运行: pip install 'elasticsearch>=8.0.0,<9.0.0'")
        
        self.es_host = es_host
        self.es_port = es_port
        self.index_name = index_name
        self.category = category
        
        # 创建 ES 客户端
        self.es_client = Elasticsearch(
            [f"http://{es_host}:{es_port}"],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # 确保索引存在
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """确保索引存在，如果不存在则创建"""
        try:
            # 先检查索引是否存在，避免不必要的PUT请求
            if self.es_client.indices.exists(index=self.index_name):
                logger.debug(f"ES索引 '{self.index_name}' 已存在")
                return
            
            # 索引不存在，创建索引
            self._create_index()
            logger.info(f"ES索引 '{self.index_name}' 创建成功")
        except RequestError as e:
            error_info = str(e)
            if "resource_already_exists_exception" in error_info:
                # 并发情况下可能同时创建，这里捕获并忽略
                logger.debug(f"ES索引 '{self.index_name}' 已存在（并发创建时）")
            else:
                logger.error(f"创建ES索引失败: {e}")
                raise
        except Exception as e:
            logger.error(f"检查/创建ES索引失败: {e}", exc_info=True)
            raise
    
    def _create_index(self):
        """创建ES索引"""
        mappings = {
            "properties": {
                "id": {"type": "keyword"},
                "brand_name": {
                    "type": "text",
                    "analyzer": "standard",  # 使用标准分析器（如果未安装IK插件）
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "model_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "model_no": {
                    "type": "keyword",
                    "fields": {
                        "text": {"type": "text", "analyzer": "standard"}
                    }
                },
                "brand_aliases": {
                    "type": "text",
                    "analyzer": "standard"  # 存储品牌的多语言别名
                },
                "model_aliases": {
                    "type": "text",
                    "analyzer": "standard"  # 存储型号的多语言别名
                },
                "search_text": {
                    "type": "text",
                    "analyzer": "standard"  # 合并的搜索文本（包含所有同义词）
                },
                "price": {"type": "integer"},
                "currency": {"type": "keyword"},
                "site": {"type": "keyword"},
                "category": {"type": "keyword"},
                "status": {"type": "keyword"},
                "last_seen_dt": {"type": "date"},
                "created_at": {"type": "date"},
                "image_thumb_300_key": {"type": "keyword"},
                "product_url": {"type": "keyword"},
                "suggest": {
                    "type": "completion",
                    "preserve_separators": True,
                    "preserve_position_increments": True,
                    "max_input_length": 50
                }
            }
        }
        
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0  # 开发环境，生产环境建议1
        }
        
        try:
            # ES 8.x 使用直接参数
            self.es_client.indices.create(
                index=self.index_name,
                mappings=mappings,
                settings=settings
            )
        except RequestError as e:
            error_info = str(e)
            if "resource_already_exists_exception" not in error_info:
                logger.error(f"创建索引失败: {e}")
                raise
            logger.info(f"索引 {self.index_name} 已存在")
    
    def is_ready(self) -> bool:
        """检查搜索引擎是否就绪"""
        try:
            return self.es_client.ping()
        except Exception as e:
            logger.error(f"ES连接检查失败: {e}", exc_info=True)
            return False
    
    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        sort: Optional[SortOption] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """执行搜索"""
        try:
            if not query or not query.strip():
                query = "*"
            
            # 构建查询
            es_query = self._build_search_query(query, filters, sort, page, page_size)
            
            # 记录查询日志（DEBUG级别）
            logger.debug(f"搜索查询: query='{query}', ES查询JSON: {json.dumps(es_query, ensure_ascii=False)}")
            
            # 执行搜索（ES 8.x 使用 body 参数）
            response = self.es_client.search(index=self.index_name, body=es_query)
            
            # 解析结果
            total = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            # 记录查询结果（DEBUG级别）
            logger.debug(f"搜索查询完成: query='{query}', 返回 {total} 个结果")
            
            items = []
            for hit in hits:
                source = hit["_source"]
                item = {
                    "id": source.get("id"),
                    "brand_name": source.get("brand_name"),
                    "model_name": source.get("model_name"),
                    "model_no": source.get("model_no"),
                    "price": source.get("price"),
                    "currency": source.get("currency"),
                    "site": source.get("site"),
                    "category": source.get("category"),
                    "status": source.get("status"),
                    "last_seen_dt": source.get("last_seen_dt"),
                    "image_thumb_300_key": source.get("image_thumb_300_key"),
                    "product_url": source.get("product_url"),
                    "created_at": source.get("created_at"),
                }
                # 添加 ES 相关性分数（用于排序和重排）
                if "_score" in hit:
                    item["_score"] = hit["_score"]
                # 添加别名字段（用于精准匹配判断，可选）
                brand_aliases = source.get("brand_aliases")
                if brand_aliases:
                    item["brand_aliases"] = brand_aliases
                model_aliases = source.get("model_aliases")
                if model_aliases:
                    item["model_aliases"] = model_aliases
                items.append(item)
            
            return SearchResult(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error(f"ES搜索失败: {e}", exc_info=True)
            raise
    
    def _build_search_query(
        self,
        query: str,
        filters: Optional[SearchFilters],
        sort: Optional[SortOption],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """构建ES查询"""
        offset = (page - 1) * page_size
        
        # 构建搜索条件
        should_clauses = []
        
        if query != "*":
            # 多字段匹配（支持多语言搜索）
            should_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "brand_name^3",           # 品牌名权重最高
                        "brand_aliases^2.5",      # 品牌别名权重次之
                        "model_name^2",           # 型号名权重
                        "model_aliases^1.5",      # 型号别名权重
                        "search_text^1",          # 合并搜索文本权重最低
                        "model_no^1"              # 型号编号
                    ],
                    "type": "best_fields",
                    "operator": "or",
                    "fuzziness": "AUTO"  # 支持模糊匹配
                }
            })
        
        # 构建bool查询
        bool_query = {
            "bool": {
                "should": should_clauses if should_clauses else [{"match_all": {}}],
                "minimum_should_match": 1 if query != "*" else 0
            }
        }
        
        # 添加过滤器
        filter_clauses = []
        if filters:
            if filters.status:
                filter_clauses.append({"term": {"status": filters.status}})
            if filters.site:
                filter_clauses.append({"term": {"site": filters.site}})
            if filters.category:
                filter_clauses.append({"term": {"category": filters.category}})
            if filters.brand_name:
                filter_clauses.append({"term": {"brand_name.keyword": filters.brand_name}})
            if filters.min_price is not None:
                filter_clauses.append({"range": {"price": {"gte": filters.min_price}}})
            if filters.max_price is not None:
                filter_clauses.append({"range": {"price": {"lte": filters.max_price}}})
            if filters.currency:
                filter_clauses.append({"term": {"currency": filters.currency}})
        
        if filter_clauses:
            bool_query["bool"]["filter"] = filter_clauses
        
        # 构建排序
        sort_clauses = []
        if sort:
            if sort.field == "price":
                sort_clauses.append({"price": {"order": sort.order}})
            elif sort.field == "last_seen_dt":
                sort_clauses.append({"last_seen_dt": {"order": sort.order}})
            elif sort.field == "created_at":
                sort_clauses.append({"created_at": {"order": sort.order}})
            else:
                # 默认按相关性排序
                sort_clauses.append({"_score": {"order": "desc"}})
        else:
            # 默认排序：最后发现时间倒序
            sort_clauses.append({"last_seen_dt": {"order": "desc"}})
        
        # 如果没有指定排序字段，添加相关性排序
        if not any("_score" in s for s in sort_clauses) and query != "*":
            sort_clauses.append({"_score": {"order": "desc"}})
        
        # 构建完整查询
        es_query = {
            "query": bool_query,
            "sort": sort_clauses,
            "from": offset,
            "size": page_size
        }
        
        return es_query
    
    def suggest(
        self,
        query: str,
        size: int = 5
    ) -> List[str]:
        """获取搜索建议（使用prefix查询，支持中文前缀匹配）"""
        if not query or not query.strip():
            return []
        
        try:
            query_clean = query.strip()
            
            # 使用match_phrase_prefix查询替代Completion Suggester，以更好地支持中文前缀匹配
            # match_phrase_prefix适用于text字段，支持分词后的前缀匹配
            es_query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match_phrase_prefix": {"brand_name": {"query": query_clean, "max_expansions": 50}}},
                            {"match_phrase_prefix": {"brand_aliases": {"query": query_clean, "max_expansions": 50}}},
                            {"match_phrase_prefix": {"model_name": {"query": query_clean, "max_expansions": 50}}},
                            {"match_phrase_prefix": {"model_aliases": {"query": query_clean, "max_expansions": 50}}},
                            {"match_phrase_prefix": {"search_text": {"query": query_clean, "max_expansions": 50}}},
                            {"prefix": {"model_no": query_clean}}  # model_no是keyword类型
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": size * 5,  # 获取更多结果以便去重
                "_source": ["brand_name", "model_name", "model_no", "brand_aliases", "model_aliases"]
            }
            
            response = self.es_client.search(index=self.index_name, body=es_query)
            
            # 从返回的文档中提取建议词条
            suggestions = []
            seen = set()
            
            hits = response["hits"]["hits"]
            for hit in hits:
                source = hit["_source"]
                
                # 收集所有可能匹配的词条
                candidate_terms = []
                
                # 添加品牌名
                if source.get("brand_name"):
                    candidate_terms.append(source["brand_name"])
                
                # 添加型号名
                if source.get("model_name"):
                    candidate_terms.append(source["model_name"])
                
                # 添加型号编号
                if source.get("model_no"):
                    candidate_terms.append(source["model_no"])
                
                # 添加品牌别名
                brand_aliases = source.get("brand_aliases", [])
                if isinstance(brand_aliases, list):
                    candidate_terms.extend(brand_aliases)
                elif isinstance(brand_aliases, str):
                    candidate_terms.append(brand_aliases)
                
                # 添加型号别名
                model_aliases = source.get("model_aliases", [])
                if isinstance(model_aliases, list):
                    candidate_terms.extend(model_aliases)
                elif isinstance(model_aliases, str):
                    candidate_terms.append(model_aliases)
                
                # 检查每个词条是否以查询前缀开头
                for term in candidate_terms:
                    if term and term not in seen:
                        # 对于中英文混合，使用大小写不敏感的匹配
                        term_lower = term.lower() if isinstance(term, str) else str(term).lower()
                        query_lower = query_clean.lower()
                        
                        if term_lower.startswith(query_lower):
                            suggestions.append(term)
                            seen.add(term)
                            
                            # 如果已经收集到足够的建议，提前返回
                            if len(suggestions) >= size:
                                return suggestions[:size]
            
            return suggestions[:size]
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}", exc_info=True)
            return []
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """索引文档"""
        try:
            # 使用 IndexBuilder 构建包含多语言同义词的文档
            es_doc = IndexBuilder.build_document(document, self.category)
            
            doc_id = str(es_doc.get("id"))
            if not doc_id:
                logger.warning(f"文档ID为空，跳过索引: {document}")
                return False
            
            self.es_client.index(
                index=self.index_name,
                id=doc_id,
                document=es_doc,
                refresh=False  # 不立即刷新，提高性能
            )
            
            return True
        except Exception as e:
            logger.error(f"索引文档失败 (document_id={document.get('id')}): {e}", exc_info=True)
            return False
    
    def delete_document(self, document_id: int) -> bool:
        """删除文档"""
        try:
            self.es_client.delete(
                index=self.index_name,
                id=str(document_id),
                refresh=False
            )
            return True
        except NotFoundError:
            logger.warning(f"文档不存在 (document_id={document_id})")
            return True  # 文档不存在视为成功
        except Exception as e:
            logger.error(f"删除文档失败 (document_id={document_id}): {e}", exc_info=True)
            return False
    
    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """批量索引文档"""
        if not documents:
            return 0
        
        try:
            actions = []
            for doc in documents:
                # 使用 IndexBuilder 构建文档
                es_doc = IndexBuilder.build_document(doc, self.category)
                doc_id = str(es_doc.get("id"))
                if not doc_id:
                    continue
                
                actions.append({
                    "_index": self.index_name,
                    "_id": doc_id,
                    "_source": es_doc
                })
            
            if not actions:
                return 0
            
            # 使用 bulk API
            from elasticsearch.helpers import bulk
            success_count, failed_items = bulk(
                self.es_client,
                actions,
                refresh=False,
                raise_on_error=False
            )
            
            if failed_items:
                logger.warning(f"批量索引有 {len(failed_items)} 个文档失败")
            
            return success_count
        except Exception as e:
            logger.error(f"批量索引文档失败: {e}", exc_info=True)
            return 0
    
    def refresh_index(self):
        """刷新索引（使索引立即可搜索）"""
        try:
            self.es_client.indices.refresh(index=self.index_name)
        except Exception as e:
            logger.error(f"刷新索引失败: {e}", exc_info=True)
    
    def close(self):
        """关闭连接"""
        # ES客户端不需要显式关闭，但可以添加清理逻辑
        pass
