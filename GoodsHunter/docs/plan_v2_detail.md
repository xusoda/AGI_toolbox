
### 结构要点
- `crawler/`：只负责“抓取 + 解析 + 产出结构化 item”，不要直接耦合 MinIO/缩略图逻辑
- `storage/`：作为基础设施层，提供 DB 与对象存储的稳定接口（Repository + MinIO client）
- `workers/`：承载耗时任务（图片下载、缩略图生成、批量入库等），避免阻塞 API 与 crawler
- `api/`：只做查询与对外契约（不承担抓取/图片生成）
- `web/`：只消费 API，不直接访问 DB/MinIO（除非你采用 CDN URL，浏览器直拉图片）

---

## 3. 数据模型与存储设计

### 3.1 Postgres 表（推荐最小集合）
#### `crawler_log` -- 原始抓取记录
  id           BIGSERIAL,                          -- 数据库中id
  category     TEXT NOT NULL,                      -- 珠宝/手表/包/服饰/...
  site         TEXT NOT NULL,                      -- 主域名，如 commit-watch.co.jp
  item_id      TEXT NOT NULL                       -- 在对方网站上，item对应的id
  raw_json     JSONB NOT NULL,                     -- 原始数据（结构化原文）
  brand_name   TEXT NULL,
  model_name   TEXT NULL,
  model_no     TEXT NULL,
  currency     TEXT NOT NULL DEFAULT 'JPY',
  price        INTEGER NULL,                       -- * 100 以免小数。
- `image_original_key` TEXT NULL
- `image_thumb_300_key` TEXT NULL
- `image_thumb_600_key` TEXT NULL
- `image_sha256` TEXT NULL
  crawl_time   TIMESTAMPTZ NOT NULL,               -- 抓取时间（精确时刻）
  dt           DATE NOT NULL,                      -- 分区键（按天/按月都可，取决于分区策略）


#### `products`
- `id` BIGSERIAL PK
- `site` TEXT NOT NULL
- `product_url` TEXT NOT NULL UNIQUE
- `brand_name` TEXT NULL
- `model` TEXT NULL
- `model_no` TEXT NULL
- `currency` TEXT NOT NULL DEFAULT 'JPY'
- `price` INTEGER NULL
- `is_available` BOOLEAN NULL
- `first_seen_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `last_seen_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `last_scraped_at` TIMESTAMPTZ NULL
- 图片引用（两种任选其一）：
  - 方案 A（推荐）：存 key（简单直观）
    - `image_original_key` TEXT NULL
    - `image_thumb_300_key` TEXT NULL
    - `image_thumb_600_key` TEXT NULL
    - `image_sha256` TEXT NULL
  - 方案 B：FK 引用 `images.id`（更规范，但查询 join 多一步）
    - `image_id` BIGINT NULL FK

索引建议：
- UNIQUE(`product_url`)
- INDEX(`brand_name`)
- INDEX(`model_name`)
- INDEX(`price`)
- INDEX(`last_seen_at` DESC)
- 组合索引：INDEX(`brand_name`, `model_name`)

