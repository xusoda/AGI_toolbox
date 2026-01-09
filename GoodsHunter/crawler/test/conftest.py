"""Pytest配置文件"""
import logging
import sys

import pytest

# 配置pytest-asyncio
pytest_plugins = ("pytest_asyncio",)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置测试相关的日志级别
logging.getLogger().setLevel(logging.INFO)
