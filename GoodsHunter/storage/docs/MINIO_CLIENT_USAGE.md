# MinIO Client 使用说明

## 什么是 MinIO Client？

`MinIOClient` 是一个封装了 MinIO 操作的 Python 类，用于管理图片在 MinIO 对象存储中的上传、下载和查询。

### 主要功能

1. **上传图片**：将图片上传到 MinIO 存储
2. **生成缩略图**：上传不同尺寸的缩略图
3. **下载图片**：从 MinIO 下载图片
4. **查询对象**：列出和检查 MinIO 中的对象
5. **生成预签名URL**：生成临时访问链接

## 为什么需要 MinIO Client？

根据架构设计（`plan_v2_detail.md`），图片应该存储在 MinIO 中而不是本地文件系统：

- **原图**：存储在 MinIO 的 `original/` 路径下
- **缩略图**：存储在 MinIO 的 `thumb/300/` 和 `thumb/600/` 路径下
- **去重**：通过 SHA256 哈希值实现内容级去重
- **可扩展**：MinIO 兼容 S3，可以无缝切换到云存储

## 当前状态

⚠️ **图片目前没有存储到 MinIO**，原因：

1. `DBWriter` 在写入数据库时，图片字段都是 `None`
2. `FileWriter` 只保存到本地文件系统
3. 缺少图片上传到 MinIO 的逻辑

## 如何使用

### 1. 直接运行检查脚本（推荐）

这是一个独立的检查工具，**不需要使用 pytest**：

```bash
cd crawler
python test/check_minio.py
```

这个脚本会：
- 检查 MinIO 连接
- 列出所有图片对象
- 检查数据库中的图片 key 是否在 MinIO 中存在

### 2. 在代码中使用 MinIOClient

```python
from storage.minio_client import MinIOClient

# 初始化客户端（自动从环境变量读取配置）
client = MinIOClient()

# 上传图片
image_data = b"..."
sha256 = "abc123..."
ext = "jpg"
key = client.upload_image(image_data, sha256=sha256, ext=ext)

# 上传缩略图
thumbnail_data = b"..."
thumb_key = client.upload_thumbnail(thumbnail_data, sha256, size=300)

# 检查对象是否存在
exists = client.object_exists(key)

# 生成预签名URL（用于前端访问）
url = client.get_presigned_url(key, expires_seconds=3600)
```

## 环境变量配置

MinIOClient 从环境变量读取配置：

```bash
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=watch-images
MINIO_USE_SSL=false
```

## 下一步

### 方案1：在 DBWriter 中集成（快速）

修改 `DBWriter.write_record()`，在写入数据库时同时上传图片到 MinIO。

### 方案2：实现 Image Worker（推荐）

创建独立的 Worker 进程：
1. 从数据库读取需要处理图片的记录
2. 下载图片（从 URL 或本地文件）
3. 计算 SHA256
4. 生成缩略图
5. 上传到 MinIO
6. 更新数据库

### 方案3：在 FileWriter 中集成（折中）

修改 `FileWriter.save_image()`，保存到本地的同时上传到 MinIO。

## 文件位置

- **MinIO Client**: `storage/minio_client.py`
- **检查脚本**: `crawler/test/check_minio.py`（直接运行）
- **测试脚本**: `crawler/test/test_minio.py`（pytest 格式，但主要用于独立运行）

## 常见问题

### Q: 为什么运行 pytest 会报错 "fixture 'client' not found"？

A: `test_minio.py` 中的函数参数被 pytest 误认为是 fixture。这个脚本设计为独立运行，使用 `python test/check_minio.py` 而不是 `pytest`。

### Q: MinIO Client 需要手动执行吗？

A: 不需要。MinIO Client 是一个工具类，应该在代码中自动调用：
- 在 Image Worker 中自动上传图片
- 或者在 DBWriter/FileWriter 中集成上传逻辑

目前还没有实现自动上传，所以需要先实现相关逻辑。

### Q: 如何检查 MinIO 中是否有图片？

A: 运行检查脚本：
```bash
python crawler/test/check_minio.py
```

或者访问 MinIO Console：http://localhost:9001

