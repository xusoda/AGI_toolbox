# GoodsHunter 项目架构文档

## 项目概述

GoodsHunter 是一个商品信息抓取、处理和展示系统，主要用于从多个电商网站抓取商品信息，进行数据清洗和去重，并记录价格变化历史，最终通过 Web 界面展示给用户。

## 整体架构

系统采用分层架构，包含以下主要层次：

1. **数据采集层**：Crawler 模块负责网页抓取和数据提取
2. **数据存储层**：Storage 模块提供数据库和对象存储服务
3. **数据处理层**：Item Extract 模块负责数据同步和变更检测
4. **服务层**：API 服务提供 RESTful 接口
5. **展示层**：Web 前端提供用户界面

## 前情提要
   整个项目的启动命令位于：`GoodsHunter/manual_operation_bash/start_all.sh` 如果对启动项做出了调整，需要修改/变更的话，请在启动命令做出相应的调整。
   以及关键的docker compose文件位于：`GoodsHunter/docker-compose.yml`


## 目录结构

```
GoodsHunter/
├── crawler/              # 网页抓取和内容解析模块
├── storage/              # 存储系统（数据库和对象存储）
├── item_extract/         # 商品数据提取和同步模块
├── search/               # 搜索模块
│   ├── engine.py        # 搜索引擎抽象接口
│   ├── postgres_engine.py  # PostgreSQL 搜索引擎实现
│   ├── es_engine.py     # Elasticsearch 搜索引擎实现（预留）
│   ├── data_manager.py  # 搜索数据管理器
│   └── service.py       # 搜索服务层
├── services/             # 服务层
│   ├── api/             # FastAPI 后端服务
│   └── web/             # React 前端应用
├── enums/                # 全局枚举值定义
│   ├── business/        # 业务相关枚举（category, status, change_type 等）
│   ├── display/         # 展示层相关枚举（sort, lang 等）
│   └── trade/           # 交易相关枚举（currency 等）
├── manual_operation_bash/  # 手动操作脚本
├── docs/                 # 项目文档
└── docker-compose.yml    # Docker 编排配置
```

---

## 1. Crawler 模块

**路径**: `crawler/`

### 1.1 模块概述

基于 Playwright 的网页抓取和结构化内容抽取工具，支持批量 URL 处理、基于 Profile 的灵活配置、多种抽取策略（JSON-LD、XPath、正则表达式）和策略链回退机制。

### 1.2 目录结构

```
crawler/
├── app/                  # 应用入口
│   ├── run.py           # CLI 入口（批量URL处理）
│   └── run_with_db.py   # 带数据库写入的入口
├── core/                 # 核心模块
│   ├── types.py         # 核心类型定义（Record, Profile, Page等）
│   └── registry.py      # Profile 注册表
├── fetch/                # 抓取模块
│   └── playwright_fetcher.py  # Playwright 抓取器
├── extract/              # 抽取模块
│   ├── engine.py        # 抽取引擎
│   ├── parse_tool.py    # 解析工具
│   ├── transforms.py    # 数据转换函数
│   └── strategies/      # 抽取策略
│       ├── jsonld.py    # JSON-LD 策略
│       ├── xpath.py     # XPath 策略
│       └── regex.py     # 正则表达式策略
├── profiles/             # Profile 配置
│   ├── profiles.yaml    # Profile 配置文件
│   ├── commit_watch.yaml
│   └── watchnian.yaml
├── test/                 # 测试模块
│   ├── test_completeness.py  # 字段完整性测试
│   └── test_config.yaml
├── config.yaml           # 全局配置
├── requirements.txt      # Python 依赖
└── README.md            # 模块文档
```

### 1.3 核心功能

1. **网页抓取**：使用 Playwright 进行动态网页抓取，支持等待条件、超时配置、视口设置等
2. **内容抽取**：支持多种抽取策略，按优先级回退
3. **数据转换**：提供丰富的数据转换函数（URL拼接、字符串处理、正则提取等）
4. **Profile 配置**：基于 YAML 的灵活配置系统，支持不同站点的抽取规则
5. **批量处理**：支持从文件读取 URL 列表进行批量处理
6. **输出格式**：支持 JSONL 格式输出，同时保存图片和文本文件

### 1.4 对外 API

#### 1.4.1 CLI 接口

**入口**: `python -m app.run`

**参数**:
- `--urls`: URL 文件路径或单个 URL（必需）
- `--out`: 输出 JSONL 文件路径（可选）
- `--profiles`: Profile 配置文件路径或目录（默认: `profiles`）

