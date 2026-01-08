#!/bin/bash
# GoodsHunter 一键启动脚本
# 启动所有服务：PostgreSQL, MinIO, API, Web前端

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

# 虚拟环境路径（GoodsHunter 的父目录的根目录下的 .venv）
VENV_PATH="$PROJECT_ROOT/../.venv"

# 日志目录
LOG_DIR="$SCRIPT_DIR/log"
DOCKER_LOG="$LOG_DIR/docker-compose.log"
API_LOG="$LOG_DIR/api.log"
WEB_LOG="$LOG_DIR/web.log"

# 初始化进程 ID 变量
DOCKER_PID=""
API_LOG_PID=""
WEB_PID=""

# 创建日志目录
echo -e "${BLUE}创建日志目录...${NC}"
mkdir -p "$LOG_DIR"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查并激活虚拟环境（如果需要本地运行 API 服务）
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        echo -e "${BLUE}找到虚拟环境: $VENV_PATH${NC}"
        source "$VENV_PATH/bin/activate"
        echo -e "${GREEN}✓ 已激活虚拟环境${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 警告: 未找到虚拟环境 $VENV_PATH${NC}"
        echo "如果需要本地运行 API 服务，请先创建虚拟环境:"
        echo "  cd $PROJECT_ROOT && python3 -m venv .venv"
        return 1
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}检查系统依赖...${NC}"

    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 Docker${NC}"
        echo "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # 检查 Docker Compose
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 Docker Compose${NC}"
        echo "请确保安装了包含 Docker Compose 的 Docker Desktop 或 Docker CLI"
        exit 1
    fi

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 Node.js${NC}"
        echo "请先安装 Node.js: https://nodejs.org/"
        exit 1
    fi

    # 检查 Python3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 Python3${NC}"
        exit 1
    fi

    # 检查虚拟环境（仅提示，不强制要求，因为 API 服务通过 Docker 运行）
    activate_venv || true

    echo -e "${GREEN}✓ 所有依赖检查通过${NC}"
}

# 停止并清理现有服务
cleanup_services() {
    echo -e "${BLUE}清理现有服务...${NC}"

    # 停止并移除现有容器
    docker compose down --remove-orphans 2>/dev/null || true

    # 停止本地进程
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true

    echo -e "${GREEN}✓ 服务清理完成${NC}"
}

# 启动 Docker Compose 服务
start_docker_services() {
    echo -e "${BLUE}启动 Docker Compose 服务 (PostgreSQL, MinIO, API)...${NC}"

    # 启动服务（后台运行）
    docker compose up -d 2>&1 | tee "$DOCKER_LOG" &

    DOCKER_PID=$!

    # 等待服务启动
    echo -e "${YELLOW}等待服务启动...${NC}"

    # 等待 PostgreSQL
    echo "等待 PostgreSQL..."
    for i in {1..30}; do
        if docker compose exec -T postgres pg_isready -U goodshunter -d goodshunter > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL 已就绪${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ PostgreSQL 启动超时${NC}"
            echo "检查容器状态..."
            docker compose ps postgres
            kill $DOCKER_PID 2>/dev/null || true
            exit 1
        fi
    done

    # 等待 MinIO
    echo "等待 MinIO..."
    for i in {1..30}; do
        if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
            echo -e "${GREEN}✓ MinIO 已就绪${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ MinIO 启动超时${NC}"
            echo "检查容器状态..."
            docker compose ps minio
            kill $DOCKER_PID 2>/dev/null || true
            exit 1
        fi
    done

    # 等待 API
    echo "等待 API 服务..."
    for i in {1..60}; do
        # 先检查健康检查端点（更轻量）
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API 服务已就绪${NC}"
            break
        fi
        # 如果健康检查失败，尝试检查 docs 端点
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API 服务已就绪${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 60 ]; then
            echo -e "${RED}❌ API 服务启动超时${NC}"
            echo "检查容器状态..."
            docker compose ps api
            echo "查看 API 服务日志..."
            docker compose logs --tail=30 api
            kill $DOCKER_PID 2>/dev/null || true
            exit 1
        fi
    done

    # 启动 API 服务日志捕获（后台运行）
    echo "启动 API 服务日志捕获..."
    # 先获取历史日志
    docker compose logs api > "$API_LOG" 2>&1 || true
    # 然后开始实时跟踪日志
    docker compose logs -f api >> "$API_LOG" 2>&1 &
    API_LOG_PID=$!

    echo -e "${GREEN}✓ 所有 Docker 服务启动完成${NC}"
}

# 启动 Web 前端服务
start_web_service() {
    echo -e "${BLUE}启动 Web 前端服务...${NC}"

    cd "$PROJECT_ROOT/services/web"

    # 检查依赖
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install 2>&1 | tee "$WEB_LOG" || {
            echo -e "${RED}❌ 前端依赖安装失败${NC}"
            exit 1
        }
    fi

    # 启动前端服务（后台运行）
    echo "启动前端开发服务器..."
    npm run dev 2>&1 | tee -a "$WEB_LOG" &
    WEB_PID=$!

    # 等待前端服务启动
    echo -e "${YELLOW}等待前端服务启动...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Web 前端服务已就绪${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Web 前端服务启动超时${NC}"
            kill $WEB_PID 2>/dev/null || true
            exit 1
        fi
    done

    cd "$PROJECT_ROOT"
}

# 显示服务信息
show_service_info() {
    echo ""
    echo -e "${GREEN}🎉 所有服务启动成功！${NC}"
    echo ""
    echo -e "${BLUE}📋 服务访问地址：${NC}"
    echo "----------------------------------------"
    echo -e "${GREEN}🌐 Web 前端:    http://localhost:3000${NC}"
    echo -e "${GREEN}🔌 API 服务:    http://localhost:8000${NC}"
    echo -e "${GREEN}📊 API 文档:    http://localhost:8000/docs${NC}"
    echo -e "${GREEN}🗄️  PostgreSQL:  localhost:5432${NC}"
    echo -e "${GREEN}📦 MinIO API:    http://localhost:9000${NC}"
    echo -e "${GREEN}🎛️  MinIO Console: http://localhost:9001${NC}"
    echo "----------------------------------------"
    echo ""
    echo -e "${BLUE}📁 日志文件位置：${NC}"
    echo "Docker 服务日志: $DOCKER_LOG"
    echo "API 服务日志:     $API_LOG"
    echo "Web 前端日志:     $WEB_LOG"
    echo ""
    echo -e "${YELLOW}💡 提示：按 Ctrl+C 停止所有服务${NC}"
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服务...${NC}"

    # 停止后台进程
    kill $DOCKER_PID 2>/dev/null || true
    kill $WEB_PID 2>/dev/null || true
    kill $API_LOG_PID 2>/dev/null || true

    # 停止 Docker 服务
    docker compose down 2>/dev/null || true

    echo -e "${GREEN}✓ 所有服务已停止${NC}"
    exit 0
}

# 主函数
main() {
    echo -e "${BLUE}🚀 GoodsHunter 一键启动脚本${NC}"
    echo "========================================"

    # 注册清理函数
    trap cleanup SIGINT SIGTERM

    # 执行启动流程
    check_dependencies
    cleanup_services
    start_docker_services
    start_web_service
    show_service_info

    # 等待用户中断
    echo -e "${YELLOW}服务正在运行中... 按 Ctrl+C 停止${NC}"
    wait
}

# 执行主函数
main "$@"