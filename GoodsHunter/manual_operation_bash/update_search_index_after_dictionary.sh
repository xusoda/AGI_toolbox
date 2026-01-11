#!/bin/bash
# 更新词典后，更新ES索引脚本
# 支持增量更新（仅更新受影响的商品）或全量重建

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到项目根目录（脚本所在目录的上一级）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查参数
REBUILD_ALL=false
BRANDS=""
MODELS=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild-all)
            REBUILD_ALL=true
            shift
            ;;
        --brands)
            BRANDS="$2"
            shift 2
            ;;
        --models)
            MODELS="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --rebuild-all          全量重建索引（更新所有商品）"
            echo "  --brands BRANDS        更新的品牌列表（空格分隔，如: 'Rolex Omega'）"
            echo "  --models JSON          更新的型号字典（JSON格式，如: '{\"Rolex\": [\"Submariner\", \"Datejust\"]}'）"
            echo "  -h, --help            显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  # 全量重建索引"
            echo "  $0 --rebuild-all"
            echo ""
            echo "  # 增量更新指定品牌"
            echo "  $0 --brands 'Rolex Omega'"
            echo ""
            echo "  # 增量更新指定型号"
            echo "  $0 --models '{\"Rolex\": [\"Submariner\", \"Datejust\"]}'"
            echo ""
            echo "  # 同时更新品牌和型号"
            echo "  $0 --brands 'Rolex' --models '{\"Rolex\": [\"Submariner\"]}'"
            exit 0
            ;;
        *)
            echo "错误: 未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 构建Python脚本参数
PYTHON_ARGS=""

if [ "$REBUILD_ALL" = true ]; then
    PYTHON_ARGS="--rebuild-all"
elif [ -n "$BRANDS" ] || [ -n "$MODELS" ]; then
    if [ -n "$BRANDS" ]; then
        # 将品牌列表转换为Python脚本参数
        PYTHON_ARGS="$PYTHON_ARGS --brands $BRANDS"
    fi
    if [ -n "$MODELS" ]; then
        PYTHON_ARGS="$PYTHON_ARGS --models '$MODELS'"
    fi
else
    echo "错误: 必须指定 --rebuild-all 或 --brands/--models"
    echo "使用 --help 查看帮助信息"
    exit 1
fi

# 执行Python脚本
# 使用 -u 参数确保无缓冲输出，让日志实时显示
echo "更新词典后，更新ES索引..."
python -u -m search.scripts.update_aliases $PYTHON_ARGS
