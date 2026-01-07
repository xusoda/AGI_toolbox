#!/bin/bash
# 运行 watchnian 爬虫脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到项目根目录（脚本所在目录的上一级）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 执行 Python 脚本
# 使用 -u 参数确保无缓冲输出，让日志实时显示
echo "Running crawl..."
python -u crawler/app/run_with_db.py --urls "https://watchnian.com/shop/r/rwatch_supd/?filtercode13=1#block_of_filter"
python -u crawler/app/run_with_db.py --urls "https://commit-watch.co.jp/collections/onsale"

