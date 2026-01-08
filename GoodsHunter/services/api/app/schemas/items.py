"""API 响应 Schema"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class ItemListItem(BaseModel):
    """商品列表项"""
    id: int
    brand_name: Optional[str]
    brand_name_translated: Optional[str] = None  # 翻译后的品牌名
    model_name: Optional[str]
    model_name_translated: Optional[str] = None  # 翻译后的型号名
    model_no: Optional[str]
    currency: str
    price: Optional[int]
    image_thumb_url: Optional[str]
    last_seen_dt: date
    status: str
    product_id: Optional[int] = None  # 关联的聚合商品ID
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()  # 允许使用 model_ 开头的字段名
    )


class ItemDetail(BaseModel):
    """商品详情"""
    id: int
    source_uid: str
    site: str
    category: str
    item_id: str
    brand_name: Optional[str]
    brand_name_translated: Optional[str] = None  # 翻译后的品牌名
    model_name: Optional[str]
    model_name_translated: Optional[str] = None  # 翻译后的型号名
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
    product_id: Optional[int] = None  # 关联的聚合商品ID
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()  # 允许使用 model_ 开头的字段名
    )


class ItemsListResponse(BaseModel):
    """商品列表响应"""
    total: int
    page: int
    page_size: int
    items: list[ItemListItem]

