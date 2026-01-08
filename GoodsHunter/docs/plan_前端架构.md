下面给出一套可直接落地的 **三层结构（Data / Service / Presentation）** 方案，并按你要求的 **MVP：商品列表（移动端两列+分页）→ 商品详情（大图+外链）** 输出“项目骨架级”的目录结构与页面设计细节。

---

## 1) 三层结构总体设计

### 1.1 Data Layer（你已具备）

* **Postgres**：`crawler_item`（目录表，APP/Web 查询主表）
* **MinIO**：图片对象（original / 300 / 600），数据库只存 `*_key` 与 `sha256`
* （建议补齐）**product_url**：详情页外链需要

  * 你当前表结构里没有 `product url` 字段，建议加一列：

    * `product_url TEXT NULL`
  * 来源：抓取时从列表/详情页写入（最可靠）；不要在前端拼 URL。

> 生产级建议索引（支撑分页/排序/筛选）

* `(status, last_seen_dt DESC)`
* `(brand_name)`、`(model_name)`、`(model_no)`
* `(price)`
* `(site, category)`

---

### 1.2 Service Layer（API 服务，推荐 FastAPI）

API 的职责非常明确：

1. 从 Postgres 读取商品数据（分页、排序）
2. 把 `image_*_key` 转成可访问 URL（**presign** 或 **CDN 拼接**）
3. 返回给前端最小字段集合

#### 图片 URL 策略（本地/云无缝切换关键）

* `IMAGE_URL_MODE=presign`（本地默认推荐）

  * API 调 MinIO 生成 **预签名 URL**（有效期 10–30 分钟）
* `IMAGE_URL_MODE=cdn`（上云后推荐）

  * API 直接返回 `CDN_BASE_URL + "/" + key`

前端永远只消费 `image_thumb_url / image_url / image_original_url`，不关心 MinIO。

#### MVP API（只要两个）

1. **GET /items**

* Query：

  * `page`（默认 1）
  * `page_size`（默认 20，最大建议 100）
  * `status`（默认 `active`）
  * `sort`（默认 `last_seen_desc`；可选 `price_asc/price_desc`）
* Response：

  * `total`
  * `page`
  * `page_size`
  * `items[]`（每个包含：`id, brand_name, model_name, model_no, currency, price, image_thumb_url, last_seen_dt, status`）

2. **GET /items/{id}**

* Response：

  * 商品全字段（至少你列表展示字段 + `product_url` + `image_600_url` + `image_original_url`）

> 推荐：详情优先返回 600 图（加载快），同时给 original 作为“查看原图”的入口。

---

### 1.3 Presentation Layer（React Web，移动端优先）

你要的 MVP 就两页：

* 列表页：iPhone 默认两列卡片 + 分页
* 详情页：大图 + 字段 + 外链（product url）

同时保证后续“原生 App 简单”：

* API 统一，未来可用 React Native（Expo）直接复用 API client 与类型（可选）。

---

## 2) MVP 页面设计细节

### 2.1 列表页（iPhone 两列 + 分页）

**路由**：`/`

**布局规则（响应式）**

* iPhone（< 768px）：两列
* iPad/桌面：3–4 列（可选）

**每个卡片包含：**

* 缩略图（`image_thumb_url`，300）
* `brand_name`（第一行，粗体）
* `model_name`（第二行）
* `model_no`（第三行，等宽/小字）
* 价格（`currency + price`，在卡片底部或右下角）

**交互：**

* 点击卡片 → 跳转详情页 `/items/:id`

**分页（移动端推荐样式）**

* 简洁的 **Prev / Next** + 当前页提示
* 或“加载更多”也属于分页的一种（更符合移动端），但你已明确需要分页，建议先做 Prev/Next。

**错误与占位**

* 图片加载失败显示占位图（或灰底）
* 列表加载中 skeleton
* 空结果提示（当前 MVP 可先不做筛选，至少要处理空）

---

### 2.2 详情页（大图 + 外链）

**路由**：`/items/:id`

**展示：**

* 顶部：返回按钮 + 标题（品牌 + 型号）
* 主图：优先 600 图（`image_600_url`），可点击“查看原图”（打开 `image_original_url`）
* 信息区（两列字段展示即可）：

  * brand_name / model_name / model_no
  * price（含 currency）
  * status（active/sold）
  * first_seen_dt / last_seen_dt（可选）
* 外链：

  * `product_url`（“Open product page”）
  * 新窗口打开

