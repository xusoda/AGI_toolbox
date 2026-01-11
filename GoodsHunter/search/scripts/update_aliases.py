#!/usr/bin/env python3
"""更新词表后，更新ES索引脚本"""
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/scripts/update_aliases.py 向上3级到 GoodsHunter
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

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from search.es_engine import ElasticsearchSearchEngine
from search.sync.alias_updater import AliasUpdater

# 从环境变量读取配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter")
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "products")


def update_aliases(rebuild_all: bool = False, updated_brands: Optional[List[str]] = None, updated_models: Optional[Dict[str, List[str]]] = None):
    """
    更新词表后，更新ES索引
    
    Args:
        rebuild_all: 是否全量重建
        updated_brands: 更新的品牌列表
        updated_models: 更新的型号字典 {brand: [models]}
    """
    try:
        print(f"连接数据库: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        print(f"连接ES: {ES_HOST}:{ES_PORT}")
        
        # 创建数据库引擎
        db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        db_session = Session(db_engine)
        
        try:
            # 创建ES引擎
            es_engine = ElasticsearchSearchEngine(
                es_host=ES_HOST,
                es_port=ES_PORT,
                index_name=ES_INDEX_NAME
            )
            
            if not es_engine.is_ready():
                print("ES连接失败", file=sys.stderr)
                sys.exit(1)
            
            # 创建更新器
            updater = AliasUpdater(es_engine)
            
            if rebuild_all:
                # 全量重建
                print("开始全量重建索引...")
                count = updater.rebuild_all(db_session)
                print(f"全量重建完成，更新 {count} 个商品")
            else:
                # 增量更新
                print(f"开始增量更新 (updated_brands={updated_brands}, updated_models={updated_models})...")
                count = updater.update_affected_items(db_session, updated_brands, updated_models)
                print(f"增量更新完成，更新 {count} 个商品")
        finally:
            db_session.close()
            db_engine.dispose()
    except Exception as e:
        print(f"更新失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="更新词表后，更新ES索引")
    parser.add_argument("--rebuild-all", action="store_true", help="全量重建索引")
    parser.add_argument("--brands", nargs="+", help="更新的品牌列表（空格分隔）")
    parser.add_argument("--models", type=str, help="更新的型号字典（JSON格式，如: '{\"Rolex\": [\"Submariner\", \"Datejust\"]}'）")
    args = parser.parse_args()
    
    updated_models = None
    if args.models:
        import json
        try:
            updated_models = json.loads(args.models)
        except json.JSONDecodeError:
            print("--models 参数格式错误，应为JSON格式", file=sys.stderr)
            sys.exit(1)
    
    update_aliases(
        rebuild_all=args.rebuild_all,
        updated_brands=args.brands,
        updated_models=updated_models
    )
