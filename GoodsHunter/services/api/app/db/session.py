"""数据库会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.settings import settings

# 创建数据库引擎（延迟连接，不会立即连接数据库）
# 使用 pool_pre_ping=True 可以在每次连接前检查连接是否有效
# 设置连接超时，避免启动时阻塞
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,  # 设置为 True 可以看到 SQL 日志
    connect_args={
        "connect_timeout": 5  # 连接超时 5 秒
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

