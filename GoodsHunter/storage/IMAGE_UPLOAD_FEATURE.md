# 图片上传功能说明

## 功能概述

已按照**方案1**在 `DBWriter` 中集成了图片上传功能。现在当使用 `DBWriter.write_record()` 写入数据时，会自动：

1. **下载图片**（如果item中有图片URL但没有图片数据）
2. **计算SHA256哈希值**（用于去重）
3. **生成缩略图**（300px和600px，WebP格式）
4. **上传到MinIO**（原图+缩略图）
5. **更新数据库**（保存图片key和SHA256）

## 工作流程

```
Crawler → Extract → Record
                    ↓
            DBWriter.write_record()
                    ↓
        处理图片（如果存在）
         ├─ 下载图片（如果需要）
         ├─ 计算SHA256
         ├─ 生成缩略图（300px, 600px）
         ├─ 上传MinIO（原图+缩略图）
         └─ 更新数据库字段
                    ↓
        写入数据库（包含图片key）✅
```

## 使用方法

### 基本使用

```python
from output.db_writer import DBWriter
from core.types import Record

# 初始化DBWriter（默认启用图片上传）
db_writer = DBWriter()

# 写入记录（会自动处理图片）
db_writer.write_record(record, site="commit-watch.co.jp")
```

### 禁用图片上传

如果不想上传图片（只写入数据库），可以禁用：

```python
db_writer = DBWriter(enable_image_upload=False)
```

## 图片数据来源

DBWriter 会按以下优先级获取图片：

1. **`_image_data`**：item中的图片二进制数据（最高优先级）
2. **`image` 或 `_image_url`**：图片URL，会自动下载

## 依赖要求

确保已安装以下依赖：

```bash
pip install psycopg2-binary minio Pillow requests
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

## 环境变量

确保设置了以下环境变量：

```bash
# 数据库
DATABASE_URL=postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=watch-images
```

## 数据库字段

写入数据库时，以下字段会被填充：

- `image_original_key`: MinIO原图key，格式：`original/{sha256[0:2]}/{sha256}.{ext}`
- `image_thumb_300_key`: 300px缩略图key，格式：`thumb/300/{sha256[0:2]}/{sha256}.webp`
- `image_thumb_600_key`: 600px缩略图key，格式：`thumb/600/{sha256[0:2]}/{sha256}.webp`
- `image_sha256`: 图片SHA256哈希值（用于去重）

如果图片处理失败，这些字段会是 `NULL`。

## 特性

### 1. 自动去重

- 通过SHA256哈希值实现内容级去重
- 如果MinIO中已存在相同SHA256的图片，会跳过上传，直接返回已有key

### 2. 缩略图生成

- 自动生成300px和600px两种尺寸的缩略图
- 使用WebP格式，质量85%
- 保持原始宽高比

### 3. 错误处理

- 图片下载失败：继续写入数据库，图片字段为NULL
- 缩略图生成失败：原图仍会上传，缩略图字段为NULL
- MinIO上传失败：记录错误日志，继续处理

### 4. 性能优化

- 如果item中没有图片数据或URL，跳过图片处理
- 已存在的图片不会重复上传
- 图片二进制数据不会写入JSON（避免数据库过大）

## 测试

运行测试脚本检查功能：

```bash
# 检查MinIO状态
python crawler/test/check_minio.py

# 测试数据库写入（包含图片上传）
python crawler/test/test_db_writer.py
```

## 注意事项

1. **图片大小限制**：默认最大10MB，超过会跳过下载
2. **网络超时**：图片下载超时时间为30秒
3. **格式支持**：支持JPEG、PNG、GIF、WebP、BMP等常见格式
4. **RGBA处理**：RGBA图片会自动转换为RGB（添加白色背景）

## 故障排查

### 图片没有上传

1. 检查MinIO服务是否运行：`docker compose ps`
2. 检查环境变量是否正确设置
3. 查看日志中的错误信息
4. 确认item中是否有图片数据或URL

### 缩略图生成失败

1. 确认已安装Pillow：`pip install Pillow`
2. 检查图片格式是否支持
3. 查看错误日志

### 数据库字段为NULL

- 可能是图片处理失败，检查日志
- 可能是item中没有图片数据
- 可能是MinIO连接失败

## 后续优化

当前实现是**方案1（快速方案）**，后续可以考虑：

1. **方案2（推荐）**：实现独立的Image Worker，异步处理图片
2. **批量处理**：批量上传图片以提高性能
3. **重试机制**：失败时自动重试
4. **进度跟踪**：记录图片处理进度

