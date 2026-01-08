#!/bin/bash
# 搜索功能完整设置脚本
# 包括数据库索引初始化和服务更新

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  搜索功能完整设置脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 步骤 1: 初始化数据库索引
echo -e "${YELLOW}[步骤 1/2] 初始化数据库索引...${NC}"
"${SCRIPT_DIR}/init_search_indexes.sh" "$@"

if [ $? -ne 0 ]; then
    echo -e "${RED}数据库索引初始化失败，请检查错误信息${NC}"
    exit 1
fi

echo ""

# 步骤 2: 更新服务
echo -e "${YELLOW}[步骤 2/2] 更新服务...${NC}"
"${SCRIPT_DIR}/update_service.sh"

if [ $? -ne 0 ]; then
    echo -e "${RED}服务更新失败，请检查错误信息${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  搜索功能设置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}搜索功能已启用，可以访问以下端点：${NC}"
echo -e "  ${BLUE}搜索商品:${NC} GET /api/search?q=<关键词>"
echo -e "  ${BLUE}搜索建议:${NC} GET /api/search/suggest?q=<关键词前缀>"
echo ""
echo -e "${YELLOW}示例：${NC}"
echo -e "  curl 'http://localhost:8000/api/search?q=Rolex&page=1&page_size=20'"
echo -e "  curl 'http://localhost:8000/api/search/suggest?q=Role&size=5'"
echo ""
