"""商品相关路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.db.queries import get_items, get_item_by_id
from app.schemas.items import ItemsListResponse, ItemListItem, ItemDetail
from app.services.images import image_service

router = APIRouter()


@router.get("/items", response_model=ItemsListResponse)
async def list_items(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query("active", description="商品状态"),
    sort: str = Query("last_seen_desc", description="排序方式：last_seen_desc/price_asc/price_desc"),
    db: Session = Depends(get_db)
):
    """
    获取商品列表（分页）
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（最大100）
    - **status**: 商品状态（active/sold/removed），默认 active
    - **sort**: 排序方式（last_seen_desc/price_asc/price_desc），默认 last_seen_desc
    """
    items, total = get_items(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        sort=sort
    )
    
    # 转换为响应格式，生成图片 URL
    item_list = []
    for item in items:
        item_dict = {
            "id": item.id,
            "brand_name": item.brand_name,
            "model_name": item.model_name,
            "model_no": item.model_no,
            "currency": item.currency,
            "price": item.price,
            "image_thumb_url": image_service.get_image_url(item.image_thumb_300_key),
            "last_seen_dt": item.last_seen_dt,
            "status": item.status
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
    db: Session = Depends(get_db)
):
    """
    获取商品详情
    
    - **item_id**: 商品 ID
    """
    item = get_item_by_id(db=db, item_id=item_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 转换为响应格式，生成图片 URL
    item_dict = {
        "id": item.id,
        "source_uid": item.source_uid,
        "site": item.site,
        "category": item.category,
        "item_id": item.item_id,
        "brand_name": item.brand_name,
        "model_name": item.model_name,
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
        "updated_at": item.updated_at
    }
    
    return ItemDetail(**item_dict)

