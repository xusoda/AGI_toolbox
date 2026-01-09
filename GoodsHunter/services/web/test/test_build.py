"""测试前端构建和基本功能"""
import pytest
import subprocess
import os
from pathlib import Path


@pytest.fixture
def web_dir():
    """获取web目录路径"""
    return Path(__file__).parent.parent


def test_package_json_exists(web_dir):
    """测试package.json文件存在"""
    package_json = web_dir / "package.json"
    assert package_json.exists(), "package.json文件不存在"


def test_vite_config_exists(web_dir):
    """测试vite.config.ts文件存在"""
    vite_config = web_dir / "vite.config.ts"
    assert vite_config.exists(), "vite.config.ts文件不存在"


def test_src_directory_exists(web_dir):
    """测试src目录存在"""
    src_dir = web_dir / "src"
    assert src_dir.exists() and src_dir.is_dir(), "src目录不存在"


def test_main_tsx_exists(web_dir):
    """测试main.tsx文件存在"""
    main_tsx = web_dir / "src" / "main.tsx"
    assert main_tsx.exists(), "main.tsx文件不存在"


def test_app_tsx_exists(web_dir):
    """测试App.tsx文件存在"""
    app_tsx = web_dir / "src" / "App.tsx"
    assert app_tsx.exists(), "App.tsx文件不存在"


def test_index_html_exists(web_dir):
    """测试index.html文件存在"""
    index_html = web_dir / "index.html"
    assert index_html.exists(), "index.html文件不存在"


def test_tsconfig_exists(web_dir):
    """测试tsconfig.json文件存在"""
    tsconfig = web_dir / "tsconfig.json"
    assert tsconfig.exists(), "tsconfig.json文件不存在"