**示例**:
```bash
# 从文件读取URL列表
python -m app.run --urls urls.txt --out results.jsonl

# 处理单个URL
python -m app.run --urls "https://example.com" --out results.jsonl

# 指定自定义Profile配置
python -m app.run --urls urls.txt --out results.jsonl --profiles custom_profiles.yaml
```

#### 1.4.2 核心类型

**Record** (`core/types.py`):
- `url`: 处理的 URL
- `data`: 成功抽取的字段数据（字典）
- `errors`: 字段级别的错误信息列表
- `status_code`: HTTP 状态码

**Profile** (`core/types.py`):
- `name`: Profile 名称
- `match`: URL 匹配配置（域名或正则表达式）
- `fetch`: 抓取配置（等待条件、超时等）
- `parse`: 解析配置（字段抽取策略链）
- `site`: 站点名称
- `category`: 商品类别

#### 1.4.3 输出格式

JSONL 格式，每行一个 JSON 对象：
```json
{
  "url": "https://example.com",
  "data": {
    "title": "示例标题",
    "price": "99.99",
    "items": [...]
  },
  "errors": []
}
```

### 1.5 依赖关系

- 依赖 `storage/output/fileWriter.py` 进行文件输出
- 依赖 `storage/output/db_writer.py` 进行数据库写入（如果使用 `run_with_db.py`）

---

## 2. Storage 模块

**路径**: `storage/`

### 2.1 模块概述

提供数据库和对象存储相关的配置、初始化脚本和客户端工具。包括 PostgreSQL 数据库管理和 MinIO 对象存储管理。

### 2.2 目录结构

```
storage/
├── db/                   # 数据库相关
│   ├── init.sql         # Postgres 数据库初始化脚本
│   └── reset_db.sh      # 数据库重置脚本
├── output/               # 输出模块
│   ├── writer.py        # 基础写入接口
│   ├── fileWriter.py    # 文件写入器（JSONL、图片、文本）
│   └── db_writer.py     # 数据库写入器
├── file_storage/         # 本地文件存储
│   ├── image/           # 图片文件（按站点分类）
│   └── text/            # 文本文件（按站点分类）
├── minio_client.py       # MinIO 客户端封装
├── test/                 # 测试模块
└── README.md            # 模块文档
```

### 2.3 核心功能

1. **数据库管理**：
   - 提供 PostgreSQL 数据库初始化脚本
   - 定义 `crawler_log`、`crawler_item`、`item_change_history`、`pipeline_state` 等表结构
   - 支持分区表（按月分区）

2. **对象存储管理**：
   - MinIO 客户端封装
   - 图片上传和缩略图生成
   - 支持 Presign URL 和 CDN URL 两种模式

3. **数据写入**：
   - `FileWriter`: 文件写入器，支持 JSONL、图片、文本文件保存
   - `DBWriter`: 数据库写入器，支持批量写入、连接池管理、图片上传

### 2.4 对外 API

#### 2.4.1 DBWriter 类

**路径**: `storage/output/db_writer.py`

**初始化**:
```python
from storage.output.db_writer import DBWriter

db_writer = DBWriter(
    database_url=None,  # 从环境变量 DATABASE_URL 读取
    pool_size=5,
    max_overflow=10,
    enable_image_upload=True
)
```

**主要方法**:
- `write_record(record, site)`: 写入单条记录到 `crawler_log` 表
- `write_records(records, site)`: 批量写入记录
- `__enter__` / `__exit__`: 支持上下文管理器

**使用示例**:
```python
from storage.output.db_writer import DBWriter
from crawler.core.types import Record

# 方式1: 直接使用
db_writer = DBWriter()
db_writer.write_record(record, site="commit-watch.co.jp")

# 方式2: 使用上下文管理器
with DBWriter() as db_writer:
    db_writer.write_record(record, site="commit-watch.co.jp")
```

#### 2.4.2 FileWriter 类

**路径**: `storage/output/fileWriter.py`

**主要方法**:
- `save_record(record, site, output_path)`: 保存记录到文件（JSONL、图片、文本）

#### 2.4.3 MinIOClient 类

**路径**: `storage/minio_client.py`

**主要方法**:
- `upload_image(image_data, key)`: 上传图片
- `generate_thumbnails(image_data, key)`: 生成缩略图
- `get_presign_url(key, expires_seconds)`: 获取 Presign URL
- `get_cdn_url(key)`: 获取 CDN URL

