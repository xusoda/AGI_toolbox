# GoodsHunter 前端架构实现指南

本文档说明如何启动和使用前端浏览系统。

## 架构概述

采用三层架构：
- **Data Layer**: PostgreSQL + MinIO（已有）
- **Service Layer**: FastAPI（新增）
- **Presentation Layer**: React + TypeScript + Vite（新增）

## 前置要求

### 必需软件

1. **Node.js** (v18 或更高版本)
   - 使用 Homebrew: `brew install node`
   - 使用 nvm: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash` 然后 `nvm install --lts`
   - 或从官网下载: https://nodejs.org/

2. **Python 3.11+**
   - macOS 通常已预装，或使用 `brew install python3`

3. **Docker & Docker Compose**
   - 用于运行 PostgreSQL 和 MinIO

### 验证安装

```bash
# 检查 Node.js
node --version  # 应显示 v18.x.x 或更高

# 检查 npm
npm --version  # 应显示 9.x.x 或更高

# 检查 Python
python3 --version  # 应显示 Python 3.11.x 或更高

# 检查 Docker
docker --version
docker-compose --version
```

## 快速开始

### 1. 启动基础设施

```bash
# 启动 PostgreSQL 和 MinIO
docker-compose up -d postgres minio
```

### 2. 启动 API 服务

```bash
cd services/api

# 方式1: 使用脚本（推荐）
chmod +x run.sh
./run.sh

# 方式2: 手动启动
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 服务将在 `http://localhost:8000` 启动。

### 3. 启动前端服务

```bash
cd services/web

# 方式1: 使用脚本（推荐）
chmod +x run.sh
./run.sh

# 方式2: 手动启动
npm install
npm run dev
```

前端服务将在 `http://localhost:3000` 启动。

**注意**: 如果遇到 "未找到 Node.js" 错误，请先安装 Node.js（见前置要求部分）。

## 功能说明

### API 端点

- `GET /api/items` - 获取商品列表
  - 查询参数：
    - `page`: 页码（默认 1）
    - `page_size`: 每页数量（默认 20，最大 100）
    - `status`: 商品状态（默认 active）
    - `sort`: 排序方式（last_seen_desc/price_asc/price_desc）

- `GET /api/items/{id}` - 获取商品详情

### 前端页面

- `/` - 商品列表页（两列网格布局，移动端优先）
- `/items/:id` - 商品详情页（大图 + 字段信息 + 外链）

## 配置说明

### API 服务配置

环境变量（`services/api/.env` 或系统环境变量）：

```bash
DATABASE_URL=postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=watch-images
IMAGE_URL_MODE=presign  # 或 cdn
CDN_BASE_URL=  # CDN 模式时使用
```

### 前端配置

前端通过 Vite 代理配置自动将 `/api` 请求代理到后端。

如需自定义，创建 `services/web/.env`：

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

## Docker 部署

使用 Docker Compose 一键启动所有服务：

```bash
# 启动所有服务（PostgreSQL + MinIO + API）
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

注意：前端开发建议使用本地 `npm run dev`，生产环境再构建 Docker 镜像。

## 开发说明

### 代码结构

```
services/
  api/                    # FastAPI 后端
    app/
      main.py             # 应用入口
      settings.py         # 配置
      db/                 # 数据库相关
        models.py         # ORM 模型
        queries.py        # 查询函数
        session.py        # 会话管理
      routers/            # 路由
        items.py          # 商品路由
      schemas/            # Pydantic Schema
        items.py
      services/           # 业务服务
        images.py         # 图片 URL 生成
  web/                    # React 前端
    src/
      api/                # API 客户端
        http.ts           # HTTP 封装
        items.ts          # 商品 API
        types.ts          # 类型定义
      pages/              # 页面组件
        ItemsListPage.tsx
        ItemDetailPage.tsx
      components/         # 通用组件
        ItemCard.tsx
        PaginationBar.tsx
        LoadingSkeleton.tsx
      styles/             # 样式
        global.css
```

### 样式设计

- 简洁风格，移动端优先
- 响应式设计：移动端 2 列，平板 3 列，桌面 4 列
- 使用 CSS Grid 实现布局
- 卡片式设计，悬停效果

## 后续改进

- [ ] 添加筛选功能（品牌、价格区间等）
- [ ] 添加搜索功能
- [ ] 优化图片加载（懒加载、占位图）
- [ ] 添加收藏功能
- [ ] 添加价格变化趋势图
- [ ] 优化移动端体验（下拉刷新、无限滚动）

