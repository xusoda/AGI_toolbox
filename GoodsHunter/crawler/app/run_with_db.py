"""CLI入口：批量URL -> 结果JSONL + 数据库存储（示例）"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# 将项目根目录添加到Python路径
_current_file = Path(__file__).resolve()
_crawler_root = _current_file.parent.parent
_project_root = _crawler_root.parent
if str(_crawler_root) not in sys.path:
    sys.path.insert(0, str(_crawler_root))
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(_project_root / ".env")

from core.registry import ProfileRegistry
from core.types import Profile
from fetch.playwright_fetcher import PlaywrightFetcher
from extract.engine import ExtractEngine
from storage.output.fileWriter import FileWriter
from storage.output.db_writer import DBWriter


async def process_urls(
    urls: List[str],
    profiles_path: str,
    output_path: Optional[str] = None,
    use_db: bool = True,
):
    """
    处理URL列表（支持数据库存储）
    
    Args:
        urls: URL列表
        profiles_path: profiles.yaml路径
        output_path: 输出JSONL文件路径（可选）
        use_db: 是否写入数据库（默认True）
    """
    # 初始化组件
    registry = ProfileRegistry(profiles_path)
    fetcher = PlaywrightFetcher()
    engine = ExtractEngine()
    
    # 初始化数据库写入器（如果启用）
    db_writer = None
    if use_db:
        try:
            db_writer = DBWriter()
            print("[DBWriter] 数据库写入器已初始化")
        except Exception as e:
            print(f"[DBWriter] 警告: 数据库写入器初始化失败: {e}")
            print("[DBWriter] 将继续运行，但不写入数据库")
            use_db = False

    try:
        await fetcher.start()

        for url in urls:
            print(f"处理: {url}")

            # 匹配Profile
            profile = registry.match_profile(url)
            if not profile:
                print(f"  警告: 未找到匹配的Profile，跳过")
                continue

            print(f"  使用Profile: {profile.name}")

            try:
                # 抓取页面
                page = await fetcher.fetch(url, profile.fetch)

                # 抽取字段
                record = engine.extract(page, profile)

                # 保存记录（包括JSONL、图片和文本文件）
                stats = FileWriter.save_record(
                    record=record,
                    site=profile.site,
                    output_path=output_path
                )

                # 写入数据库（如果启用）
                if use_db and db_writer:
                    try:
                        db_count = db_writer.write_record(
                            record=record,
                            site=profile.site
                        )
                        print(f"  [DBWriter] 已写入 {db_count} 条记录到数据库")
                    except Exception as e:
                        print(f"  [DBWriter] 写入数据库失败: {e}")

                # 显示提取结果
                if "items" in record.data:
                    items = record.data["items"]
                    print(f"  完成: 提取了 {len(items)} 个列表项")
                    if items:
                        # 显示第一个项的字段信息（排除内部字段）
                        first_item = items[0]
                        display_keys = [k for k in first_item.keys() if not k.startswith("_")]
                        print(f"  每个项包含字段: {display_keys}")
                        # 显示示例数据（排除图片数据）
                        display_item = {k: v for k, v in first_item.items() if not k.startswith("_") and k != "image"}
                        if "_image_data" in first_item:
                            display_item["_image_data"] = f"<binary data, {len(first_item['_image_data'])} bytes>"
                        print(f"  示例项数据: {display_item}")
                else:
                    print(f"  完成: 提取了 {len(record.data)} 个字段")
                    if record.data:
                        print(f"  字段: {list(record.data.keys())}")
                
                if record.errors:
                    print(f"  警告: {len(record.errors)} 个错误")
                    for error in record.errors:
                        print(f"    - {error.field}: {error.error}")

            except Exception as e:
                print(f"  错误: {e}")
                continue

    finally:
        await fetcher.stop()
        if db_writer:
            db_writer.close()


def load_urls_from_file(file_path: str) -> List[str]:
    """
    从文件加载URL列表
    
    Args:
        file_path: URL文件路径（每行一个URL）
        
    Returns:
        URL列表
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"URL文件不存在: {file_path}")

    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith("#"):  # 忽略空行和注释
                urls.append(url)

    return urls


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="网页抓取和内容解析工具（支持数据库存储）")
    parser.add_argument(
        "--urls",
        type=str,
        required=True,
        help="URL文件路径（每行一个URL）或单个URL",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=False,
        default=None,
        help="输出JSONL文件路径（可选，如果不指定则只保存图片和文本文件）",
    )
    parser.add_argument(
        "--profiles",
        type=str,
        default="profiles",
        help="Profile配置文件路径或目录（默认: profiles）",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="禁用数据库写入",
    )

    args = parser.parse_args()

    # 处理profiles路径：如果是相对路径，则基于crawler目录解析
    profiles_path = Path(args.profiles)
    if not profiles_path.is_absolute():
        # 相对路径：基于crawler目录
        profiles_path = _crawler_root / profiles_path
    profiles_path_str = str(profiles_path.resolve())

    # 加载URLs
    urls_path = Path(args.urls)
    if urls_path.exists():
        urls = load_urls_from_file(args.urls)
    else:
        # 假设是单个URL
        urls = [args.urls]

    if not urls:
        print("错误: 没有找到有效的URL")
        return

    print(f"找到 {len(urls)} 个URL")
    print(f"使用profiles路径: {profiles_path_str}")

    # 运行异步处理
    asyncio.run(process_urls(
        urls, 
        profiles_path_str, 
        args.out,
        use_db=not args.no_db
    ))

    if args.out:
        print(f"完成！结果已保存到: {args.out}")
    else:
        print("完成！图片和文本文件已保存到配置的目录")


if __name__ == "__main__":
    main()