### 2.5 数据库表结构

#### 2.5.1 crawler_log 表

存储原始抓取记录：
- `id`: 自增主键
- `category`: 商品类别
- `site`: 站点域名
- `item_id`: 商品ID
- `raw_json`: 原始JSON数据（JSONB）
- `brand_name`, `model_name`, `model_no`: 商品信息
- `currency`: 货币单位（默认JPY）
- `price`: 价格（整数）
- `image_original_key`, `image_thumb_300_key`, `image_thumb_600_key`: MinIO 图片key
- `image_sha256`: 图片SHA256哈希值
- `source_uid`: 源唯一标识
- `raw_hash`: 原始数据哈希
- `status`: 状态（success/error）
- `crawl_time`: 抓取时间
- `dt`: 日期（分区键）

#### 2.5.2 crawler_item 表

存储去重后的商品信息：
- `id`: 自增主键
- `source_uid`: 源唯一标识（唯一约束）
- `site`, `category`, `item_id`: 商品标识
- `brand_name`, `model_name`, `model_no`: 商品信息
- `currency`, `price`: 价格信息
- `image_*_key`: 图片key
- `product_url`: 商品链接
- `status`: 状态（active/sold/removed）
- `first_seen_dt`, `last_seen_dt`: 首次/最后发现时间
- `sold_dt`, `sold_reason`: 售出信息
- `last_crawl_time`: 最后抓取时间

#### 2.5.3 item_change_history 表

存储商品变更历史（按月分区）：
- `id`: 自增主键
- `item_id`: 商品ID（外键）
- `event_key`: 事件唯一标识（唯一约束，保证幂等性）
- `change_type`: 变更类型（price_change/status_change）
- `old_value`, `new_value`: 变更前后值
- `change_dt`: 变更时间
- `created_at`: 创建时间

#### 2.5.4 pipeline_state 表

存储处理流水线状态：
- `pipeline_name`: 流水线名称（主键）
- `last_log_id`: 最后处理的日志ID（游标）
- `updated_at`: 更新时间

### 2.6 依赖关系

- 依赖 PostgreSQL 数据库
- 依赖 MinIO 对象存储服务
- 被 `crawler` 模块使用（通过 `DBWriter` 和 `FileWriter`）
- 被 `item_extract` 模块使用（读取 `crawler_log`，写入 `crawler_item` 和 `item_change_history`）
- 被 `services/api` 模块使用（读取商品数据，生成图片URL）

---

## 3. Item Extract 模块

**路径**: `item_extract/`

### 3.1 模块概述

从 `crawler_log` 表中提取商品数据，同步到 `crawler_item` 表，并记录变更历史到 `item_change_history` 表。支持增量同步、价格变化检测、幂等性保证和并发安全。

### 3.2 目录结构

```
item_extract/
├── main.py                    # 入口脚本
├── sync_processor.py          # 主处理流程
├── log_reader.py              # Crawler Log 读取
├── item_upserter.py           # Item 表 Upsert
├── history_writer.py           # 变更历史写入
├── state_manager.py           # 游标状态管理
├── change_detector.py          # 变化检测逻辑
├── price_normalizer.py        # 价格规范化
├── source_uid_generator.py    # Source UID 生成
├── event_key_generator.py     # Event Key 生成（幂等）
├── models.py                  # 表结构定义
├── utils.py                   # 工具函数（数据库连接等）
├── exceptions.py              # 自定义异常
└── README.md                  # 模块文档
```

### 3.3 核心功能

1. **增量同步**：从 `crawler_log` 增量同步到 `crawler_item` 表
2. **价格变化检测**：自动检测价格变化并记录到 `item_change_history`
3. **游标机制**：使用 `pipeline_state` 表记录处理进度，支持崩溃恢复
4. **幂等性保证**：通过 `event_key` 唯一约束保证历史记录不重复
5. **并发安全**：使用 `SELECT ... FOR UPDATE` 防止并发问题
6. **批量处理**：支持批量读取和处理，提高效率

### 3.4 对外 API

#### 3.4.1 CLI 接口

**入口**: `python -m item_extract.main`

**参数**:
- `--database-url`: 数据库连接URL（默认从环境变量 `DATABASE_URL` 读取）
- `--batch-size`: 批量处理大小（默认: 100）
- `--max-records`: 最大处理记录数（默认: 不限制）
- `--once`: 只运行一次（默认: 持续运行）
- `--interval`: 持续运行模式的轮询间隔（秒，默认: 60）
- `--init-db`: 初始化数据库表（如果不存在）

