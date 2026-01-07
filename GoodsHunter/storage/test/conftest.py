"""Pytest配置文件"""
import os
import sys
from pathlib import Path
import pytest

# 添加项目根目录到路径
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv
from storage.minio_client import MinIOClient

# 加载环境变量
load_dotenv(_project_root / ".env")

# 配置pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="module")
def minio_client():
    """MinIO客户端fixture"""
    try:
        client = MinIOClient()
        yield client
    except Exception as e:
        pytest.skip(f"MinIO连接失败，跳过测试: {e}")

