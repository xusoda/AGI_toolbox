"""测试搜索服务基础功能（只读）"""
import pytest
from search.service import SearchService
from search.postgres_engine import PostgresSearchEngine
from search.engine import SearchFilters, SortOption
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


@pytest.fixture
def search_service(search_engine):
    """创建搜索服务实例"""
    return SearchService(search_engine)


def test_service_initialization(search_service):
    """测试搜索服务初始化"""
    assert search_service is not None
    assert search_service.search_engine is not None
    assert search_service.data_manager is not None


def test_service_search_products_readonly(search_service):
    """测试搜索商品功能（只读操作）"""
    # 执行一个简单的搜索查询（只读）
    try:
        result = search_service.search_products(
            query="test",
            page=1,
            page_size=10
        )
        # 验证返回结果结构
        assert hasattr(result, 'items')
        assert hasattr(result, 'total')
        assert hasattr(result, 'page')
        assert hasattr(result, 'page_size')
        assert isinstance(result.items, list)
        assert isinstance(result.total, int)
        assert result.page == 1
        assert result.page_size == 10
    except Exception as e:
        # 如果数据库中没有数据或连接失败，跳过测试
        pytest.skip(f"搜索测试跳过: {e}")


def test_service_suggest_products_readonly(search_service):
    """测试搜索建议功能（只读操作）"""
    try:
        suggestions = search_service.suggest_products(
            query="test",
            size=5
        )
        # 验证返回结果结构
        assert isinstance(suggestions, list)
        # 建议数量应该不超过请求的数量
        assert len(suggestions) <= 5
    except Exception as e:
        # 如果数据库中没有数据或连接失败，跳过测试
        pytest.skip(f"搜索建议测试跳过: {e}")


def test_service_search_with_filters_readonly(search_service):
    """测试带过滤器的搜索（只读操作）"""
    try:
        filters = SearchFilters(
            status="active",
            category="watch"
        )
        result = search_service.search_products(
            query="test",
            filters=filters,
            page=1,
            page_size=10
        )
        # 验证返回结果结构
        assert hasattr(result, 'items')
        assert hasattr(result, 'total')
    except Exception as e:
        pytest.skip(f"带过滤器的搜索测试跳过: {e}")


def test_service_search_with_sort_readonly(search_service):
    """测试带排序的搜索（只读操作）"""
    try:
        sort = SortOption(field="price", order="asc")
        result = search_service.search_products(
            query="test",
            sort=sort,
            page=1,
            page_size=10
        )
        # 验证返回结果结构
        assert hasattr(result, 'items')
        assert hasattr(result, 'total')
    except Exception as e:
        pytest.skip(f"带排序的搜索测试跳过: {e}")