**使用示例**:
```bash
# 初始化数据库表
python -m item_extract.main --init-db

# 运行一次同步
python -m item_extract.main --once

# 持续运行模式（默认每60秒轮询一次）
python -m item_extract.main

# 自定义轮询间隔
python -m item_extract.main --interval 30
```

#### 3.4.2 核心函数

**run_sync** (`sync_processor.py`):
```python
def run_sync(
    conn,
    batch_size: int = 100,
    max_records: Optional[int] = None
) -> Dict[str, Any]:
    """
    执行同步处理
    
    Returns:
        {
            'total_processed': int,
            'total_success': int,
            'total_failed': int,
            'total_price_changed': int,
            'total_history_written': int,
            'last_log_id_before': int,
            'last_log_id_after': int,
            'errors': List[str]
        }
    """
```

### 3.5 处理流程

1. **读取游标**：从 `pipeline_state` 表获取 `last_log_id`
2. **读取日志**：从 `crawler_log` 表读取 `id > last_log_id` 且 `status='success'` 的记录
3. **处理每条记录**：
   - 规范化价格（`price_normalizer.py`）
   - 生成 `source_uid`（`source_uid_generator.py`）
   - Upsert 到 `crawler_item` 表（获取旧价格）
   - 检测价格变化（`change_detector.py`）
   - 如果价格变化，更新 item 价格字段并写入 `item_change_history`
4. **更新游标**：处理成功后更新 `last_log_id`

### 3.6 设计原则

1. **幂等性**：通过 `event_key` 唯一约束保证历史记录不重复
2. **并发安全**：使用 `SELECT ... FOR UPDATE` 防止并发问题
3. **崩溃恢复**：游标机制支持从上次中断处继续处理
4. **批量处理**：支持批量读取和处理，提高效率

### 3.7 依赖关系

- 依赖 `storage` 模块的数据库表结构
- 读取 `crawler_log` 表
- 写入 `crawler_item` 和 `item_change_history` 表
- 使用 `pipeline_state` 表管理状态

---

## 4. Search 模块

**路径**: `search/`

### 4.1 模块概述

搜索模块提供商品搜索功能，支持全文搜索、过滤、排序和分页。采用抽象设计，可以无缝切换不同的搜索引擎实现（PostgreSQL、Elasticsearch 等）。

### 4.2 目录结构

```
search/
├── __init__.py          # 模块初始化
├── engine.py            # 搜索引擎抽象接口
├── postgres_engine.py   # PostgreSQL 搜索引擎实现
├── es_engine.py         # Elasticsearch 搜索引擎实现（预留）
├── data_manager.py      # 搜索数据管理器
├── service.py          # 搜索服务层
└── README.md           # 模块文档
```

### 4.3 核心功能

1. **全文搜索**：支持在品牌名、型号名、型号编号中搜索，支持中文、英文、日文
2. **搜索过滤**：支持按状态、站点、类别、品牌、价格范围等过滤
3. **排序功能**：支持按价格、最后发现时间、创建时间排序
4. **分页功能**：支持分页查询
5. **搜索建议（SUG）**：根据用户输入的前缀提供自动补全建议

### 4.4 对外 API

#### 4.4.1 SearchEngine 抽象接口

**路径**: `search/engine.py`

**核心方法**:
- `search(query, filters, sort, page, page_size)`: 执行搜索
- `suggest(query, size)`: 获取搜索建议
- `index_document(document)`: 索引文档
- `delete_document(document_id)`: 删除文档
- `bulk_index_documents(documents)`: 批量索引文档

#### 4.4.2 PostgresSearchEngine 类

**路径**: `search/postgres_engine.py`

**功能**:
- 使用 PostgreSQL 的全文搜索功能（tsvector/tsquery）
- 支持中文、英文、日文搜索
- 使用 `plainto_tsquery` 和 `to_tsvector` 实现全文搜索

**初始化**:
```python
from search.postgres_engine import PostgresSearchEngine

search_engine = PostgresSearchEngine(
    database_url="postgresql://...",
    session=db_session  # 可选
)
```

#### 4.4.3 SearchService 类

**路径**: `search/service.py`

**功能**:
- 封装搜索业务逻辑
- 提供统一的搜索接口
- 集成搜索建议功能