---

## 3) 项目骨架级目录结构（Monorepo，与你现有 crawler/storage 兼容）

你现有：

* `crawler/`（抓取解析）
* `storage/`（存储相关）

建议扩展成：

```text
project-root/
  crawler/                      # 已有：抓取、解析、写入 crawler_log/crawler_item
  storage/                      # 已有：DB/MinIO 操作封装、迁移、工具脚本

  services/
    api/                        # Service Layer: FastAPI
      app/
        main.py                 # FastAPI 启动入口
        settings.py             # env 配置（DATABASE_URL、S3/MinIO、IMAGE_URL_MODE 等）
        db/
          session.py            # DB session/连接池
          models.py             # ORM models（crawler_item 映射）
          queries.py            # 列表/详情 SQL（分页、排序）
        routers/
          items.py              # /items 与 /items/{id}
        schemas/
          items.py              # Pydantic response schemas
        services/
          images.py             # key -> url（presign 或 cdn）
          pricing.py            # price 格式化（可选）
      tests/                    # API tests（可后续）
      Dockerfile

    web/                        # Presentation Layer: React + Vite
      src/
        api/
          http.ts               # fetch/axios 封装、baseURL
          items.ts              # getItems/getItemById
          types.ts              # ItemListItem/ItemDetail 类型
        pages/
          ItemsListPage.tsx
          ItemDetailPage.tsx
        components/
          ItemCard.tsx
          PaginationBar.tsx
          PriceTag.tsx
          ImageBox.tsx
          LoadingSkeleton.tsx
        routes/
          router.tsx            # react-router 配置
        styles/
          global.css
          tokens.css
      index.html
      vite.config.ts
      package.json
      Dockerfile                # 可选（本地开发不一定要）

  infra/
    docker-compose.yml          # 本地一键启动（postgres/minio/api）
    env/
      .env.local.example        # 本地示例配置
      .env.cloud.example        # 云上示例配置（S3/CDN/RDS）
    init/
      postgres-init.sql         # 可选：初始化/扩展（pg_trgm 等）

  docs/
    plan.md                     # 你要的规划文档（可后续补充）
    api.md                      # 接口说明（可选）

  README.md
```

> 你可以保持 `crawler/` 继续写数据库；`api/` 只读查询 + 生成图片 URL。这样边界最清晰，迭代也最稳。

---

## 4) 前端页面组件拆分（MVP 级）

### ItemsListPage

* 状态：

  * `page, pageSize, total, items, loading, error`
* 组件：

  * `ItemGrid`（可直接用 CSS Grid）
  * `ItemCard`（单卡片）
  * `PaginationBar`（Prev/Next）
* 行为：

  * `GET /items?page=&page_size=`
  * 点击卡片跳转详情

**移动端两列实现方式（建议）**

* 用 CSS Grid：

  * `grid-template-columns: repeat(2, minmax(0, 1fr));`
  * 在桌面用媒体查询改成 3/4 列

### ItemDetailPage

* 状态：

  * `item, loading, error`
* 组件：

  * `ImageBox`（主图 + “查看原图”）
  * `KeyValueList`（字段列表，可简单 div）
  * `ExternalLinkButton`（打开 product_url）

---

## 5) 本地部署与云迁移（保持“无缝切换”）

### 本地（macOS）建议

* `docker-compose` 起：

  * Postgres
  * MinIO
  * API
* Web 用本机 `npm run dev`（开发体验最好）

### 上云迁移（几乎只改 env）

* `DATABASE_URL`：本地 → RDS/托管 PG
* `S3_ENDPOINT`：MinIO → S3（或云上 MinIO）
* `IMAGE_URL_MODE`：presign → cdn（可选）
* `CDN_BASE_URL`：新增即可

数据库无需改结构（仍存 key）。

---

## 6) MVP 所需的最小字段确认（避免返工）

为满足你“详情页外链”，建议你在 `crawler_item` 增加：

* `product_url TEXT NULL`

并在抓取写入时填充。后端详情接口直接返回该字段即可。

---

如果你认可这个骨架，我下一步可以直接输出两份更“可执行”的设计材料（仍不写业务代码也能落地）：

1. **API 的请求/响应 JSON Schema（按你表字段映射）**，包含 `image_thumb_url/image_600_url/image_original_url` 生成规则
2. **React 页面信息架构与状态流（数据加载、分页交互、移动端两列 CSS 规则）**，让你按图施工即可
