"""商品相关路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径，以便导入 i18n 和 enums 模块
# 在 Docker 容器中，模块目录被挂载到 /app/../*
# 注意：避免使用 resolve()，可能导致路径问题或阻塞
possible_roots = [
    Path(__file__).parent.parent.parent.parent.parent,  # 从 services/api/app/routers/items.py 向上5级到 GoodsHunter
    Path(__file__).parent.parent.parent.parent,  # 从 services/api/app/routers/items.py 向上4级
    Path("/app").parent,  # Docker 容器中，/app 的父目录（不使用 resolve）
]

# 查找项目根目录并添加到 sys.path（优先通过 enums 目录，因为这是必需的）
project_root = None

# 方法1: 通过 enums 目录定位（最可靠，因为这是必需的）
for root in possible_roots:
    try:
        enums_path = root / "enums"
        if enums_path.exists() and enums_path.is_dir():
            project_root = str(root.absolute()) if hasattr(root, 'absolute') else str(root)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            break
    except (OSError, PermissionError):
        continue

# 方法2: 如果还没找到，尝试通过 i18n 目录定位
if project_root is None:
    possible_i18n_paths = [
        Path("/app").parent / "i18n",  # Docker 环境（不使用 resolve）
        Path("/i18n"),
    ]
    for i18n_path in possible_i18n_paths:
        try:
            if i18n_path.exists() and i18n_path.is_dir():
                project_root = str((i18n_path.parent).absolute() if hasattr(i18n_path.parent, 'absolute') else i18n_path.parent)
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                break
        except (OSError, PermissionError):
            continue

from app.db.session import get_db
from app.db.queries import get_items, get_item_by_id
from app.schemas.items import ItemsListResponse, ItemListItem, ItemDetail
from app.services.images import image_service, get_image_service
from app.settings import settings
from enums.business.category import Category
from enums.business.status import ItemStatus
from enums.display.sort import SortOption
from enums.display.lang import LanguageCode
from fastapi.responses import StreamingResponse

# 获取 logger
logger = logging.getLogger(__name__)

# 导入翻译映射器
try:
    from i18n.translation.mapper import TranslationMapper
    from i18n.translation.normalizer import Normalizer
    from i18n.translation.language_detector import LanguageDetector
    TRANSLATION_AVAILABLE = True
    logger.info("i18n 模块加载成功")
except ImportError as e:
    TRANSLATION_AVAILABLE = False
    logger.warning(f"i18n 模块不可用，多语言功能将被禁用: {e}")
    logger.debug(f"Python 路径: {sys.path}")

router = APIRouter()


@router.get("/items", response_model=ItemsListResponse)
async def list_items(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description=f"商品状态（{'/'.join(ItemStatus.all_values())}），默认 {ItemStatus.get_default()}"),
    sort: str = Query(SortOption.get_default(), description=f"排序方式（{'/'.join([s.value for s in SortOption])}），默认 {SortOption.get_default()}"),
    lang: Optional[str] = Query(LanguageCode.get_default(), description=f"语言代码（{'/'.join(LanguageCode.all_values())}），默认 {LanguageCode.get_default()}"),
    category: Optional[str] = Query(None, description=f"商品类别（{'/'.join(Category.all_values())}），可选"),
    db: Session = Depends(get_db)
):
    """
    获取商品列表（分页）
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（最大100）
    - **status**: 商品状态，默认 active
    - **sort**: 排序方式，默认 first_seen_desc
    - **lang**: 语言代码，默认 en
    - **category**: 商品类别，可选
    """
    # 验证和设置默认值
    if status and not ItemStatus.is_valid(status):
        status = ItemStatus.get_default()
    elif status is None:
        status = ItemStatus.get_default()
    
    if category and not Category.is_valid(category):
        category = None
    
    if lang and not LanguageCode.is_valid(lang):
        lang = LanguageCode.get_default()
    
    items, total = get_items(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        sort=sort,
        category=category
    )

    # 初始化翻译映射器
    mapper = None
    if TRANSLATION_AVAILABLE and lang:
        try:
            mapper = TranslationMapper(database_url=settings.DATABASE_URL)
        except Exception as e:
            logger.warning(f"翻译映射器初始化失败: {e}", exc_info=True)
    
    # 转换为响应格式，生成图片 URL
    item_list = []
    for item in items:
        brand_final = None
        model_final = None
        
        # 动态检测商品语言并智能翻译
        if TRANSLATION_AVAILABLE and mapper and item.brand_name and item.model_name:
            try:
                # 1. 检测商品本身的语言
                product_lang = LanguageDetector.detect_product_language(
                    item.brand_name,
                    item.model_name
                )
                logger.debug(f"商品 {item.id}: 检测到语言={product_lang}, 用户选择={lang}, brand={item.brand_name}, model={item.model_name}")
                
                # 2. 只有当商品语言与用户选择的语言不同时，才进行翻译
                if product_lang != lang:
                    category = item.category or Category.get_default()
                    
                    # 归一化品牌和型号
                    normalized_brand = Normalizer.normalize_brand(item.brand_name, category)
                    normalized_model = Normalizer.normalize_model_name(
                        normalized_brand,
                        item.model_name,
                        category
                    )
                    logger.debug(f"商品 {item.id}: 归一化后 brand={normalized_brand}, model={normalized_model}")
                    
                    # 翻译
                    brand_translated = mapper.translate_brand(normalized_brand, lang)
                    model_translated = mapper.translate_model_name(
                        normalized_brand,
                        normalized_model,
                        lang
                    )
                    logger.debug(f"商品 {item.id}: 翻译后 brand={brand_translated}, model={model_translated}")
                    
                    # 只有当翻译后的值确实不同时，才使用翻译值
                    if brand_translated and brand_translated != item.brand_name:
                        brand_final = brand_translated
                    if model_translated and model_translated != item.model_name:
                        model_final = model_translated
                else:
                    logger.debug(f"商品 {item.id}: 语言匹配，无需翻译")
            except Exception as e:
                logger.warning(f"翻译商品失败 (item_id={item.id}): {e}", exc_info=True)
        else:
            if not TRANSLATION_AVAILABLE:
                logger.debug(f"商品 {item.id}: TRANSLATION_AVAILABLE=False")
            elif not mapper:
                logger.debug(f"商品 {item.id}: mapper=None")
            elif not item.brand_name or not item.model_name:
                logger.debug(f"商品 {item.id}: brand_name={item.brand_name}, model_name={item.model_name}")
        
        item_dict = {
            "id": item.id,
            "brand_name": item.brand_name,
            "brand_name_translated": brand_final,
            "model_name": item.model_name,
            "model_name_translated": model_final,
            "model_no": item.model_no,
            "currency": item.currency,
            "price": item.price,
            "image_thumb_url": image_service.get_image_url(item.image_thumb_300_key),
            "last_seen_dt": item.last_seen_dt,
            "status": item.status,
            "product_id": getattr(item, 'product_id', None)
        }
        item_list.append(ItemListItem(**item_dict))
    
    return ItemsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=item_list
    )


@router.get("/items/{item_id}", response_model=ItemDetail)
async def get_item(
    item_id: int,
    lang: Optional[str] = Query(LanguageCode.get_default(), description=f"语言代码（{'/'.join(LanguageCode.all_values())}），默认 {LanguageCode.get_default()}"),
    db: Session = Depends(get_db)
):
    """
    获取商品详情
    
    - **item_id**: 商品 ID
    - **lang**: 语言代码，默认 en
    """
    item = get_item_by_id(db=db, item_id=item_id)
    
    if not item:
         raise HTTPException(status_code=404, detail="商品不存在")

    # 验证语言代码
    if lang and not LanguageCode.is_valid(lang):
        lang = LanguageCode.get_default()
    
    # 初始化翻译映射器
    mapper = None
    if TRANSLATION_AVAILABLE and lang:
        try:
            mapper = TranslationMapper(database_url=settings.DATABASE_URL)
        except Exception as e:
            logger.warning(f"翻译映射器初始化失败: {e}", exc_info=True)
    
    # 动态检测商品语言并智能翻译
    brand_final = None
    model_final = None
    if TRANSLATION_AVAILABLE and mapper and item.brand_name and item.model_name:
        try:
            # 1. 检测商品本身的语言
            product_lang = LanguageDetector.detect_product_language(
                item.brand_name,
                item.model_name
            )
            
            # 2. 只有当商品语言与用户选择的语言不同时，才进行翻译
            if product_lang != lang:
                category = item.category or Category.get_default()
                
                # 归一化品牌和型号
                normalized_brand = Normalizer.normalize_brand(item.brand_name, category)
                normalized_model = Normalizer.normalize_model_name(
                    normalized_brand,
                    item.model_name,
                    category
                )
                
                # 翻译
                brand_translated = mapper.translate_brand(normalized_brand, lang)
                model_translated = mapper.translate_model_name(
                    normalized_brand,
                    normalized_model,
                    lang
                )
                
                # 只有当翻译后的值确实不同时，才使用翻译值
                if brand_translated and brand_translated != item.brand_name:
                    brand_final = brand_translated
                if model_translated and model_translated != item.model_name:
                    model_final = model_translated
        except Exception as e:
            logger.warning(f"翻译商品失败 (item_id={item_id}): {e}", exc_info=True)
    
    # 转换为响应格式，生成图片 URL
    item_dict = {
        "id": item.id,
        "source_uid": item.source_uid,
        "site": item.site,
        "category": item.category,
        "item_id": item.item_id,
        "brand_name": item.brand_name,
        "brand_name_translated": brand_final,
        "model_name": item.model_name,
        "model_name_translated": model_final,
        "model_no": item.model_no,
        "currency": item.currency,
        "price": item.price,
        "image_thumb_url": image_service.get_image_url(item.image_thumb_300_key),
        "image_600_url": image_service.get_image_url(item.image_thumb_600_key),
        "image_original_url": image_service.get_image_url(item.image_original_key),
        "product_url": item.product_url,
        "status": item.status,
        "first_seen_dt": item.first_seen_dt,
        "last_seen_dt": item.last_seen_dt,
        "sold_dt": item.sold_dt,
        "sold_reason": item.sold_reason,
        "last_crawl_time": item.last_crawl_time,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "product_id": getattr(item, 'product_id', None)
    }
    
    return ItemDetail(**item_dict)


@router.get("/images/{key:path}")
async def get_image(key: str):
    """
    图片代理端点：从 MinIO 获取图片并转发给前端
    这样可以避免 presigned URL 的端点问题
    """
    try:
        # 使用内部端点客户端下载图片
        # 获取实际的 ImageService 实例（延迟初始化）
        service = get_image_service()
        service._ensure_initialized()  # 确保已初始化
        
        if not service.minio_client:
            raise HTTPException(status_code=500, detail="图片服务未初始化")
        
        # 从 MinIO 下载图片
        # MinIOClient 有 download_image 方法
        image_data = service.minio_client.download_image(key)
        
        # 根据文件扩展名确定 content type
        content_type = "image/jpeg"
        if key.endswith(".webp"):
            content_type = "image/webp"
        elif key.endswith(".png"):
            content_type = "image/png"
        elif key.endswith(".gif"):
            content_type = "image/gif"
        
        # 返回图片流
        from io import BytesIO
        return StreamingResponse(
            BytesIO(image_data),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600"  # 缓存1小时
            }
        )
    except Exception as e:
        logger.error(f"[ImageProxy] 获取图片失败: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"图片不存在: {key}")

