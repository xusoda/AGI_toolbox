"""API 响应 Schema"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ItemListItem(BaseModel):
    """商品列表项"""
    id: int
    brand_name: Optional[str]
    model_name: Optional[str]
    model_no: Optional[str]
    currency: str
    price: Optional[int]
    image_thumb_url: Optional[str]
    last_seen_dt: date
    status: str
    
    class Config:
        from_attributes = True


class ItemDetail(BaseModel):
    """商品详情"""
    id: int
    source_uid: str
    site: str
    category: str
    item_id: str
    brand_name: Optional[str]
    model_name: Optional[str]
    model_no: Optional[str]
    currency: str
    price: Optional[int]
    image_thumb_url: Optional[str]
    image_600_url: Optional[str]
    image_original_url: Optional[str]
    product_url: Optional[str]
    status: str
    first_seen_dt: date
    last_seen_dt: date
    sold_dt: Optional[date]
    sold_reason: Optional[str]
    last_crawl_time: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ItemsListResponse(BaseModel):
    """商品列表响应"""
    total: int
    page: int
    page_size: int
    items: list[ItemListItem]

