#!/bin/bash
# Web 前端启动脚本

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo ""
    echo "请先安装 Node.js："
    echo ""
    echo "方式1: 使用 Homebrew (推荐)"
    echo "  brew install node"
    echo ""
    echo "方式2: 使用 nvm (Node Version Manager)"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  nvm install --lts"
    echo ""
    echo "方式3: 从官网下载"
    echo "  https://nodejs.org/"
    echo ""
    exit 1
fi

# 显示 Node.js 版本
NODE_VERSION=$(node --version)
echo "✓ Node.js 版本: $NODE_VERSION"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 运行开发服务器
echo "🚀 启动前端开发服务器..."
npm run dev