#### `images`（如采用方案 B 或希望保留图片元数据）
- `id` BIGSERIAL PK
- `source_url` TEXT NOT NULL
- `sha256` TEXT NOT NULL UNIQUE
- `mime` TEXT NULL
- `ext` TEXT NULL
- `bytes` BIGINT NULL
- `width` INT NULL
- `height` INT NULL
- `original_key` TEXT NOT NULL
- `thumb_300_key` TEXT NOT NULL
- `thumb_600_key` TEXT NOT NULL
- `downloaded_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `status` TEXT NOT NULL DEFAULT 'ok'
- `error` TEXT NULL

#### `crawl_runs`（抓取运行记录）
- `id` BIGSERIAL PK
- `site` TEXT NOT NULL
- `job_name` TEXT NOT NULL
- `started_at` TIMESTAMPTZ NOT NULL DEFAULT now()
- `finished_at` TIMESTAMPTZ NULL
- `status` TEXT NOT NULL DEFAULT 'running'
- `items_found` INT NULL
- `items_upserted` INT NULL
- `items_failed` INT NULL
- `error` TEXT NULL

#### `price_history`（可选）
- `id` BIGSERIAL PK
- `product_id` BIGINT NOT NULL
- `price` INT NOT NULL
- `currency` TEXT NOT NULL DEFAULT 'JPY'
- `observed_at` TIMESTAMPTZ NOT NULL DEFAULT now()
索引：INDEX(`product_id`, `observed_at` DESC)

---

### 3.2 MinIO 存储规范

Bucket：
- `watch-images`

对象 Key：
- 原图：`original/{sha256[0:2]}/{sha256}.{ext}`
- 缩略图 300：`thumb/300/{sha256[0:2]}/{sha256}.webp`
- 缩略图 600：`thumb/600/{sha256[0:2]}/{sha256}.webp`

格式策略：
- **原图**：尽量保留源格式（jpeg/png/webp/gif）
- **缩略图**：建议统一 WebP（或 JPEG）以提升加载性能；质量 75–85（可配置）

---

## 4. 抓取与入库策略（与现有 crawler 对接）

### 4.1 统一 Item Schema（crawler 输出）
crawler 产出的最小字段（示例）：
- `site`
- `product_url`
- `brand_name`
- `model_name`
- `model_no`
- `price`（int）
- `currency`（JPY）
- `image_source_url`（列表页图片 url）
- `scraped_at`

> crawler 只负责输出结构化 item；写库与图片处理由 storage/workers 承担。

### 4.2 Upsert 与去重
- 商品去重：`product_url` 唯一
- 图片去重：`sha256` 唯一（内容级）
- Upsert 规则：
  - 已存在：更新可变字段（price、last_seen_at、brand/serial/model 纠正），并更新 `last_scraped_at`
  - 新插入：设置 `first_seen_at` 与 `last_seen_at`
  - 若 price 变化且启用 `price_history`：插入一条 history

### 4.3 图片处理触发条件
- 新商品或 `image_source_url` 变化 → 触发 image_worker
- 若已有 `image_sha256` 且 `source_url` 未变化 → 可跳过下载（可配置）

---

## 5. Worker（图片下载/缩略图/上传）

### 5.1 Image Worker 逻辑
输入（任务消息）：
- `product_id`
- `image_source_url`

处理步骤：
1. 下载图片 bytes（校验 content-type 与大小上限）
2. 计算 `sha256`
3. 判断 `images.sha256` 是否已存在（已存在则复用 keys）
4. 生成缩略图 300/600（webp/jpeg）
5. 上传 MinIO：original + thumbs
6. 写回 DB：
   - 写 `images`（若采用）
   - 更新 `products.image_*_key` 与 `image_sha256`

### 5.2 异步队列（推荐）
本地与云都建议使用 Redis：
- 本地：docker-compose 启动 redis
- 云：替换成托管 Redis（无代码改动，仅切 env）

---

## 6. API 设计（FastAPI）

### 6.1 GET `/items`
Query：
- `page`（default=1）
- `page_size`（default=20，max=100）
- `brand`（可选）
- `serial`（可选）
- `price_min` / `price_max`（可选）
- `sort`（可选）：`newest` / `price_asc` / `price_desc`

Response：
- `page, page_size, total, items[]`
- item 字段（建议）：
  - `id, product_url, brand_name, model_name, model_no, price, currency, last_seen_at`
  - `image_thumb_url`（默认 300）
  - `image_url`（可返回 600 或 original，按前端策略）

### 6.2 GET `/items/{id}`
返回详情：
- 基础字段 + `image_thumb_300_url` / `image_thumb_600_url` / `image_original_url`

### 6.3 图片 URL 策略（两种模式）
- **预签名模式（默认）**：MinIO 私有桶
  - API 在响应中为 key 生成短时效 URL（例如 15 分钟）
- **CDN 模式（上线推荐）**：
  - MinIO 对象公开读（或通过网关） + CDN 域名
  - API 直接拼接 `CDN_BASE_URL + key`

> 两种模式通过环境变量切换，前端无需变更。

---

## 7. Web GUI（React/Vue）

### 7.1 页面
- 列表页 `/items`
  - 筛选（brand/serial/价格区间）
  - 排序（newest/price）
  - 分页（page/page_size）
  - 表格列：缩略图（300）、brand、serial、model_no、price、外链、详情按钮
- 详情页 `/items/:id`
  - 展示 600 图（首屏），点击后加载 original

### 7.2 性能建议（百万级数据）
- 列表页只用 300 缩略图，懒加载图片（IntersectionObserver）
- 后端索引保证常用筛选排序
- 深分页后续可升级为 keyset pagination（不影响当前 API 基本形态，可新增参数）

---

## 8. macOS 本地部署（优先）与云部署无缝切换

### 8.1 本地部署方式：Docker Compose（推荐）
本地启动组件：
- Postgres
- MinIO
- Redis（推荐）
- API（FastAPI）
- Worker（image_worker）
- Web（可选：本地 `npm run dev`；生产可用 Nginx 容器）

优势：
- macOS 一键启动
- 与云部署一致（同容器镜像与 env）
- 数据可持久化（docker volume）

### 8.2 配置策略（本地/云统一）
- 使用 `.env`（本地）+ 环境变量（云）
- `configs/app.yaml` 可作为默认配置模板，但最终以 env 覆盖为准

关键环境变量（建议统一命名）：
- `DATABASE_URL=postgresql+psycopg://...`
- `REDIS_URL=redis://...`
- `MINIO_ENDPOINT=http://minio:9000`
- `MINIO_ACCESS_KEY=...`
- `MINIO_SECRET_KEY=...`
- `MINIO_BUCKET=watch-images`
- `IMAGE_URL_MODE=presign|cdn`
- `PRESIGN_TTL_SECONDS=900`
- `CDN_BASE_URL=https://cdn.example.com/watch-images/`（仅 CDN 模式）

