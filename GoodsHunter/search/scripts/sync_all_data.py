#!/usr/bin/env python3
"""全量同步数据到ES脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/scripts/sync_all_data.py 向上3级到 GoodsHunter
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
from search.sync.index_syncer import IndexSyncer

# 从环境变量读取配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter")
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME", "products")


def sync_all(batch_size: int = 100):
    """全量同步数据到ES"""
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
            
            # 创建同步器
            syncer = IndexSyncer(es_engine)
            
            # 执行全量同步
            print(f"开始全量同步 (batch_size={batch_size})...")
            count = syncer.sync_all(db_session, batch_size=batch_size)
            
            print(f"同步完成，共同步 {count} 个商品")
        finally:
            db_session.close()
            db_engine.dispose()
    except Exception as e:
        print(f"同步失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="全量同步数据到ES")
    parser.add_argument("--batch-size", type=int, default=100, help="批量大小（默认: 100）")
    args = parser.parse_args()
    
    sync_all(batch_size=args.batch_size)