**使用示例**:
```python
from search.service import SearchService
from search.engine import SearchFilters, SortOption

search_service = SearchService(search_engine)

# 搜索
filters = SearchFilters(status="active", min_price=1000)
sort = SortOption(field="price", order="asc")
result = search_service.search_products(
    query="Rolex",
    filters=filters,
    sort=sort,
    page=1,
    page_size=20
)

# 获取建议
suggestions = search_service.suggest_products(query="Role", size=5)
```

### 4.5 设计原则

1. **抽象设计**：通过 `SearchEngine` 抽象接口，将底层搜索引擎与其他模块解耦
2. **无缝迁移**：可以轻松切换搜索引擎（从 PostgreSQL 到 Elasticsearch），API 层和前端无需修改
3. **多语言支持**：支持中文、英文、日文搜索
4. **性能优化**：使用数据库索引优化搜索性能

### 4.6 依赖关系

- 依赖 `storage` 模块的数据库表（`crawler_item`）
- 被 `services/api` 模块使用（通过搜索路由）
- 未来可扩展支持 Elasticsearch 等其他搜索引擎

### 4.7 迁移到 Elasticsearch

当需要迁移到 Elasticsearch 时：

1. 实现 `ElasticsearchSearchEngine` 类（继承 `SearchEngine`）
2. 在 API 路由中替换搜索引擎实例
3. API 层和前端无需修改，因为接口保持一致

---

## 5. Services 模块

**路径**: `services/`

### 4.1 API 服务

**路径**: `services/api/`

#### 5.1.1 模块概述

FastAPI 后端服务，提供商品浏览和搜索 RESTful API。支持分页、排序、图片 URL 生成、全文搜索等功能。

#### 5.1.2 目录结构

```
services/api/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── settings.py          # 配置管理
│   ├── db/                  # 数据库相关
│   │   ├── models.py        # SQLAlchemy ORM 模型
│   │   ├── queries.py       # 查询函数
│   │   └── session.py       # 数据库会话管理
│   ├── routers/             # 路由
│   │   ├── items.py         # 商品路由
│   │   └── search.py        # 搜索路由
│   ├── schemas/             # Pydantic Schema
│   │   ├── items.py         # 商品 Schema
│   │   └── search.py        # 搜索 Schema
│   └── services/            # 业务服务
│       └── images.py        # 图片 URL 生成服务
├── Dockerfile               # Docker 镜像构建文件
├── requirements.txt         # Python 依赖
├── run.sh                   # 启动脚本
└── README.md               # 模块文档
```

#### 5.1.3 核心功能

1. **商品列表查询**：支持分页、排序、状态筛选
2. **商品详情查询**：根据 ID 获取商品详细信息
3. **商品搜索**：支持全文搜索、过滤、排序、分页
4. **搜索建议（SUG）**：提供搜索自动补全建议
5. **图片 URL 生成**：支持 Presign URL 和 CDN URL 两种模式
6. **CORS 支持**：配置跨域资源共享

#### 5.1.4 对外 API

**基础路径**: `/api`

**端点**:

1. **GET `/api/items`** - 获取商品列表
   - **查询参数**:
     - `page`: 页码（默认: 1）
     - `page_size`: 每页数量（默认: 20，最大: 100）
     - `status`: 商品状态（默认: `active`，可选: `active`/`sold`/`removed`）
     - `sort`: 排序方式（默认: `last_seen_desc`，可选: `last_seen_desc`/`price_asc`/`price_desc`）
   - **响应**:
     ```json
     {
       "total": 100,
       "page": 1,
       "page_size": 20,
       "items": [
         {
           "id": 1,
           "brand_name": "Rolex",
           "model_name": "Submariner",
           "model_no": "116610LN",
           "currency": "JPY",
           "price": 1000000,
           "image_thumb_url": "https://...",
           "last_seen_dt": "2024-01-01",
           "status": "active"
         }
       ]
     }
     ```

