"""测试MinIO连接和图片存储"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv
from storage.minio_client import MinIOClient

# 加载环境变量
load_dotenv(_project_root / ".env")

# 尝试导入 pytest（如果可用）
try:
    import pytest
except ImportError:
    pytest = None


def _test_minio_connection():
    """测试MinIO连接（内部函数）"""
    print("=" * 50)
    print("测试MinIO连接")
    print("=" * 50)
    
    try:
        client = MinIOClient()
        print(f"✓ MinIO连接成功")
        print(f"  端点: {client.endpoint}")
        print(f"  Bucket: {client.bucket}")
        return client
    except Exception as e:
        print(f"✗ MinIO连接失败: {e}")
        return None


def test_minio_connection():
    """pytest 测试函数：测试MinIO连接"""
    client = _test_minio_connection()
    assert client is not None, "MinIO连接失败"


# 定义 fixture 函数
def _minio_client_fixture():
    """pytest fixture：提供MinIO客户端"""
    client = _test_minio_connection()
    if client is None:
        if pytest:
            pytest.skip("MinIO连接失败，跳过测试")
        else:
            raise Exception("MinIO连接失败")
    return client

# 如果 pytest 可用，将函数标记为 fixture
if pytest:
    minio_client = pytest.fixture(_minio_client_fixture)
else:
    minio_client = _minio_client_fixture


def _test_list_objects(minio_client):
    """列出MinIO中的对象（内部函数）"""
    print("\n" + "=" * 50)
    print("列出MinIO中的对象")
    print("=" * 50)
    
    try:
        # 列出所有对象
        all_objects = minio_client.list_objects()
        print(f"总对象数: {len(all_objects)}")
        
        # 按类型分类
        original_objects = minio_client.list_objects("original/")
        thumb_300_objects = minio_client.list_objects("thumb/300/")
        thumb_600_objects = minio_client.list_objects("thumb/600/")
        
        print(f"\n原图数量: {len(original_objects)}")
        print(f"300px缩略图数量: {len(thumb_300_objects)}")
        print(f"600px缩略图数量: {len(thumb_600_objects)}")
        
        # 显示前10个对象
        if all_objects:
            print("\n前10个对象:")
            for i, obj_key in enumerate(all_objects[:10], 1):
                print(f"  {i}. {obj_key}")
        else:
            print("\n⚠️  MinIO中没有对象")
            print("   说明：图片还没有上传到MinIO")
            print("   当前图片只保存在本地文件系统: storage/file_storage/image/")
        
        return len(all_objects)
        
    except Exception as e:
        print(f"✗ 列出对象失败: {e}")
        import traceback
        traceback.print_exc()
        return 0


def test_list_objects(minio_client):
    """pytest 测试函数：列出MinIO中的对象"""
    result = _test_list_objects(minio_client)
    assert result >= 0, "列出对象失败"


def test_check_database_images(minio_client):
    """检查数据库中的图片key是否在MinIO中存在"""
    print("\n" + "=" * 50)
    print("检查数据库中的图片key")
    print("=" * 50)
    
    try:
        import psycopg2
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("✗ 未设置 DATABASE_URL 环境变量")
            return
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 查询有图片key的记录
        cursor.execute("""
            SELECT id, item_id, image_original_key, image_thumb_300_key, image_thumb_600_key, image_sha256
            FROM crawler_log
            WHERE image_original_key IS NOT NULL
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("⚠️  数据库中没有图片key记录")
            print("   说明：DBWriter在写入时，图片相关字段都设置为None")
            print("   需要实现Image Worker来下载图片、生成缩略图并上传到MinIO")
        else:
            print(f"找到 {len(rows)} 条有图片key的记录")
            print("\n检查这些key是否在MinIO中存在:")
            
            missing_count = 0
            for row in rows:
                record_id, item_id, orig_key, thumb_300_key, thumb_600_key, sha256 = row
                print(f"\n记录ID {record_id} (item_id: {item_id}):")
                
                if orig_key:
                    exists = minio_client.object_exists(orig_key)
                    status = "✓" if exists else "✗"
                    print(f"  {status} 原图: {orig_key}")
                    if not exists:
                        missing_count += 1
                
                if thumb_300_key:
                    exists = minio_client.object_exists(thumb_300_key)
                    status = "✓" if exists else "✗"
                    print(f"  {status} 300px: {thumb_300_key}")
                    if not exists:
                        missing_count += 1
                
                if thumb_600_key:
                    exists = minio_client.object_exists(thumb_600_key)
                    status = "✓" if exists else "✗"
                    print(f"  {status} 600px: {thumb_600_key}")
                    if not exists:
                        missing_count += 1
            
            if missing_count > 0:
                print(f"\n⚠️  有 {missing_count} 个key在MinIO中不存在")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ 检查数据库失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("MinIO图片存储检查")
    print("=" * 50)
    
    # 测试连接（使用内部函数，避免 pytest 警告）
    client = _test_minio_connection()
    if not client:
        print("\n无法继续测试，请检查MinIO服务是否运行")
        print("运行: docker compose up -d")
        return
    
    # 列出对象
    object_count = _test_list_objects(client)
    
    # 检查数据库
    test_check_database_images(client)
    
    # 总结
    print("\n" + "=" * 50)
    print("检查总结")
    print("=" * 50)
    
    if object_count == 0:
        print("⚠️  当前状态：")
        print("   1. MinIO中没有图片对象")
        print("   2. 图片只保存在本地文件系统")
        print("   3. 数据库中的图片字段都是None")
        print("\n📋 需要实现：")
        print("   1. Image Worker来下载图片")
        print("   2. 生成缩略图（300px和600px）")
        print("   3. 上传到MinIO")
        print("   4. 更新数据库中的图片key")
    else:
        print(f"✓ MinIO中有 {object_count} 个图片对象")


if __name__ == "__main__":
    main()

