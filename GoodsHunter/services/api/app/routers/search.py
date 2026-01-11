"""搜索相关路由"""
import logging
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.search import SearchResponse, SuggestResponse
from app.services.images import image_service, get_image_service
from app.settings import settings
from enums.business.category import Category
from enums.business.status import ItemStatus
from enums.display.lang import LanguageCode
from enums.trade.currency import CurrencyCode
from enums.display.sort import SortField, SortOrder

# 添加项目根目录到路径（为了导入 search 和 enums 模块）
# 在 Docker 容器中，路径结构是：
# /app (services/api)
# /app/../search (项目根目录下的 search) - 挂载为 /app/../search
# /app/../i18n (项目根目录下的 i18n)
# /app/../enums (项目根目录下的 enums)
# /app/../storage (项目根目录下的 storage)

# 注意：不要使用 resolve()，因为它会规范化路径，/app/.. 会变成 /，可能导致路径查找失败或阻塞
# 直接使用字符串路径或 Path 对象，不调用 resolve()

possible_roots = [
    Path(__file__).parent.parent.parent.parent.parent,  # 从 services/api/app/routers/search.py 向上5级到 GoodsHunter
    Path(__file__).parent.parent.parent.parent,  # 从 services/api/app/routers/search.py 向上4级
    Path("/app").parent,  # Docker 容器中，/app 的父目录（不使用 resolve）
]

# 查找项目根目录并添加到 sys.path
project_root = None

# 方法1: 通过 enums 目录定位（最可靠，因为这是必需的）
for root in possible_roots:
    try:
        enums_path = root / "enums"
        if enums_path.exists() and enums_path.is_dir():
            project_root = str(root.absolute() if hasattr(root, 'absolute') else root)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                print(f"[Search] 通过 enums 目录找到项目根目录: {project_root}")
            break
    except (OSError, PermissionError) as e:
        print(f"[Search] 检查路径 {root} 时出错: {e}")
        continue

# 方法2: 如果还没找到，尝试通过 search 目录定位
if project_root is None:
    possible_search_paths = [
        Path("/app").parent / "search",  # Docker 环境（不使用 resolve）
        Path(__file__).parent.parent.parent.parent.parent / "search",  # 本地开发环境
        Path(__file__).parent.parent.parent.parent / "search",  # 本地开发环境（备用）
    ]
    
    for search_path in possible_search_paths:
        try:
            if search_path.exists() and search_path.is_dir():
                project_root = str((search_path.parent).absolute() if hasattr(search_path.parent, 'absolute') else search_path.parent)
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                    print(f"[Search] 通过 search 目录找到项目根目录: {project_root}")
                break
        except (OSError, PermissionError) as e:
            print(f"[Search] 检查路径失败 {search_path}: {e}")
            continue

if project_root is None:
    print(f"[Search] 警告: 未找到项目根目录")
    print(f"[Search] 当前工作目录: {Path.cwd()}")
    print(f"[Search] Python 路径: {sys.path}")

# 导入搜索模块
try:
    from search.es_engine import ElasticsearchSearchEngine
    from search.service import SearchService
    from search.rank import SearchRanker
    from search.engine import SearchFilters, SortOption
    SEARCH_AVAILABLE = True
except ImportError as e:
    SEARCH_AVAILABLE = False
    # 定义占位类型，避免类型检查错误
    SearchService = None
    SearchRanker = None
    ElasticsearchSearchEngine = None
    SearchFilters = None
    SortOption = None
    logging.warning(f"搜索模块不可用: {e}")

logger = logging.getLogger(__name__)

router = APIRouter()

# 缓存搜索服务实例（单例模式，避免每次请求都创建新实例）
_search_service_cache = None
_search_ranker_cache = None


