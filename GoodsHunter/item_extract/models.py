"""数据模型定义

注意：所有表结构已统一管理在 storage/db/init.sql 中。
本文件仅用于向后兼容，检查表是否存在。

表结构初始化：
- 推荐方式：通过 Docker 自动执行 storage/db/init.sql
- 手动方式：psql -U goodshunter -d goodshunter -f storage/db/init.sql
"""


def create_tables(conn):
    """
    检查必要的表是否存在
    
    注意：表结构已统一在 storage/db/init.sql 中定义。
    此函数仅用于检查表是否存在，不创建表。
    
    如果表不存在，此函数会抛出异常，提示用户先执行 init.sql。
    
    Args:
        conn: 数据库连接对象
        
    Raises:
        Exception: 如果表不存在
    """
    cursor = conn.cursor()
    
    try:
        # 检查必要的表是否存在
        required_tables = [
            'pipeline_state',
            'crawler_item',
            'item_change_history'
        ]
        
        missing_tables = []
        for table_name in required_tables:
            check_table_sql = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """
            cursor.execute(check_table_sql, (table_name,))
            exists = cursor.fetchone()[0]
            if not exists:
                missing_tables.append(table_name)
        
        if missing_tables:
            raise Exception(
                f"以下表不存在: {', '.join(missing_tables)}。"
                "请先执行 storage/db/init.sql 初始化数据库表结构。"
                "或通过 Docker 启动时自动执行。"
            )
        
        print("[models] 所有必要的表已存在")
        
    except Exception as e:
        print(f"[models] 表检查失败: {e}")
        raise
    finally:
        cursor.close()

