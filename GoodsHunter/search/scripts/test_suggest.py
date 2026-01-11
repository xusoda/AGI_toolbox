#!/usr/bin/env python3
"""测试搜索建议功能的脚本"""
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/scripts/test_suggest.py 向上3级到 GoodsHunter
    Path("/app").parent,  # Docker 容器中
]

for root in possible_roots:
    try:
        api_path = root / "services" / "api"
        if api_path.exists() and api_path.is_dir():
            if str(root / "services" / "api") not in sys.path:
                sys.path.insert(0, str(root / "services" / "api"))
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            break
    except (OSError, PermissionError):
        continue

from elasticsearch import Elasticsearch
from search.es_engine import ElasticsearchSearchEngine

# 从环境变量读取配置
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "products")


def check_suggest_field_structure():
    """检查suggest字段的结构"""
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    print("\n检查suggest字段结构")
    print("=" * 80)
    
    try:
        # 查询包含"劳力士"或"Rolex"的文档
        query = {
            "query": {
                "bool": {
                    "should": [
                        {"term": {"brand_name.keyword": "Rolex"}},
                        {"match": {"brand_aliases": "劳力士"}},
                    ]
                }
            },
            "size": 5
        }
        
        response = es_client.search(index=ES_INDEX_NAME, body=query)
        hits = response["hits"]["hits"]
        
        print(f"找到 {len(hits)} 个相关文档\n")
        
        for i, hit in enumerate(hits, 1):
            doc = hit["_source"]
            print(f"\n文档 {i}:")
            print(f"  ID: {doc.get('id')}")
            print(f"  品牌名: {doc.get('brand_name')}")
            print(f"  型号名: {doc.get('model_name')}")
            print(f"  品牌别名: {doc.get('brand_aliases', [])}")
            print(f"  型号别名: {doc.get('model_aliases', [])}")
            
            suggest_field = doc.get('suggest')
            if suggest_field:
                suggest_inputs = suggest_field.get('input', [])
                print(f"  suggest.input: {suggest_inputs}")
                print(f"  是否包含'劳力士': {'劳力士' in suggest_inputs}")
                print(f"  是否包含'Rolex': {'Rolex' in suggest_inputs or 'ROLEX' in suggest_inputs}")
            else:
                print(f"  suggest字段: None（缺失！）")
            
            print("-" * 80)
            
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()


def test_suggest_query(query: str):
    """测试Completion Suggester查询"""
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    print(f"\n测试Completion Suggester查询: '{query}'")
    print("=" * 80)
    
    try:
        # 方式1：使用Completion Suggester API（当前代码使用的方式）
        es_query = {
            "suggest": {
                "product-suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "suggest",
                        "size": 10,
                        "skip_duplicates": True
                    }
                }
            }
        }
        
        print("\n查询结构:")
        print(json.dumps(es_query, ensure_ascii=False, indent=2))
        
        response = es_client.search(index=ES_INDEX_NAME, body=es_query)
        
        print("\n响应结构:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        
        # 解析结果
        suggestions = []
        if "suggest" in response and "product-suggest" in response["suggest"]:
            suggest_result = response["suggest"]["product-suggest"]
            if suggest_result and len(suggest_result) > 0:
                options = suggest_result[0].get("options", [])
                print(f"\n找到 {len(options)} 个建议:")
                for option in options:
                    text = option.get("text", "")
                    score = option.get("_score", 0)
                    source = option.get("_source", {})
                    print(f"  - {text} (score: {score})")
                    if text and text not in suggestions:
                        suggestions.append(text)
        
        if not suggestions:
            print("\n❌ 没有找到任何建议")
            
            # 检查可能的原因
            print("\n可能的原因:")
            print("1. 索引中没有包含该前缀的suggest字段")
            print("2. Completion Suggester对中文前缀匹配的支持问题")
            print("3. 需要重建索引")
        else:
            print(f"\n✓ 找到 {len(suggestions)} 个建议: {suggestions}")
            
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()


def test_suggest_with_engine(query: str):
    """使用ES引擎测试suggest功能"""
    print(f"\n使用ES引擎测试suggest: '{query}'")
    print("=" * 80)
    
    try:
        es_engine = ElasticsearchSearchEngine(
            es_host=ES_HOST,
            es_port=ES_PORT,
            index_name=ES_INDEX_NAME
        )
        
        suggestions = es_engine.suggest(query, size=10)
        
        if suggestions:
            print(f"\n✓ 找到 {len(suggestions)} 个建议:")
            for sug in suggestions:
                print(f"  - {sug}")
        else:
            print("\n❌ 没有找到任何建议")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


def check_mapping():
    """检查索引mapping"""
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    print("\n检查索引mapping")
    print("=" * 80)
    
    try:
        mapping = es_client.indices.get_mapping(index=ES_INDEX_NAME)
        suggest_mapping = mapping[ES_INDEX_NAME]["mappings"]["properties"].get("suggest", {})
        
        print("\nsuggest字段的mapping:")
        print(json.dumps(suggest_mapping, ensure_ascii=False, indent=2))
        
        # 检查是否有analyzer配置
        if "analyzer" in suggest_mapping:
            print(f"\n⚠️  警告: suggest字段使用了analyzer: {suggest_mapping['analyzer']}")
            print("Completion Suggester对中文前缀匹配可能不支持analyzer")
        else:
            print("\n✓ suggest字段没有使用analyzer（正确）")
            
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试搜索建议功能")
    parser.add_argument("--query", type=str, default="劳", help="测试查询词（默认: 劳）")
    parser.add_argument("--check-structure", action="store_true", help="检查suggest字段结构")
    parser.add_argument("--check-mapping", action="store_true", help="检查索引mapping")
    parser.add_argument("--test-raw", action="store_true", help="测试原始ES查询")
    parser.add_argument("--test-engine", action="store_true", help="使用ES引擎测试")
    
    args = parser.parse_args()
    
    if args.check_mapping:
        check_mapping()
    
    if args.check_structure:
        check_suggest_field_structure()
    
    if args.test_raw:
        test_suggest_query(args.query)
    
    if args.test_engine:
        test_suggest_with_engine(args.query)
    
    # 如果没有任何参数，运行所有检查
    if not any([args.check_mapping, args.check_structure, args.test_raw, args.test_engine]):
        print("运行所有检查...")
        check_mapping()
        check_suggest_field_structure()
        test_suggest_query(args.query)
        test_suggest_with_engine(args.query)