"""初始化翻译表：将 watch.yaml 中的数据导入到翻译表"""
import os
import sys
import json
import yaml
from pathlib import Path

# 添加项目根目录到路径
# 脚本位置: GoodsHunter/i18n/scripts/init_translations.py
# 项目根目录: GoodsHunter/
# 使用 resolve() 确保获取绝对路径，无论从哪里运行脚本
script_file = Path(__file__).resolve()
script_dir = script_file.parent  # i18n/scripts/
project_root = script_dir.parent.parent  # GoodsHunter/
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("错误: psycopg2 未安装，请运行: pip install psycopg2-binary")
    sys.exit(1)


def load_docker_compose_config() -> dict:
    """从 docker-compose.yml 读取数据库配置"""
    compose_path = project_root / "docker-compose.yml"
    
    if not compose_path.exists():
        return {}
    
    try:
        with open(compose_path, "r", encoding="utf-8") as f:
            compose_data = yaml.safe_load(f) or {}
        
        # 查找 postgres 服务配置
        services = compose_data.get("services", {})
        postgres_service = services.get("postgres", {})
        
        if not postgres_service:
            return {}
        
        # 提取环境变量
        env = postgres_service.get("environment", {})
        user = env.get("POSTGRES_USER", "")
        password = env.get("POSTGRES_PASSWORD", "")
        dbname = env.get("POSTGRES_DB", "")
        
        # 提取端口映射（默认 5432）
        ports = postgres_service.get("ports", [])
        port = 5432  # 默认端口
        if ports:
            # ports 格式可能是 ["5432:5432"] 或 ["5432:5432"]
            for port_mapping in ports:
                if isinstance(port_mapping, str):
                    # 格式: "5432:5432"
                    port = int(port_mapping.split(":")[0])
                elif isinstance(port_mapping, dict):
                    # 格式: {"published": 5432, "target": 5432}
                    port = port_mapping.get("published", 5432)
                break
        
        return {
            "user": user,
            "password": password,
            "dbname": dbname,
            "host": "localhost",  # 从宿主机访问，使用 localhost
            "port": port
        }
    except Exception as e:
        print(f"警告: 无法读取 docker-compose.yml: {e}")
        return {}


def get_database_url() -> str:
    """获取数据库连接 URL（优先使用环境变量，否则从 docker-compose.yml 读取）"""
    # 优先使用环境变量
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # 从 docker-compose.yml 读取配置
    config = load_docker_compose_config()
    if config.get("user") and config.get("password") and config.get("dbname"):
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        user = config["user"]
        password = config["password"]
        dbname = config["dbname"]
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        print(f"提示: 从 docker-compose.yml 读取数据库配置")
        print(f"      数据库: {dbname}@{host}:{port}")
        return database_url
    
    # 如果都不可用，返回空字符串
    return ""


def load_watch_dict() -> dict:
    """加载 watch.yaml 字典文件"""
    # 字典文件路径: GoodsHunter/i18n/dictionaries/watch.yaml
    dict_path = project_root / "i18n" / "dictionaries" / "watch.yaml"
    
    if not dict_path.exists():
        print(f"错误: 字典文件不存在: {dict_path}")
        print(f"提示: 请确保在 GoodsHunter 项目根目录下运行此脚本")
        print(f"当前项目根目录: {project_root}")
        sys.exit(1)
    
    with open(dict_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def init_brand_translations(conn, watch_dict: dict):
    """初始化品牌翻译表（幂等操作：可重复执行，不会产生冲突）"""
    cursor = conn.cursor()
    
    brand_count = 0
    
    for brand_name, brand_data in watch_dict.items():
        if not isinstance(brand_data, dict):
            continue
        
        aliases = brand_data.get("aliases", [])
        
        # 构建翻译映射
        translations = {
            "en": brand_name,  # 英文标准名
        }
        
        # 添加别名（判断语言）
        for alias in aliases:
            # 判断是否为日文（包含日文字符）
            if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in alias):
                if "ja" not in translations:
                    translations["ja"] = alias
            # 判断是否为中文（包含中文字符）
            elif any('\u4e00' <= char <= '\u9fff' for char in alias):
                if "zh" not in translations:
                    translations["zh"] = alias
            # 其他情况可能是英文变体
            else:
                # 如果英文标准名和别名不同，可以作为英文变体
                if alias.lower() != brand_name.lower():
                    translations["en_variants"] = translations.get("en_variants", [])
                    translations["en_variants"].append(alias)
        
        # 使用 ON CONFLICT 实现幂等插入/更新
        # 如果记录已存在则更新，不存在则插入（完全替换 translations，因为 YAML 是权威来源）
        cursor.execute(
            """
            INSERT INTO brand_translations (brand_name, translations)
            VALUES (%s, %s)
            ON CONFLICT (brand_name) 
            DO UPDATE SET 
                translations = EXCLUDED.translations, 
                updated_at = now()
            """,
            (brand_name, json.dumps(translations, ensure_ascii=False))
        )
        brand_count += 1
    
    cursor.close()
    print(f"✓ 已处理 {brand_count} 个品牌翻译（幂等操作：新增或更新）")


