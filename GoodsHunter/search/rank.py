"""搜索排序模块：实现召回+过滤+排序+重排的逻辑"""
import logging
from typing import Dict, List, Optional, Any
from search.engine import SearchEngine, SearchResult, SearchFilters, SortOption
from search.i18n.alias_resolver import AliasResolver

logger = logging.getLogger(__name__)


class SearchRanker:
    """搜索排序器
    
    实现"召回+过滤+排序+重排"的搜索流程：
    1. 召回（Recall）：使用搜索引擎返回的结果
    2. 过滤（Filter）：当有精准匹配时，仅保留精准匹配的结果
    3. 排序（Sort）：默认按 ES 相关性分数排序
    4. 重排（Rerank）：未来可扩展的重排序逻辑
    """
    
    def __init__(self, search_engine: SearchEngine, category: str = "watch"):
        """
        初始化搜索排序器
        
        Args:
            search_engine: 搜索引擎实例
            category: 商品类别
        """
        self.search_engine = search_engine
        self.category = category
    
    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        sort: Optional[SortOption] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        执行搜索（召回+过滤+排序+重排）
        
        Args:
            query: 搜索关键词
            filters: 搜索过滤器
            sort: 排序选项（如果为 None，则使用 ES 相关性分数排序）
            page: 页码（从1开始）
            page_size: 每页数量
        
        Returns:
            SearchResult: 处理后的搜索结果
        """
        # 步骤1：召回（Recall）
        # 使用搜索引擎返回初始结果（包含更多结果以便后续过滤）
        recall_result = self._recall(query, filters, sort, page, page_size)
        
        if not recall_result.items:
            return recall_result
        
        # 步骤2：过滤（Filter）
        # 当有精准匹配时，仅保留精准匹配的结果
        filtered_items = self._filter(query, recall_result.items)
        
        # 步骤3：排序（Sort）
        # 如果用户未指定排序方式，默认按 ES 相关性分数排序
        sorted_items = self._sort(filtered_items, sort)
        
        # 步骤4：重排（Rerank）
        # 未来可扩展的重排序逻辑（目前直接返回排序后的结果）
        reranked_items = self._rerank(query, sorted_items)
        
        # 分页处理
        total = len(reranked_items)
        offset = (page - 1) * page_size
        paginated_items = reranked_items[offset:offset + page_size]
        
        return SearchResult(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    def _recall(
        self,
        query: str,
        filters: Optional[SearchFilters],
        sort: Optional[SortOption],
        page: int,
        page_size: int
    ) -> SearchResult:
        """
        召回阶段：使用搜索引擎获取初始结果
        
        注意：为了确保过滤后仍有足够的结果，这里会获取更多结果
        （实际分页在最后阶段处理）
        """
        # 如果用户指定了排序方式，在召回阶段就使用该排序方式
        # 如果未指定，则使用相关性排序（ES 默认）
        recall_sort = sort
        
        # 获取更多结果以便后续过滤（最多获取 page_size * 5 的结果）
        recall_page_size = min(page_size * 5, 100)
        
        return self.search_engine.search(
            query=query,
            filters=filters,
            sort=recall_sort,
            page=1,
            page_size=recall_page_size
        )
    
    def _filter(self, query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤阶段：当有精准匹配时，仅保留精准匹配的结果
        
        Args:
            query: 搜索关键词
            items: 召回的结果列表
        
        Returns:
            过滤后的结果列表
        """
        if not query or not query.strip():
            return items
        
        query_clean = query.strip()
        
        # 判断每个结果是否为精准匹配
        exact_matches = []
        non_exact_matches = []
        
        for item in items:
            if self._is_exact_match(query_clean, item):
                exact_matches.append(item)
            else:
                non_exact_matches.append(item)
        
        # 如果有精准匹配，仅返回精准匹配的结果
        if exact_matches:
            logger.debug(f"搜索 '{query_clean}' 找到 {len(exact_matches)} 个精准匹配，过滤掉 {len(non_exact_matches)} 个非精准匹配")
            return exact_matches
        else:
            logger.debug(f"搜索 '{query_clean}' 未找到精准匹配，保留所有 {len(items)} 个结果")
            return items
    
    def _is_exact_match(self, query: str, item: Dict[str, Any]) -> bool:
        """
        判断结果是否为精准匹配
        
        精准匹配的定义：查询词完全匹配以下字段之一（不区分大小写）：
        - brand_name（品牌名）
        - brand_aliases（品牌别名，从索引中获取）
        - model_name（型号名）
        - model_aliases（型号别名，从索引中获取）
        - model_no（型号编号）
        
        Args:
            query: 搜索关键词
            item: 商品项
        
        Returns:
            是否为精准匹配
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return False
        
        # 检查品牌名
        brand_name = item.get("brand_name")
        if brand_name and brand_name.lower().strip() == query_lower:
            return True
        
        # 检查型号名
        model_name = item.get("model_name")
        if model_name and model_name.lower().strip() == query_lower:
            return True
        
        # 检查型号编号
        model_no = item.get("model_no")
        if model_no and str(model_no).lower().strip() == query_lower:
            return True
        
        # 检查品牌别名（优先使用 ES 文档中的别名，否则从别名解析器获取）
        if brand_name:
            brand_aliases = item.get("brand_aliases")
            if not brand_aliases:
                # 如果 ES 文档中没有别名，从别名解析器获取
                try:
                    brand_aliases = AliasResolver.get_brand_aliases(brand_name, self.category)
                except Exception as e:
                    logger.debug(f"获取品牌别名失败 (brand_name={brand_name}): {e}")
                    brand_aliases = []
            
            # 处理别名（可能是列表或字符串）
            alias_list = brand_aliases if isinstance(brand_aliases, list) else [brand_aliases] if brand_aliases else []
            for alias in alias_list:
                if alias and str(alias).lower().strip() == query_lower:
                    return True
        
        # 检查型号别名（优先使用 ES 文档中的别名，否则从别名解析器获取）
        if brand_name and model_name:
            model_aliases = item.get("model_aliases")
            if not model_aliases:
                # 如果 ES 文档中没有别名，从别名解析器获取
                try:
                    model_aliases = AliasResolver.get_model_aliases(brand_name, model_name, self.category)
                except Exception as e:
                    logger.debug(f"获取型号别名失败 (brand_name={brand_name}, model_name={model_name}): {e}")
                    model_aliases = []
            
            # 处理别名（可能是列表或字符串）
            alias_list = model_aliases if isinstance(model_aliases, list) else [model_aliases] if model_aliases else []
            for alias in alias_list:
                if alias and str(alias).lower().strip() == query_lower:
                    return True
        
        return False
    
    def _sort(
        self,
        items: List[Dict[str, Any]],
        sort: Optional[SortOption]
    ) -> List[Dict[str, Any]]:
        """
        排序阶段：对结果进行排序
        
        如果用户未指定排序方式，默认按 ES 相关性分数（_score）降序排序
        如果用户指定了排序方式，则按用户指定的方式排序
        
        Args:
            items: 过滤后的结果列表
            sort: 排序选项
        
        Returns:
            排序后的结果列表
        """
        if not items:
            return items
        
        # 如果用户指定了排序方式，直接返回（因为召回阶段已经按该方式排序）
        if sort:
            return items
        
        # 默认按 ES 相关性分数排序（降序）
        def get_score(item: Dict[str, Any]) -> float:
            score = item.get("_score", 0.0)
            return float(score) if score is not None else 0.0
        
        sorted_items = sorted(items, key=get_score, reverse=True)
        return sorted_items
    
    def _rerank(
        self,
        query: str,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        重排阶段：对结果进行重排序（未来可扩展）
        
        目前直接返回排序后的结果，未来可以在这里实现更复杂的重排序逻辑，
        例如：
        - 基于用户行为的个性化排序
        - 基于商品属性的排序优化
        - 基于多因子模型的排序
        
        Args:
            query: 搜索关键词
            items: 排序后的结果列表
        
        Returns:
            重排后的结果列表
        """
        # 目前直接返回，未来可以在这里实现重排序逻辑
        return items
