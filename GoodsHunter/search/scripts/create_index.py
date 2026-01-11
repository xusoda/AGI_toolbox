#!/usr/bin/env python3
"""创建ES索引脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/scripts/create_index.py 向上3级到 GoodsHunter
    Path("/app").parent,  # Docker 容器中
]

for root in possible_roots:
    try:
        search_path = root / "search"
        if search_path.exists() and search_path.is_dir():
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            break
    except (OSError, PermissionError):
        continue

from search.es_engine import ElasticsearchSearchEngine

# 从环境变量读取配置
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "products")


def create_index():
    """创建ES索引"""
    try:
        print(f"连接ES: {ES_HOST}:{ES_PORT}")
        es_engine = ElasticsearchSearchEngine(
            es_host=ES_HOST,
            es_port=ES_PORT,
            index_name=ES_INDEX_NAME
        )
        
        if es_engine.is_ready():
            print(f"ES索引 '{ES_INDEX_NAME}' 创建/检查成功")
        else:
            print("ES连接失败")
            sys.exit(1)
    except Exception as e:
        print(f"创建索引失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    create_index()