def init_model_name_translations(conn, watch_dict: dict):
    """初始化型号名称翻译表（幂等操作：可重复执行，不会产生冲突）"""
    cursor = conn.cursor()
    
    model_count = 0
    
    for brand_name, brand_data in watch_dict.items():
        if not isinstance(brand_data, dict):
            continue
        
        model_dict = brand_data.get("model_name", {})
        if not isinstance(model_dict, dict):
            continue
        
        for model_name, model_info in model_dict.items():
            if not isinstance(model_info, dict):
                continue
            
            aliases = model_info.get("aliases", [])
            
            # 构建翻译映射
            translations = {
                "en": model_name,  # 英文标准名
            }
            
            # 添加别名（判断语言）
            for alias in aliases:
                # 判断是否为日文
                if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' for char in alias):
                    if "ja" not in translations:
                        translations["ja"] = alias
                # 判断是否为中文
                elif any('\u4e00' <= char <= '\u9fff' for char in alias):
                    if "zh" not in translations:
                        translations["zh"] = alias
                # 其他情况可能是英文变体
                else:
                    if alias.lower() != model_name.lower():
                        translations["en_variants"] = translations.get("en_variants", [])
                        translations["en_variants"].append(alias)
            
            # 使用 ON CONFLICT 实现幂等插入/更新
            # 如果记录已存在则更新，不存在则插入（完全替换 translations，因为 YAML 是权威来源）
            cursor.execute(
                """
                INSERT INTO model_name_translations (brand_name, model_name, translations)
                VALUES (%s, %s, %s)
                ON CONFLICT (brand_name, model_name) 
                DO UPDATE SET 
                    translations = EXCLUDED.translations, 
                    updated_at = now()
                """,
                (brand_name, model_name, json.dumps(translations, ensure_ascii=False))
            )
            model_count += 1
    
    cursor.close()
    print(f"✓ 已处理 {model_count} 个型号名称翻译（幂等操作：新增或更新）")


def init_model_translations(conn, watch_dict: dict):
    """初始化型号编号翻译表（型号编号通常不需要翻译，但保留接口）"""
    # 型号编号通常不需要翻译，这里可以留空或根据实际需求实现
    print("✓ 型号编号翻译表初始化完成（当前无需翻译）")


def main():
    """主函数"""
    database_url = get_database_url()
    if not database_url:
        print("错误: 无法获取数据库连接 URL")
        print("请设置环境变量: export DATABASE_URL='postgresql://user:password@host:port/dbname'")
        print("或者确保 docker-compose.yml 中存在 postgres 服务配置")
        sys.exit(1)
    
    print("=" * 60)
    print("初始化翻译表")
    print("=" * 60)
    
    # 加载字典
    print("\n1. 加载字典文件...")
    watch_dict = load_watch_dict()
    print(f"   加载了 {len(watch_dict)} 个品牌")
    
    # 连接数据库
    print("\n2. 连接数据库...")
    try:
        conn = psycopg2.connect(database_url)
        print("   ✓ 数据库连接成功")
    except Exception as e:
        print(f"   ✗ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 初始化翻译表（使用单个事务确保原子性）
    print("\n3. 初始化翻译表...")
    try:
        # 开始事务（默认 autocommit=False，所以已经是事务模式）
        init_brand_translations(conn, watch_dict)
        init_model_name_translations(conn, watch_dict)
        init_model_translations(conn, watch_dict)
        
        # 所有操作成功，提交事务
        conn.commit()
        print("   ✓ 所有翻译表已成功更新")
    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")
        conn.rollback()
        print("   ✗ 已回滚所有更改")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("初始化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

