"""数据库查询函数"""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from typing import Optional, List, Tuple
from app.db.models import CrawlerItem

# 添加项目根目录到路径（如果还未添加）
# 检查是否已经添加了项目根目录
if not any('enums' in str(p) or Path(str(p)).name == 'GoodsHunter' for p in sys.path):
    # 尝试从当前文件位置向上查找项目根目录
    current_file = Path(__file__)
    possible_roots = [
        current_file.parent.parent.parent.parent.parent,  # 从 services/api/app/db/queries.py 向上5级到 GoodsHunter
        current_file.parent.parent.parent.parent,  # 从 services/api/app/db/queries.py 向上4级
        Path("/app").parent,  # Docker 容器中，/app 的父目录（不使用 resolve）
    ]
    for root in possible_roots:
        try:
            enums_path = root / "enums"
            if enums_path.exists() and enums_path.is_dir():
                project_root = str(root.absolute() if hasattr(root, 'absolute') else root)
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                break
        except (OSError, PermissionError):
            continue

from enums.business.category import Category
from enums.business.status import ItemStatus
from enums.display.sort import SortOption


def get_items(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    sort: str = "first_seen_desc",
    category: Optional[str] = None
) -> Tuple[List[CrawlerItem], int]:
    """
    获取商品列表（分页）
    
    Args:
        db: 数据库会话
        page: 页码（从1开始）
        page_size: 每页数量
        status: 商品状态（active/sold/removed），None 表示不过滤，默认使用 ItemStatus.get_default()
        sort: 排序方式（first_seen_desc/price_asc/price_desc）
        category: 商品类别，None 表示不过滤
    
    Returns:
        (商品列表, 总数)
    """
    query = db.query(CrawlerItem)
    
    # 状态过滤
    if status:
        query = query.filter(CrawlerItem.status == status)
    
    # 类别过滤
    if category and Category.is_valid(category):
        query = query.filter(CrawlerItem.category == category)
    
    # 排序
    if sort == SortOption.PRICE_ASC.value:
        query = query.order_by(asc(CrawlerItem.price))
    elif sort == SortOption.PRICE_DESC.value:
        query = query.order_by(desc(CrawlerItem.price))
    else:  # 默认 first_seen_desc
        # 按 first_seen_dt 降序排序，如果 first_seen_dt 相同则按 id 降序排序
        query = query.order_by(desc(CrawlerItem.first_seen_dt), desc(CrawlerItem.id))
    
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

