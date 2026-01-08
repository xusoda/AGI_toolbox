#!/bin/bash
# 搜索功能服务更新脚本
# 用于更新 API 服务以支持搜索功能

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始更新服务以支持搜索功能...${NC}"

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 检查是否在 Docker 环境中
if [ -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}检测到 Docker Compose 环境${NC}"
    
    # 检查服务是否运行
    if docker compose ps | grep -q "goodshunter-api"; then
        echo -e "${YELLOW}正在重启 API 服务...${NC}"
        docker compose restart api
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ API 服务重启成功！${NC}"
            echo -e "${GREEN}搜索功能已启用，可以访问以下端点：${NC}"
            echo -e "  - GET /api/search?q=<关键词>"
            echo -e "  - GET /api/search/suggest?q=<关键词前缀>"
        else
            echo -e "${RED}✗ API 服务重启失败！${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}API 服务未运行，正在启动...${NC}"
        docker compose up -d api
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ API 服务启动成功！${NC}"
        else
            echo -e "${RED}✗ API 服务启动失败！${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}非 Docker 环境，请手动重启 API 服务${NC}"
    echo -e "请执行以下命令重启服务："
    echo -e "  cd services/api && ./run.sh"
fi

echo -e "${GREEN}服务更新完成！${NC}"
