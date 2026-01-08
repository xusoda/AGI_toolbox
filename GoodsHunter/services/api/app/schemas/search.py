"""搜索相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class SearchFiltersSchema(BaseModel):
    """搜索过滤器 Schema"""
    status: Optional[str] = Field(None, description="商品状态（active/sold/removed）")
    site: Optional[str] = Field(None, description="站点域名")
    category: Optional[str] = Field(None, description="商品类别")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    min_price: Optional[int] = Field(None, description="最低价格")
    max_price: Optional[int] = Field(None, description="最高价格")
    currency: Optional[str] = Field(None, description="货币单位")


class SearchItemResult(BaseModel):
    """搜索结果项"""
    id: int
    brand_name: Optional[str]
    model_name: Optional[str]
    model_no: Optional[str]
    price: Optional[int]
    currency: str
    site: str
    category: str
    status: str
    last_seen_dt: Optional[date]
    image_thumb_300_key: Optional[str]
    product_url: Optional[str]
    created_at: Optional[str]
    
    # 用于展示的字段（由路由层填充）
    image_thumb_url: Optional[str] = None
    brand_name_translated: Optional[str] = None
    model_name_translated: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    total: int = Field(description="总结果数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    items: List[SearchItemResult] = Field(description="搜索结果列表")


class SuggestResponse(BaseModel):
    """搜索建议响应"""
    suggestions: List[str] = Field(description="建议列表")