### 8.3 云部署无缝切换策略
保持代码不变，替换基础设施端点：
- Postgres：本地容器 → 云托管 Postgres（RDS/CloudSQL 等）
- MinIO：本地 MinIO → 云 MinIO 集群或直接 S3（S3 兼容，代码不变）
- Redis：本地 redis → 云托管 Redis
- Web：静态托管/CDN；API：容器平台（ECS/K8s/Cloud Run）

迁移要点：
- MinIO/S3 保持同一 key 规则（original/thumb/300/thumb/600），前端与 API 不受影响
- API 的 `IMAGE_URL_MODE` 从 presign 切换到 cdn 后，仍保持字段名不变

---

## 9. 交付与验收标准（不含里程碑）

### 9.1 功能验收
- crawler 输出 item 可成功 upsert 到 Postgres（可重复运行不产生重复数据）
- image_worker 成功下载图片并生成 300/600 缩略图写入 MinIO
- API：
  - `/items` 支持分页、筛选、排序，并返回可用的 `image_thumb_url` 与 `image_url`
  - `/items/{id}` 返回详情与 3 种图 URL
- Web GUI：
  - 列表可浏览、筛选、排序、分页
  - 缩略图可加载，详情可查看大图

### 9.2 可运维性验收
- 所有组件可在 macOS 本地通过 docker-compose 启动
- 通过环境变量可以切换到云端 Postgres/MinIO/Redis，无需改代码
- 基础日志可定位：抓取失败、图片失败、API 错误

---

## 10. 关键工程决策（建议默认值）

- DB：Postgres（百万级查询与索引更稳）
- 图片：MinIO（S3 兼容）+ 原图保留 + 缩略图 webp
- 图片不入 DB BLOB：DB 只存 keys/hash/元数据（可扩展与性能更优）
- URL 模式：本地默认 presign，上线切换 cdn
- 队列：推荐引入 Redis + worker，避免 crawler 与图片处理耦合

---
