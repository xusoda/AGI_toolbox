#!/bin/bash
# 搜索功能数据库索引初始化脚本
# 用于为搜索功能添加必要的索引

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-goodshunter}"
DB_USER="${DB_USER:-goodshunter}"
DB_PASSWORD="${DB_PASSWORD:-goodshunter123}"

# 从环境变量或参数获取配置
if [ -n "$1" ]; then
    DB_HOST="$1"
fi
if [ -n "$2" ]; then
    DB_PORT="$2"
fi
if [ -n "$3" ]; then
    DB_NAME="$3"
fi
if [ -n "$4" ]; then
    DB_USER="$4"
fi
if [ -n "$5" ]; then
    DB_PASSWORD="$5"
fi

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/init_search_indexes.sql"

echo -e "${GREEN}开始初始化搜索功能数据库索引...${NC}"
echo -e "数据库: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# 检查 SQL 文件是否存在
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}错误: SQL 文件不存在: $SQL_FILE${NC}"
    exit 1
fi

# 执行 SQL
export PGPASSWORD="$DB_PASSWORD"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 搜索功能数据库索引初始化成功！${NC}"
else
    echo -e "${RED}✗ 搜索功能数据库索引初始化失败！${NC}"
    exit 1
fi
