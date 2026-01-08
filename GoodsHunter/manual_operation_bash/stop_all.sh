#!/bin/bash
# GoodsHunter 停止所有服务脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo -e "${BLUE}🛑 停止 GoodsHunter 所有服务${NC}"
echo "==================================="

# 停止本地进程
echo -e "${YELLOW}停止本地进程...${NC}"
pkill -f "uvicorn.*app.main:app" 2>/dev/null || echo "API 服务未运行"
pkill -f "vite" 2>/dev/null || echo "Web 前端服务未运行"

# 停止 Docker 服务
echo -e "${YELLOW}停止 Docker 服务...${NC}"
docker compose down --remove-orphans 2>&1 || echo "Docker Compose 服务未运行"

# 清理可能残留的容器
echo -e "${YELLOW}清理残留容器...${NC}"
docker rm -f goodshunter-postgres goodshunter-minio goodshunter-api 2>/dev/null || true

echo -e "${GREEN}✓ 所有服务已停止${NC}"
echo ""
echo -e "${BLUE}💡 如需重新启动，请运行: ./manual_operation_bash/start_all.sh${NC}"