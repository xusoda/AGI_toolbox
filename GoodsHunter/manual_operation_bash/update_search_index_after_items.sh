#!/bin/bash
# 更新商品后，更新ES索引脚本
# 支持增量同步或全量同步

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到项目根目录（脚本所在目录的上一级）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查参数
BATCH_SIZE=100
REBUILD_ALL=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild-all)
            REBUILD_ALL=true
            shift
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --rebuild-all          全量同步（同步所有商品）"
            echo "  --batch-size SIZE      批量大小（默认: 100）"
            echo "  -h, --help            显示此帮助信息"
            echo ""
            echo "说明:"
            echo "  如果不指定 --rebuild-all，脚本会同步所有商品（全量同步）"
            echo "  指定 --rebuild-all 也是全量同步，两者功能相同"
            echo ""
            echo "示例:"
            echo "  # 全量同步所有商品"
            echo "  $0"
            echo ""
            echo "  # 全量同步，指定批量大小"
            echo "  $0 --batch-size 200"
            exit 0
            ;;
        *)
            echo "错误: 未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 执行Python脚本
# 使用 -u 参数确保无缓冲输出，让日志实时显示
echo "更新商品后，同步ES索引..."
python -u -m search.scripts.sync_all_data --batch-size "$BATCH_SIZE"
