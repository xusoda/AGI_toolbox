#!/bin/bash
# 运行爬虫脚本
# 从 urls.txt 文件读取 URL 列表（每行一个 URL）

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到项目根目录（脚本所在目录的上一级）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# URL 列表文件路径
URLS_FILE="$SCRIPT_DIR/urls.yaml"

# 检查文件是否存在
if [ ! -f "$URLS_FILE" ]; then
    echo "错误: URL 列表文件不存在: $URLS_FILE"
    exit 1
fi

# 执行 Python 脚本
# 使用 -u 参数确保无缓冲输出，让日志实时显示
echo "Running crawl from $URLS_FILE..."
python -u crawler/app/run_with_db.py --urls "$URLS_FILE"