def get_search_service(db: Session = Depends(get_db)):
    """获取搜索服务实例（依赖注入，使用单例模式）
    
    注意：搜索功能现在使用 SearchRanker，但 SearchService 仍用于其他功能（如 suggest）
    """
    global _search_service_cache
    
    if not SEARCH_AVAILABLE:
        raise HTTPException(status_code=503, detail="搜索功能不可用")
    
    # 如果已有缓存实例，直接返回
    if _search_service_cache is not None:
        return _search_service_cache
    
    try:
        # 确保导入（防止延迟导入问题）
        from search.es_engine import ElasticsearchSearchEngine
        from search.service import SearchService
        
        # 创建 Elasticsearch 搜索引擎实例（只创建一次）
        search_engine = ElasticsearchSearchEngine(
            es_host=settings.ES_HOST,
            es_port=settings.ES_PORT,
            index_name=settings.ES_INDEX_NAME
        )
        search_service = SearchService(search_engine)
        
        # 缓存实例
        _search_service_cache = search_service
        logger.info("搜索服务实例已创建并缓存")
        
        return search_service
    except Exception as e:
        logger.error(f"初始化搜索服务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索服务初始化失败: {e}")


def get_search_ranker(db: Session = Depends(get_db)):
    """获取搜索排序器实例（依赖注入，使用单例模式）
    
    用于执行搜索，实现召回+过滤+排序+重排的逻辑
    """
    global _search_ranker_cache
    
    if not SEARCH_AVAILABLE:
        raise HTTPException(status_code=503, detail="搜索功能不可用")
    
    # 如果已有缓存实例，直接返回
    if _search_ranker_cache is not None:
        return _search_ranker_cache
    
    try:
        # 确保导入（防止延迟导入问题）
        from search.es_engine import ElasticsearchSearchEngine
        from search.rank import SearchRanker
        
        # 创建 Elasticsearch 搜索引擎实例（只创建一次）
        search_engine = ElasticsearchSearchEngine(
            es_host=settings.ES_HOST,
            es_port=settings.ES_PORT,
            index_name=settings.ES_INDEX_NAME
        )
        # 创建搜索排序器（默认使用 watch 类别）
        search_ranker = SearchRanker(search_engine, category="watch")
        
        # 缓存实例
        _search_ranker_cache = search_ranker
        logger.info("搜索排序器实例已创建并缓存")
        
        return search_ranker
    except Exception as e:
        logger.error(f"初始化搜索排序器失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索排序器初始化失败: {e}")


