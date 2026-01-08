"""搜索相关路由"""
import logging
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.search import SearchResponse, SuggestResponse
from app.services.images import image_service
from app.settings import settings

# 添加项目根目录到路径
# 在 Docker 容器中，路径结构是：
# /app (services/api)
# /app/../search (项目根目录下的 search) - 挂载为 /app/../search
# /app/../i18n (项目根目录下的 i18n)
# /app/../storage (项目根目录下的 storage)

# 注意：不要使用 resolve()，因为它会规范化路径，/app/.. 会变成 /
# 直接使用字符串路径或 Path 对象，不调用 resolve()

possible_search_paths = [
    Path("/app/../search"),  # Docker 容器中的搜索模块路径（不 resolve）
    Path("/app").parent / "search",  # 另一种方式
    Path(__file__).parent.parent.parent.parent.parent / "search",  # 本地开发环境
    Path(__file__).parent.parent.parent.parent / "search",  # 本地开发环境（备用）
]

# 添加搜索模块路径
search_found = False
for search_path in possible_search_paths:
    # 检查路径是否存在（不 resolve，直接检查）
    try:
        if search_path.exists() and search_path.is_dir():
            # 获取项目根目录（search 的父目录）
            project_root = search_path.parent
            sys.path.insert(0, str(project_root))
            print(f"[Search] 找到搜索模块路径: {search_path}, 添加根目录: {project_root}")
            search_found = True
            break
    except Exception as e:
        print(f"[Search] 检查路径失败 {search_path}: {e}")
        continue

if not search_found:
    # 如果找不到，尝试直接添加可能的路径
    print("[Search] 未找到搜索模块路径，尝试添加默认路径")
    # 尝试直接使用 /app/.. 作为项目根目录（Docker 环境）
    docker_root = Path("/app/..")
    docker_search_path = docker_root / "search"
    if docker_search_path.exists():
        sys.path.insert(0, str(docker_root))
        print(f"[Search] 使用 Docker 路径: {docker_root} (搜索模块: {docker_search_path})")
    else:
        print(f"[Search] 警告: 搜索模块路径不存在: {docker_search_path}")
        print(f"[Search] 当前工作目录: {Path.cwd()}")
        print(f"[Search] Python 路径: {sys.path}")
        # 列出可能的路径供调试
        test_paths = [
            Path("/app/../search"),
            Path("/app").parent / "search",
            Path("/search"),
        ]
        for test_path in test_paths:
            exists = test_path.exists() if hasattr(test_path, 'exists') else False
            print(f"[Search] 测试路径 {test_path}: exists={exists}")

# 导入搜索模块
try:
    from search.postgres_engine import PostgresSearchEngine
    from search.service import SearchService
    from search.engine import SearchFilters, SortOption
    SEARCH_AVAILABLE = True
except ImportError as e:
    SEARCH_AVAILABLE = False
    # 定义占位类型，避免类型检查错误
    SearchService = None
    PostgresSearchEngine = None
    SearchFilters = None
    SortOption = None
    logging.warning(f"搜索模块不可用: {e}")

logger = logging.getLogger(__name__)

router = APIRouter()


def get_search_service(db: Session = Depends(get_db)):
    """获取搜索服务实例（依赖注入）"""
    if not SEARCH_AVAILABLE:
        raise HTTPException(status_code=503, detail="搜索功能不可用")
    
    try:
        # 确保导入（防止延迟导入问题）
        from search.postgres_engine import PostgresSearchEngine
        from search.service import SearchService
        
        # 每次创建新的搜索引擎实例，使用当前数据库会话
        search_engine = PostgresSearchEngine(
            database_url=settings.DATABASE_URL,
            session=db
        )
        search_service = SearchService(search_engine)
        return search_service
    except Exception as e:
        logger.error(f"初始化搜索服务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索服务初始化失败: {e}")


@router.get("/search", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., description="搜索关键词（支持中英日文）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: Optional[str] = Query("last_seen_dt", description="排序字段（price/last_seen_dt/created_at）"),
    sort_order: Optional[str] = Query("desc", description="排序方向（asc/desc）"),
    status: Optional[str] = Query(None, description="商品状态（active/sold/removed）"),
    site: Optional[str] = Query(None, description="站点域名"),
    category: Optional[str] = Query(None, description="商品类别"),
    brand_name: Optional[str] = Query(None, description="品牌名称"),
    min_price: Optional[int] = Query(None, description="最低价格"),
    max_price: Optional[int] = Query(None, description="最高价格"),
    currency: Optional[str] = Query(None, description="货币单位"),
    lang: Optional[str] = Query("en", description="语言代码（en/zh/ja），默认 en"),
    db: Session = Depends(get_db),
    search_service = Depends(get_search_service)
):
    """
    搜索商品
    
    - **q**: 搜索关键词（支持中英日文）
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（最大100）
    - **sort_field**: 排序字段（price/last_seen_dt/created_at）
    - **sort_order**: 排序方向（asc/desc）
    - **filters**: 各种过滤条件
    - **lang**: 语言代码（en/zh/ja），用于翻译
    """
    try:
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
        
        # 构建排序选项
        sort = None
        if sort_field:
            from search.engine import SortOption
            sort = SortOption(field=sort_field, order=sort_order or "desc")
        
        # 执行搜索
        result = search_service.search_products(
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