2. **GET `/api/search`** - 搜索商品
   - **查询参数**:
     - `q`: 搜索关键词（必需，支持中英日文）
     - `page`: 页码（默认: 1）
     - `page_size`: 每页数量（默认: 20，最大: 100）
     - `sort_field`: 排序字段（默认: `last_seen_dt`，可选: `price`/`last_seen_dt`/`created_at`）
     - `sort_order`: 排序方向（默认: `desc`，可选: `asc`/`desc`）
     - `status`: 商品状态（可选: `active`/`sold`/`removed`）
     - `site`: 站点域名（可选）
     - `category`: 商品类别（可选）
     - `brand_name`: 品牌名称（可选）
     - `min_price`: 最低价格（可选）
     - `max_price`: 最高价格（可选）
     - `currency`: 货币单位（可选）
     - `lang`: 语言代码（默认: `en`，可选: `en`/`zh`/`ja`）
   - **响应**:
     ```json
     {
       "total": 100,
       "page": 1,
       "page_size": 20,
       "items": [...]
     }
     ```

3. **GET `/api/search/suggest`** - 获取搜索建议
   - **查询参数**:
     - `q`: 搜索关键词前缀（必需）
     - `size`: 返回建议数量（默认: 5，最大: 20）
   - **响应**:
     ```json
     {
       "suggestions": ["Rolex", "Rolex Submariner", ...]
     }
     ```

4. **GET `/api/items/{item_id}`** - 获取商品详情
   - **路径参数**:
     - `item_id`: 商品 ID（整数）
   - **响应**:
     ```json
     {
       "id": 1,
       "source_uid": "commit-watch.co.jp-12345",
       "site": "commit-watch.co.jp",
       "category": "watch",
       "item_id": "12345",
       "brand_name": "Rolex",
       "model_name": "Submariner",
       "model_no": "116610LN",
       "currency": "JPY",
       "price": 1000000,
       "image_thumb_url": "https://...",
       "image_600_url": "https://...",
       "image_original_url": "https://...",
       "product_url": "https://...",
       "status": "active",
       "first_seen_dt": "2024-01-01",
       "last_seen_dt": "2024-01-15",
       "sold_dt": null,
       "sold_reason": null,
       "last_crawl_time": "2024-01-15T10:00:00Z",
       "created_at": "2024-01-01T00:00:00Z",
       "updated_at": "2024-01-15T10:00:00Z"
     }
     ```

5. **GET `/`** - 健康检查
   - **响应**: `{"message": "GoodsHunter API", "status": "ok"}`

6. **GET `/health`** - 健康检查
   - **响应**: `{"status": "healthy"}`

#### 5.1.5 环境变量

```bash
# 数据库
DATABASE_URL=postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=watch-images
MINIO_USE_SSL=false

# 图片 URL 策略
IMAGE_URL_MODE=presign  # presign 或 cdn
CDN_BASE_URL=  # CDN 模式时使用
PRESIGN_EXPIRES_SECONDS=1800  # Presign URL 过期时间（秒）
```

#### 5.1.6 依赖关系

- 依赖 `storage` 模块的数据库表（`crawler_item`）
- 依赖 `storage/minio_client.py` 生成图片 URL
- 依赖 `search` 模块提供搜索功能
- 被 `services/web` 模块调用

---

### 5.2 Web 前端

**路径**: `services/web/`

#### 5.2.1 模块概述

React + TypeScript + Vite 前端应用，移动端优先设计。提供商品列表和详情页面。

#### 5.2.2 目录结构

```
services/web/
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── api/                  # API 客户端
│   │   ├── http.ts           # HTTP 封装
│   │   ├── items.ts          # 商品 API
│   │   └── types.ts          # 类型定义
│   ├── pages/                # 页面组件
│   │   ├── ItemsListPage.tsx # 商品列表页
│   │   └── ItemDetailPage.tsx # 商品详情页
│   ├── components/           # 通用组件
│   │   ├── ItemCard.tsx      # 商品卡片
│   │   ├── PaginationBar.tsx # 分页组件
│   │   └── LoadingSkeleton.tsx # 加载骨架屏
│   ├── hooks/                # 自定义 Hooks
│   │   ├── useURLState.ts    # URL 状态管理 Hook
│   │   └── useDebounce.ts    # 防抖 Hook
│   ├── types/                # 类型定义
│   │   └── urlState.ts       # URL 状态类型
│   └── styles/               # 样式
│       └── global.css        # 全局样式
├── docs/                     # 文档
│   └── URL_STATE_MANAGEMENT_IMPLEMENTATION.md  # URL 状态管理实现文档
├── index.html                # HTML 模板
├── package.json              # Node.js 依赖
├── vite.config.ts            # Vite 配置
├── tsconfig.json             # TypeScript 配置
├── run.sh                    # 启动脚本
└── README.md                 # 模块文档
```

#### 5.2.3 核心功能