@router.get("/search", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., description="搜索关键词（支持中英日文）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: Optional[str] = Query(SortField.get_default(), description=f"排序字段（{'/'.join([s.value for s in SortField])}），默认 {SortField.get_default()}"),
    sort_order: Optional[str] = Query(SortOrder.get_default(), description=f"排序方向（{'/'.join([s.value for s in SortOrder])}），默认 {SortOrder.get_default()}"),
    status: Optional[str] = Query(None, description=f"商品状态（{'/'.join(ItemStatus.all_values())}）"),
    site: Optional[str] = Query(None, description="站点域名"),
    category: Optional[str] = Query(None, description=f"商品类别（{'/'.join(Category.all_values())}）"),
    brand_name: Optional[str] = Query(None, description="品牌名称"),
    min_price: Optional[int] = Query(None, description="最低价格"),
    max_price: Optional[int] = Query(None, description="最高价格"),
    currency: Optional[str] = Query(None, description=f"货币单位（{'/'.join(CurrencyCode.all_values())}）"),
    lang: Optional[str] = Query(LanguageCode.get_default(), description=f"语言代码（{'/'.join(LanguageCode.all_values())}），默认 {LanguageCode.get_default()}"),
    db: Session = Depends(get_db),
    search_ranker = Depends(get_search_ranker)
):
    """
    搜索商品
    
    使用 SearchRanker 实现召回+过滤+排序+重排的搜索流程
    
    - **q**: 搜索关键词（支持中英日文）
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（最大100）
    - **sort_field**: 排序字段（price/last_seen_dt/created_at），如果未指定则使用 ES 相关性分数排序
    - **sort_order**: 排序方向（asc/desc）
    - **filters**: 各种过滤条件
    - **lang**: 语言代码（en/zh/ja），用于翻译
    """
    try:
        # 验证枚举值
        if status and not ItemStatus.is_valid(status):
            status = None
        if category and not Category.is_valid(category):
            category = None
        if currency and not CurrencyCode.is_valid(currency):
            currency = None
        if lang and not LanguageCode.is_valid(lang):
            lang = LanguageCode.get_default()
        if sort_field and not any(sf.value == sort_field for sf in SortField):
            sort_field = SortField.get_default()
        if sort_order and not any(so.value == sort_order for so in SortOrder):
            sort_order = SortOrder.get_default()
        
        # 构建过滤器
        filters = None
        if any([status, site, category, brand_name, min_price is not None, max_price is not None, currency]):
            filters = SearchFilters(
                status=status,
                site=site,
                category=category,
                brand_name=brand_name,
                min_price=min_price,
                max_price=max_price,
                currency=currency
            )
        
        # 构建排序选项（如果用户未指定，SearchRanker 将使用 ES 相关性分数排序）
        sort = None
        if sort_field:
            from search.engine import SortOption
            sort = SortOption(field=sort_field, order=sort_order or SortOrder.get_default())
        
        # 执行搜索（使用 SearchRanker 实现召回+过滤+排序+重排）
        result = search_ranker.search(
            query=q,
            filters=filters,
            sort=sort,
            page=page,
            page_size=page_size
        )
        
        # 初始化翻译映射器（如果需要）
        mapper = None
        if lang and lang != "en":
            try:
                from i18n.translation.mapper import TranslationMapper
                from i18n.translation.normalizer import Normalizer
                from i18n.translation.language_detector import LanguageDetector
                mapper = TranslationMapper(database_url=settings.DATABASE_URL)
            except ImportError:
                mapper = None
            except Exception as e:
                logger.warning(f"翻译映射器初始化失败: {e}", exc_info=True)
                mapper = None
        
        # 处理结果，添加图片 URL 和翻译
        items = []
        for item in result.items:
            # 生成图片 URL
            image_thumb_url = None
            if item.get("image_thumb_300_key"):
                image_thumb_url = image_service.get_image_url(item["image_thumb_300_key"])
            
            # 翻译处理
            brand_translated = None
            model_translated = None
            if mapper and item.get("brand_name") and item.get("model_name"):
                try:
                    # 检测商品语言
                    product_lang = LanguageDetector.detect_product_language(
                        item["brand_name"],
                        item["model_name"]
                    )
                    
                    # 如果商品语言与用户选择的语言不同，进行翻译
                    if product_lang != lang:
                        category = item.get("category") or "watch"
                        normalized_brand = Normalizer.normalize_brand(item["brand_name"], category)
                        normalized_model = Normalizer.normalize_model_name(
                            normalized_brand,
                            item["model_name"],
                            category
                        )
                        
                        brand_translated = mapper.translate_brand(normalized_brand, lang)
                        model_translated = mapper.translate_model_name(
                            normalized_brand,
                            normalized_model,
                            lang
                        )
                except Exception as e:
                    logger.warning(f"翻译商品失败 (item_id={item.get('id')}): {e}", exc_info=True)
            
            # 构建结果项
            item_result = {
                **item,
                "image_thumb_url": image_thumb_url,
                "brand_name_translated": brand_translated,
                "model_name_translated": model_translated,
            }
            items.append(item_result)
        
        return SearchResponse(
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            items=items
        )
    except Exception as e:
        logger.error(f"搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/search/suggest", response_model=SuggestResponse)
async def suggest_products(
    q: str = Query(..., description="搜索关键词前缀"),
    size: int = Query(5, ge=1, le=20, description="返回建议数量"),
    db: Session = Depends(get_db),
    search_service = Depends(get_search_service)
):
    """
    获取搜索建议（SUG）
    
    - **q**: 搜索关键词前缀
    - **size**: 返回建议数量（最大20）
    """
    try:
        suggestions = search_service.suggest_products(query=q, size=size)
        return SuggestResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")
