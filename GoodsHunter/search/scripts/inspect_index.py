#!/usr/bin/env python3
"""检查ES索引的工具脚本"""
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/scripts/inspect_index.py 向上3级到 GoodsHunter
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
from search.i18n.alias_resolver import AliasResolver

# 从环境变量读取配置
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "products")


def inspect_product_by_id(product_id: int):
    """检查指定商品的索引数据"""
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    try:
        response = es_client.get(index=ES_INDEX_NAME, id=str(product_id))
        doc = response["_source"]
        
        print(f"\n商品 ID: {product_id}")
        print("=" * 80)
        print(f"品牌名: {doc.get('brand_name')}")
        print(f"型号名: {doc.get('model_name')}")
        print(f"型号编号: {doc.get('model_no')}")
        print(f"\n品牌别名 (brand_aliases): {doc.get('brand_aliases', [])}")
        print(f"型号别名 (model_aliases): {doc.get('model_aliases', [])}")
        print(f"搜索文本 (search_text): {doc.get('search_text', '')}")
        print("\n完整文档:")
        import json
        print(json.dumps(doc, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"查询失败: {e}")


def inspect_brand_products(brand_name: str, search_term: Optional[str] = None):
    """检查指定品牌的所有商品索引，并验证是否包含某个搜索词"""
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    try:
        # 查询指定品牌的所有商品
        query = {
            "query": {
                "term": {"brand_name.keyword": brand_name}
            },
            "size": 100  # 最多返回100个
        }
        
        response = es_client.search(index=ES_INDEX_NAME, body=query)
        total = response["hits"]["total"]["value"]
        hits = response["hits"]["hits"]
        
        print(f"\n品牌: {brand_name}")
        print("=" * 80)
        print(f"总商品数: {total}")
        
        if search_term:
            print(f"\n检查是否包含搜索词: '{search_term}'")
            print("-" * 80)
            
            found_count = 0
            not_found_count = 0
            
            for hit in hits:
                doc = hit["_source"]
                brand_aliases = doc.get("brand_aliases", [])
                model_aliases = doc.get("model_aliases", [])
                search_text = doc.get("search_text", "")
                
                # 检查是否包含搜索词
                all_text = " ".join([
                    doc.get("brand_name", ""),
                    doc.get("model_name", ""),
                    *brand_aliases,
                    *model_aliases,
                    search_text
                ]).lower()
                
                if search_term.lower() in all_text:
                    found_count += 1
                    print(f"✓ 商品 {doc.get('id')}: {doc.get('brand_name')} {doc.get('model_name')}")
                    print(f"  品牌别名: {brand_aliases}")
                    print(f"  型号别名: {model_aliases}")
                else:
                    not_found_count += 1
                    print(f"✗ 商品 {doc.get('id')}: {doc.get('brand_name')} {doc.get('model_name')} (未包含'{search_term}')")
                    print(f"  品牌别名: {brand_aliases}")
                    print(f"  搜索文本: {search_text[:100]}...")
            
            print("\n" + "=" * 80)
            print(f"包含 '{search_term}' 的商品数: {found_count}")
            print(f"不包含 '{search_term}' 的商品数: {not_found_count}")
        else:
            # 只显示前10个商品的别名信息
            print("\n前10个商品的别名信息:")
            print("-" * 80)
            for i, hit in enumerate(hits[:10], 1):
                doc = hit["_source"]
                print(f"\n{i}. 商品 {doc.get('id')}: {doc.get('brand_name')} {doc.get('model_name')}")
                print(f"   品牌别名: {doc.get('brand_aliases', [])}")
                print(f"   型号别名: {doc.get('model_aliases', [])}")
                print(f"   搜索文本: {doc.get('search_text', '')[:100]}...")
    
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()


def inspect_model_products(model_name: str):
    """检查指定型号名的所有商品索引"""
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    try:
        # 使用 match 查询来匹配型号名（支持文本搜索）
        query = {
            "query": {
                "match": {"model_name": model_name}
            },
            "size": 100  # 最多返回100个
        }
        
        response = es_client.search(index=ES_INDEX_NAME, body=query)
        total = response["hits"]["total"]["value"]
        hits = response["hits"]["hits"]
        
        print(f"\n型号名: {model_name}")
        print("=" * 80)
        print(f"总商品数: {total}")
        
        # 显示所有匹配的商品信息
        print("\n匹配的商品信息:")
        print("-" * 80)
        for i, hit in enumerate(hits, 1):
            doc = hit["_source"]
            print(f"\n{i}. 商品 ID: {doc.get('id')}")
            print(f"   品牌名: {doc.get('brand_name')}")
            print(f"   型号名: {doc.get('model_name')}")
            print(f"   型号编号: {doc.get('model_no')}")
            print(f"   品牌别名: {doc.get('brand_aliases', [])}")
            print(f"   型号别名: {doc.get('model_aliases', [])}")
            print(f"   搜索文本: {doc.get('search_text', '')[:100]}...")
    
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()


def check_word_mapping(brand_name: str, category: str = "watch"):
    """检查词表中的品牌别名映射"""
    print(f"\n词表中的品牌别名映射: {brand_name}")
    print("=" * 80)
    
    aliases = AliasResolver.get_brand_aliases(brand_name, category)
    print(f"品牌: {brand_name}")
    print(f"别名列表: {aliases}")
    
    return aliases


def explain_search_query(query_text: str):
    """解释搜索查询是如何被构建的"""
    from search.es_engine import ElasticsearchSearchEngine
    from search.engine import SearchFilters
    
    print(f"\n搜索查询分析: '{query_text}'")
    print("=" * 80)
    
    es_engine = ElasticsearchSearchEngine(
        es_host=ES_HOST,
        es_port=ES_PORT,
        index_name=ES_INDEX_NAME
    )
    
    # 构建查询（不执行）
    es_query = es_engine._build_search_query(query_text, None, None, 1, 20)
    
    import json
    print("\nES查询结构:")
    print(json.dumps(es_query, ensure_ascii=False, indent=2))
    
    print("\n查询说明:")
    print("- 使用 multi_match 在多个字段中搜索:")
    print("  - brand_name (权重: 3.0)")
    print("  - brand_aliases (权重: 2.5)")
    print("  - model_name (权重: 2.0)")
    print("  - model_aliases (权重: 1.5)")
    print("  - search_text (权重: 1.0)")
    print("  - model_no (权重: 1.0)")
    print("- 支持模糊匹配 (fuzziness: AUTO)")
    print("- operator: or (任一字段匹配即可)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="检查ES索引的工具")
    parser.add_argument("--product-id", type=int, help="查看指定商品ID的索引数据")
    parser.add_argument("--brand", type=str, help="查看指定品牌的所有商品索引")
    parser.add_argument("--search-term", type=str, help="检查是否包含指定的搜索词（需配合--brand使用）")
    parser.add_argument("--model_name", type=str, help="查看指定型号名的所有商品索引")
    parser.add_argument("--check-word-mapping", type=str, help="检查词表中的品牌别名映射")
    parser.add_argument("--explain-query", type=str, help="解释搜索查询的结构")
    
    args = parser.parse_args()
    
    if args.product_id:
        inspect_product_by_id(args.product_id)
    elif args.brand:
        inspect_brand_products(args.brand, args.search_term)
    elif args.model_name:
        inspect_model_products(args.model_name)
    elif args.check_word_mapping:
        check_word_mapping(args.check_word_mapping)
    elif args.explain_query:
        explain_search_query(args.explain_query)
    else:
        parser.print_help()
        print("\n示例用法:")
        print("  # 查看商品ID为123的索引数据")
        print("  python inspect_index.py --product-id 123")
        print("\n  # 查看Rolex品牌的所有商品，并检查是否包含'劳力士'")
        print("  python inspect_index.py --brand Rolex --search-term 劳力士")
        print("\n  # 查看指定型号名的所有商品")
        print("  python inspect_index.py --model_name サブマリナー")
        print("\n  # 查看词表中Rolex的别名映射")
        print("  python inspect_index.py --check-word-mapping Rolex")
        print("\n  # 解释搜索查询'爱彼'的结构")
        print("  python inspect_index.py --explain-query 爱彼")