1. **商品列表页**：
   - 两列网格布局（移动端）
   - 支持分页
   - 支持排序（最后发现时间、价格）
   - 响应式设计（移动端 2 列，平板 3 列，桌面 4 列）

2. **商品详情页**：
   - 大图展示
   - 字段信息展示
   - 外链跳转

3. **用户体验**：
   - 加载骨架屏
   - 错误处理
   - 移动端优化

4. **URL 状态管理**：
   - 基于 React Router 的 `useSearchParams` 实现
   - 将搜索、筛选、分页、排序等 UI 状态同步到 URL
   - 支持深层链接（Deep Linking），可通过 URL 直接访问特定状态
   - 支持浏览器前进/后退功能
   - 搜索关键词使用防抖处理，避免频繁更新 URL
   - 详细实现文档：`services/web/docs/URL_STATE_MANAGEMENT_IMPLEMENTATION.md`

#### 5.2.4 对外接口

**API 调用** (`src/api/items.ts`):
- `getItems(params)`: 获取商品列表
- `getItemById(id)`: 获取商品详情

**路由**:
- `/`: 商品列表页
- `/items/:id`: 商品详情页

#### 5.2.5 环境变量

```bash
VITE_API_BASE_URL=/api  # 默认使用 Vite 代理配置
```

#### 5.2.6 依赖关系

- 依赖 `services/api` 模块提供的 RESTful API
- 通过 Vite 代理将 `/api` 请求代理到后端服务

---

## 6. Manual Operation Bash 模块

**路径**: `manual_operation_bash/`

### 5.1 模块概述

提供手动操作的 Bash 脚本，用于快速启动各个模块。

### 6.2 目录结构

```
manual_operation_bash/
├── run_crawl.sh          # 运行抓取任务
└── run_item_extract.sh   # 运行商品提取任务
```

### 6.3 功能

- `run_crawl.sh`: 执行网页抓取任务
- `run_item_extract.sh`: 执行商品数据提取和同步任务

---

## 7. 数据流

### 7.1 完整数据流

```
1. 网页抓取 (Crawler)
   ↓
   [crawler_log 表] (原始抓取记录)
   ↓
2. 数据提取和同步 (Item Extract)
   ↓
   [crawler_item 表] (去重后的商品)
   [item_change_history 表] (变更历史)
   ↓
3. API 服务 (Services/API)
   ↓
4. Web 前端 (Services/Web)
   ↓
   用户界面
```

### 7.2 图片存储流

```
1. Crawler 抓取图片
   ↓
2. DBWriter 上传到 MinIO
   ↓
   [MinIO 对象存储]
   ↓
3. API 服务生成 Presign URL 或 CDN URL
   ↓
4. Web 前端展示图片
```

---

## 8. 基础设施

### 8.1 Docker Compose 服务

**文件**: `docker-compose.yml`

**服务**:
1. **postgres**: PostgreSQL 15 数据库
   - 端口: 5432
   - 用户名: `goodshunter`
   - 密码: `goodshunter123`
   - 数据库: `goodshunter`

2. **minio**: MinIO 对象存储
   - API 端口: 9000
   - Console 端口: 9001
   - 用户名: `minioadmin`
   - 密码: `minioadmin123`

3. **api**: FastAPI 后端服务
   - 端口: 8000
   - 依赖: postgres, minio

### 8.2 启动方式

```bash
# 启动所有服务
docker compose up -d

# 启动特定服务
docker compose up -d postgres minio

# 查看日志
docker compose logs -f api

# 停止服务
docker compose down
```

---

## 9. 模块间依赖关系图

```
┌─────────────┐
│   Crawler   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Storage   │◄─────────┐
│  (DB/MinIO) │         │
└──────┬──────┘         │
       │                 │
       ↓                 │
┌─────────────┐         │
│Item Extract │─────────┘
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Services   │
│    /api     │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Services   │
│    /web     │
└─────────────┘
```

---

## 10. 技术栈

### 10.1 后端
- **Python 3.11+**
- **FastAPI**: Web 框架
- **SQLAlchemy**: ORM
- **Playwright**: 网页抓取
- **PostgreSQL**: 关系型数据库
- **MinIO**: 对象存储

### 10.2 前端
- **React**: UI 框架
- **TypeScript**: 类型系统
- **Vite**: 构建工具

### 10.3 基础设施
- **Docker & Docker Compose**: 容器化部署
- **PostgreSQL**: 数据库
- **MinIO**: 对象存储

---

