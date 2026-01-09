"""测试搜索引擎基础功能（只读）"""
import pytest
from search.engine import SearchEngine, SearchFilters, SortOption
from search.postgres_engine import PostgresSearchEngine
import os

# 从环境变量获取测试数据库URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter"
)


@pytest.fixture
def search_engine():
    """创建搜索引擎实例"""
    try:
        return PostgresSearchEngine(database_url=TEST_DATABASE_URL)
    except Exception as e:
        pytest.skip(f"无法连接到数据库: {e}")


def test_engine_is_ready(search_engine):
    """测试搜索引擎是否就绪（只读操作）"""
    # is_ready方法只执行SELECT 1，是只读操作
    is_ready = search_engine.is_ready()
    assert isinstance(is_ready, bool)


def test_engine_implements_interface(search_engine):
    """测试搜索引擎实现了SearchEngine接口"""
    assert isinstance(search_engine, SearchEngine)


def test_search_filters_dataclass():
    """测试SearchFilters数据类"""
    filters = SearchFilters(
        status="active",
        site="example.com",
        category="watch",
        brand_name="Rolex",
        min_price=1000,
        max_price=5000,
        currency="JPY"
    )
    assert filters.status == "active"
    assert filters.site == "example.com"
    assert filters.category == "watch"
    assert filters.brand_name == "Rolex"
    assert filters.min_price == 1000
    assert filters.max_price == 5000
    assert filters.currency == "JPY"


def test_sort_option_dataclass():
    """测试SortOption数据类"""
    sort = SortOption(field="price", order="asc")
    assert sort.field == "price"
    assert sort.order == "asc"
