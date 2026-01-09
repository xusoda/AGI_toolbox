"""Pytest 配置文件"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from search.postgres_engine import PostgresSearchEngine
from search.service import SearchService

# 从环境变量获取测试数据库URL，如果没有则使用默认值
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter"
)


@pytest.fixture(scope="function")
def search_engine():
    """创建搜索引擎实例（只读）"""
    try:
        engine = PostgresSearchEngine(database_url=TEST_DATABASE_URL)
        yield engine
    except Exception as e:
        pytest.skip(f"无法连接到数据库: {e}")


@pytest.fixture(scope="function")
def search_service(search_engine):
    """创建搜索服务实例（只读）"""
    return SearchService(search_engine)