## 11. 扩展性

### 11.1 添加新站点
1. 在 `crawler/profiles/` 目录下创建新的 Profile 配置文件
2. 配置 URL 匹配规则和字段抽取策略
3. 运行抓取任务

### 11.2 添加新字段
1. 更新 `crawler/profiles/` 中的 Profile 配置
2. 更新数据库表结构（如需要）
3. 更新 API Schema 和前端类型定义

### 11.3 添加新的变化检测
1. 在 `item_extract/change_detector.py` 中添加新的检测逻辑
2. 在 `item_extract/history_writer.py` 中添加新的写入方法
3. 更新 `item_change_history` 表的 `change_type` 枚举

---

## 12. 测试

### 12.1 Crawler 测试
- **位置**: `crawler/test/`
- **测试类型**: 字段完整性测试
- **运行**: `pytest test/test_completeness.py`

### 12.2 Storage 测试
- **位置**: `storage/test/`
- **测试内容**: 数据库写入、MinIO 上传等

---

## 13. 部署

### 13.1 开发环境
1. 启动基础设施：`docker compose up -d postgres minio`
2. 启动 API 服务：`cd services/api && ./run.sh`
3. 启动前端服务：`cd services/web && ./run.sh`

### 13.2 生产环境
1. 使用 Docker Compose 部署所有服务
2. 配置环境变量（数据库密码、MinIO 密钥等）
3. 配置 CDN（如使用 CDN 模式）
4. 配置反向代理（Nginx）

---

## 14. 注意事项

1. **数据库初始化**：首次启动时，Postgres 会自动执行 `init.sql` 创建表结构
2. **MinIO 配置**：生产环境请修改默认密码和配置
3. **图片存储**：支持本地文件存储和 MinIO 对象存储两种模式
4. **幂等性**：Item Extract 模块通过 `event_key` 保证历史记录不重复
5. **并发安全**：使用数据库锁机制防止并发问题
6. **游标恢复**：如果处理失败，游标不更新，下次可以继续处理

---

## 15. 枚举值定义

系统使用全局枚举值来统一管理常量，确保类型安全和代码一致性。枚举值定义在 `enums/` 目录下，按类别组织。

### 15.1 枚举分类

枚举值按业务领域分类：

- **business/**: 业务相关枚举
  - `Category`: 商品类别（watch/bag/jewelry/clothing/camera）
  - `ItemStatus`: 商品状态（active/sold/removed）
  - `ChangeType`: 变更类型（price/status）
  - `CrawlerLogStatus`: 抓取日志状态（success/failed）

- **display/**: 展示层相关枚举
  - `SortOption`: 列表页排序选项（first_seen_desc/price_asc/price_desc）
  - `SortField`: 搜索页排序字段（price/last_seen_dt/created_at）
  - `SortOrder`: 排序顺序（asc/desc）
  - `LanguageCode`: 语言代码（en/zh/ja）

- **trade/**: 交易相关枚举
  - `CurrencyCode`: 货币代码（JPY/USD/CNY）

### 15.2 使用方式

**Python 后端**:
```python
from enums.business.category import Category
from enums.business.status import ItemStatus

# 使用枚举值
category = Category.WATCH.value  # "watch"
if Category.is_valid(category):
    # 处理类别
    pass

# 获取默认值
default_category = Category.get_default()  # "watch"
```

**TypeScript 前端**:
```typescript
import { Category } from '@enums/business/category'
import { ItemStatus } from '@enums/business/status'

// 使用枚举值
const category: Category = Category.WATCH
const status: ItemStatus = ItemStatus.ACTIVE

// 验证枚举值
if (isValidCategory(value)) {
  // 处理类别
}
```

注意：前端项目配置了路径别名 `@enums`，指向全局的 `enums/` 目录。这需要：
- 在 `tsconfig.json` 中配置 `paths` 别名
- 在 `vite.config.ts` 中配置 `resolve.alias`

### 15.3 详细文档

更多关于枚举值的定义、使用场景和代码位置，请参考：`enums/README.md`

---

## 16. 文档索引

- **Crawler 模块**: `crawler/README.md`
- **Storage 模块**: `storage/README.md`
- **Item Extract 模块**: `item_extract/README.md`
- **Search 模块**: `search/README.md`
- **API 服务**: `services/api/README.md`
- **Web 前端**: `services/web/README.md`
- **前端架构**: `README_FRONTEND.md`
- **枚举值定义**: `enums/README.md`

