#!/bin/bash
# 重置开发环境数据库脚本

set -e

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查 docker-compose.yml 是否存在
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：在 $PROJECT_ROOT 找不到 docker-compose.yml"
    exit 1
fi

# 检测使用 docker compose 还是 docker-compose
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ 错误：未找到 docker compose 或 docker-compose 命令"
    exit 1
fi

echo "⚠️  警告：这将删除所有数据库数据！"
read -p "确认要继续吗？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消操作"
    exit 0
fi

echo "正在停止容器并删除数据卷..."
$DOCKER_COMPOSE down -v

echo "正在重新启动容器（Postgres 和 MinIO）..."
echo "  - Postgres 将自动执行 init.sql"
echo "  - MinIO 将同时启动"
$DOCKER_COMPOSE up -d postgres minio

echo "等待服务启动..."
echo "  - 等待 Postgres 启动..."
sleep 5

echo "检查服务状态..."
echo "  - 检查 Postgres..."
docker exec goodshunter-postgres psql -U goodshunter -d goodshunter -c "\dt" 2>/dev/null || echo "    Postgres 可能还在初始化中，请稍候..."

echo "  - 检查 MinIO..."
if docker ps | grep -q goodshunter-minio; then
    echo "    ✅ MinIO 容器正在运行"
    echo "    MinIO API: http://localhost:9000"
    echo "    MinIO Console: http://localhost:9001"
else
    echo "    ⚠️  MinIO 容器未运行，请检查日志"
fi

echo ""
echo "✅ 数据库重置完成！"
echo "提示：如果表未创建，请等待几秒后再次检查"

