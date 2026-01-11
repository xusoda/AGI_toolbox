#!/usr/bin/env python3
"""重建ES索引以启用新的Completion Suggester功能"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
possible_roots = [
    Path(__file__).parent.parent.parent,  # 从 search/scripts/rebuild_index_with_sug.py 向上3级到 GoodsHunter
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


def rebuild_index_with_sug(batch_size: int = 100, force: bool = False):
    """重建ES索引以启用新的Completion Suggester功能"""
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
            
            # 检查索引是否存在
            if es_engine.es_client.indices.exists(index=ES_INDEX_NAME):
                print(f"警告: 索引 '{ES_INDEX_NAME}' 已存在")
                if not force:
                    response = input(f"是否删除现有索引并重建? (yes/no): ")
                    if response.lower() not in ['yes', 'y']:
                        print("取消操作")
                        return
                
                print(f"删除现有索引: {ES_INDEX_NAME}")
                es_engine.es_client.indices.delete(index=ES_INDEX_NAME)
                print("索引已删除")
            
            # 创建新索引（会自动包含completion字段）
            print(f"创建新索引: {ES_INDEX_NAME}")
            es_engine._create_index()
            print("索引创建成功（包含completion字段）")
            
            # 创建同步器
            syncer = IndexSyncer(es_engine)
            
            # 执行全量同步
            print(f"开始全量同步数据 (batch_size={batch_size})...")
            count = syncer.sync_all(db_session, batch_size=batch_size)
            
            # 刷新索引
            print("刷新索引...")
            es_engine.refresh_index()
            
            print(f"✓ 索引重建完成！")
            print(f"  - 共同步 {count} 个商品")
            print(f"  - 新SUG功能已启用（使用Completion Suggester）")
            print(f"\n可以测试新的搜索建议功能:")
            print(f"  curl \"http://localhost:8000/api/search/suggest?q=Role&size=5\"")
            
        finally:
            db_session.close()
            db_engine.dispose()
    except Exception as e:
        print(f"重建索引失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="重建ES索引以启用新的Completion Suggester功能"
    )
    parser.add_argument("--batch-size", type=int, default=100, help="批量大小（默认: 100）")
    parser.add_argument("--force", "-f", action="store_true", help="强制删除现有索引（不提示确认）")
    args = parser.parse_args()
    
    rebuild_index_with_sug(batch_size=args.batch_size, force=args.force)
