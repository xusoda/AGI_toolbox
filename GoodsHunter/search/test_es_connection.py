#!/usr/bin/env python3
"""测试ES连接和API"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent,
    Path("/app").parent,
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

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    print("elasticsearch 库未安装")
    sys.exit(1)

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))

def test_connection():
    """测试ES连接"""
    try:
        print(f"连接ES: {ES_HOST}:{ES_PORT}")
        es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
        
        # 测试连接
        if es_client.ping():
            print("✓ ES连接成功")
        else:
            print("✗ ES连接失败")
            return False
        
        # 获取集群信息
        info = es_client.info()
        print(f"✓ ES版本: {info['version']['number']}")
        print(f"✓ 集群名称: {info['cluster_name']}")
        
        # 检查集群健康
        health = es_client.cluster.health()
        print(f"✓ 集群状态: {health['status']}")
        
        return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_index():
    """测试创建索引"""
    try:
        es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
        index_name = "test_products"
        
        # 先删除测试索引（如果存在）
        try:
            if es_client.indices.exists(index=index_name):
                es_client.indices.delete(index=index_name)
                print(f"删除已存在的测试索引: {index_name}")
        except Exception as e:
            print(f"检查/删除测试索引时出错（忽略）: {e}")
        
        # 创建测试索引
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "brand_name": {"type": "text"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        print(f"尝试创建索引: {index_name}")
        print(f"Mapping结构: {mapping}")
        
        # 方法1: 使用body参数
        try:
            result = es_client.indices.create(index=index_name, body=mapping)
            print(f"✓ 方法1成功（body参数）: {result}")
            es_client.indices.delete(index=index_name)
        except Exception as e:
            print(f"✗ 方法1失败（body参数）: {e}")
        
        # 方法2: 直接传递参数
        try:
            result = es_client.indices.create(
                index=index_name,
                mappings=mapping["mappings"],
                settings=mapping["settings"]
            )
            print(f"✓ 方法2成功（直接参数）: {result}")
            es_client.indices.delete(index=index_name)
        except Exception as e:
            print(f"✗ 方法2失败（直接参数）: {e}")
        
        # 方法3: 使用**mapping展开
        try:
            result = es_client.indices.create(index=index_name, **mapping)
            print(f"✓ 方法3成功（**展开）: {result}")
            es_client.indices.delete(index=index_name)
        except Exception as e:
            print(f"✗ 方法3失败（**展开）: {e}")
        
    except Exception as e:
        print(f"✗ 测试创建索引失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if test_connection():
        test_create_index()
