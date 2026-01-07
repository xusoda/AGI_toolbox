"""测试 DBWriter 功能"""
import os
import sys
from pathlib import Path

# 添加项目根目录和crawler目录到路径
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
_crawler_dir = _project_root / "crawler"

if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_crawler_dir) not in sys.path:
    sys.path.insert(0, str(_crawler_dir))

from dotenv import load_dotenv
from output.db_writer import DBWriter
from core.types import Record, FieldError

# 加载环境变量
load_dotenv(_project_root / ".env")


def test_db_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        db_writer = DBWriter()
        print("✓ 数据库连接成功")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


def test_write_record():
    """测试写入记录"""
    print("\n测试写入记录...")
    try:
        # 创建测试记录
        test_record = Record(
            url="https://commit-watch.co.jp/products/test123",
            data={
                "items": [
                    {
                        "item_id": "test123",
                        "product_url": "https://commit-watch.co.jp/products/test123",
                        "brand_name": "Rolex",
                        "model_name": "Submariner",
                        "model_no": "116610LN",
                        "price_jpy": 1000000,
                        "currency": "JPY",
                        "image": "https://example.com/image.jpg"
                    }
                ]
            },
            errors=[]
        )
        
        db_writer = DBWriter()
        count = db_writer.write_record(test_record, site="commit-watch.co.jp")
        
        if count > 0:
            print(f"✓ 成功写入 {count} 条记录")
            return True
        else:
            print("✗ 写入失败：记录数为0")
            return False
            
    except Exception as e:
        print(f"✗ 写入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_record():
    """测试查询记录"""
    print("\n测试查询记录...")
    try:
        import psycopg2
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("✗ 未设置 DATABASE_URL 环境变量")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM crawler_log")
        count = cursor.fetchone()[0]
        print(f"✓ 数据库中共有 {count} 条记录")
        
        cursor.execute("""
            SELECT site, item_id, brand_name, model_name, price 
            FROM crawler_log 
            ORDER BY crawl_time DESC 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        if rows:
            print("\n最近5条记录:")
            for row in rows:
                print(f"  - {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("DBWriter 测试")
    print("=" * 50)
    
    # 检查环境变量
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("错误: 未设置 DATABASE_URL 环境变量")
        print("请创建 .env 文件并设置 DATABASE_URL")
        return
    
    print(f"数据库URL: {database_url.split('@')[1] if '@' in database_url else 'N/A'}")
    
    # 运行测试
    results = []
    results.append(("数据库连接", test_db_connection()))
    results.append(("写入记录", test_write_record()))
    results.append(("查询记录", test_query_record()))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("测试结果:")
    print("=" * 50)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 部分测试失败，请检查错误信息")


if __name__ == "__main__":
    main()

