"""数据库 ORM 模型"""
from sqlalchemy import Column, BigInteger, Text, Integer, Date, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class CrawlerItem(Base):
    """商品主表模型"""
    __tablename__ = "crawler_item"
    
    id = Column(BigInteger, primary_key=True, index=True)
    source_uid = Column(Text, unique=True, nullable=False, index=True)
    site = Column(Text, nullable=False, index=True)
    category = Column(Text, nullable=False)
    item_id = Column(Text, nullable=False)
    
    # 展示字段
    brand_name = Column(Text, nullable=True, index=True)
    model_name = Column(Text, nullable=True)
    model_no = Column(Text, nullable=True, index=True)
    currency = Column(String(10), nullable=False, default="JPY")
    price = Column(Integer, nullable=True, index=True)
    
    # 图片引用（MinIO keys）
    image_sha256 = Column(Text, nullable=True)
    image_original_key = Column(Text, nullable=True)
    image_thumb_300_key = Column(Text, nullable=True)
    image_thumb_600_key = Column(Text, nullable=True)
    
    # 商品 URL
    product_url = Column(Text, nullable=True)
    
    # 状态字段
    status = Column(Text, nullable=False, default="active", index=True)
    first_seen_dt = Column(Date, nullable=False)
    last_seen_dt = Column(Date, nullable=False, index=True)
    sold_dt = Column(Date, nullable=True)
    sold_reason = Column(Text, nullable=True)
    
    # 时间戳字段
    last_crawl_time = Column(DateTime(timezone=True), nullable=False)
    last_log_id = Column(BigInteger, nullable=True)
    price_last_changed_at = Column(DateTime(timezone=True), nullable=True)
    price_last_changed_dt = Column(Date, nullable=True)
    
    # 版本号
    version = Column(Integer, nullable=False, default=1)
    
    # 创建和更新时间
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

