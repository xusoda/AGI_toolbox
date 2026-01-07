"""数据库查询函数"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from typing import Optional, List, Tuple
from app.db.models import CrawlerItem


def get_items(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = "active",
    sort: str = "last_seen_desc"
) -> Tuple[List[CrawlerItem], int]:
    """
    获取商品列表（分页）
    
    Args:
        db: 数据库会话
        page: 页码（从1开始）
        page_size: 每页数量
        status: 商品状态（active/sold/removed），None 表示不过滤
        sort: 排序方式（last_seen_desc/price_asc/price_desc）
    
    Returns:
        (商品列表, 总数)
    """
    query = db.query(CrawlerItem)
    
    # 状态过滤
    if status:
        query = query.filter(CrawlerItem.status == status)
    
    # 排序
    if sort == "price_asc":
        query = query.order_by(asc(CrawlerItem.price))
    elif sort == "price_desc":
        query = query.order_by(desc(CrawlerItem.price))
    else:  # 默认 last_seen_desc
        query = query.order_by(desc(CrawlerItem.last_seen_dt))
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    return items, total


def get_item_by_id(db: Session, item_id: int) -> Optional[CrawlerItem]:
    """
    根据 ID 获取商品详情
    
    Args:
        db: 数据库会话
        item_id: 商品 ID
    
    Returns:
        商品对象，如果不存在返回 None
    """
    return db.query(CrawlerItem).filter(CrawlerItem.id == item_id).first()

