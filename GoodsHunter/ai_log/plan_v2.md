# Plan.md — Watch Listings Crawler + Catalog System (Local macOS → Cloud-Ready)

## 0. 背景与目标

你当前已完成 `crawler/`（抓取 + 解析）。本计划在此基础上补齐：

- **Storage 层**：Postgres（结构化数据）+ MinIO（图片原图与缩略图 300/600）
- **Service 层**：API（建议 FastAPI），提供分页/筛选/排序与详情接口，并返回图片可访问 URL（预签名或 CDN）
- **Presentation 层**：Web GUI（React/Vue），表格列表 + 图片缩略图 + 详情页
- **Local-first 部署**：优先 macOS 本地一键启动（Docker Compose），并确保后续可无缝切换到云部署（同一套配置约束与接口契约）

---

## 1. 总体架构

### 1.1 组件清单
- **crawler**（已完成）
  - 负责抓取页面/接口，解析字段，输出结构化 items
- **storage**
  - Postgres：商品元数据、抓取状态、去重索引、（可选）价格历史
  - MinIO：原图 + 300/600 缩略图
- **workers**
  - Image Worker：下载图片、hash 去重、生成缩略图、上传 MinIO、写回 DB
  -（可选）Crawl Orchestrator：负责定时/批量运行 crawler，并记录 crawl_run
- **api**
  - FastAPI：对外提供 `GET /items` 与 `GET /items/{id}`
  - 负责签名 MinIO URL 或拼接 CDN URL
- **web**
  - React/Vue：列表页（表格+缩略图+筛选排序分页）与详情页（600/原图）
- **infra**
  - Docker Compose：macOS 本地部署
  - 统一 `.env` 与配置文件，保证本地/云部署只需切换环境变量与 endpoint

### 1.2 数据流
1. crawler 抓取 → 解析 items → 写入 Postgres（upsert products）
2. 对需要处理图片的商品，产生 image 任务 → Image Worker
3. Image Worker 下载图片 → 计算 sha256 → 生成 300/600 缩略图 → 上传 MinIO → 更新 Postgres（images + products.image_keys）
4. Web GUI 调用 API → API 查询 Postgres → 返回 items 与图片 URL → 浏览器加载缩略图/原图

---

## 2. 目录结构设计（基于现有 crawler/ 与 storage/ 扩展）

> 目标：清晰分层、可单独运行、可测试、可容器化；本地与云环境切换仅依赖配置。

建议最终项目结构如下（在保留你现有目录的基础上扩展）：

