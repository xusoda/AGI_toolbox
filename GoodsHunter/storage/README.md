# Storage 存储系统

本目录包含数据库和对象存储相关的配置和初始化脚本。

## 目录结构

```
storage/
├── db/
│   └── init.sql          # Postgres数据库初始化脚本
└── README.md             # 本文件
```

## 快速开始

### 1. 启动 Postgres 和 MinIO 服务

在项目根目录运行：

```bash
docker-compose up -d
```

这将启动：
- **Postgres**: 端口 5432
  - 用户名: `goodshunter`
  - 密码: `goodshunter123`
  - 数据库: `goodshunter`
- **MinIO**: 
  - API 端口: 9000
  - Console 端口: 9001
  - 用户名: `minioadmin`
  - 密码: `minioadmin123`

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
DATABASE_URL=postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=watch-images
```

### 3. 使用 DBWriter 写入数据

在 crawler 代码中使用 `DBWriter`：

```python
from output.db_writer import DBWriter
from core.types import Record

# 初始化DBWriter（会自动从环境变量读取DATABASE_URL）
db_writer = DBWriter()

# 写入记录
db_writer.write_record(record, site="commit-watch.co.jp")

# 或使用上下文管理器
with DBWriter() as db_writer:
    db_writer.write_record(record, site="commit-watch.co.jp")
```

## 数据库表结构

### crawler_log 表

存储原始抓取记录，包含以下字段：

- `id`: 自增主键
- `category`: 商品类别
- `site`: 站点域名
- `item_id`: 商品ID
- `raw_json`: 原始JSON数据
- `brand_name`: 品牌名称
- `model_name`: 型号名称
- `model_no`: 型号编号
- `currency`: 货币单位（默认JPY）
- `price`: 价格（整数）
- `image_original_key`: MinIO原图key
- `image_thumb_300_key`: MinIO 300px缩略图key
- `image_thumb_600_key`: MinIO 600px缩略图key
- `image_sha256`: 图片SHA256哈希值
- `crawl_time`: 抓取时间
- `dt`: 日期（分区键）

## MinIO 存储

MinIO 用于存储图片文件。访问 Console 界面：

http://localhost:9001

使用 `minioadmin` / `minioadmin123` 登录。

## 注意事项

1. 首次启动时，Postgres 会自动执行 `init.sql` 创建表结构
2. 如果需要重置数据库，可以删除 Docker volume：`docker-compose down -v`
3. 生产环境请修改默认密码和配置

