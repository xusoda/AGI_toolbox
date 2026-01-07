# 图片存储分析报告

## 当前状态检查

### 问题发现

经过代码检查，发现**图片目前没有存储到MinIO中**，存在以下问题：

#### 1. DBWriter 中的图片字段都是 None

在 `crawler/output/db_writer.py` 的第210-213行：

```python
None,  # image_original_key (后续由image_worker填充)
None,  # image_thumb_300_key
None,  # image_thumb_600_key
None,  # image_sha256
```

**说明**：数据库写入时，所有图片相关字段都被设置为 `None`，注释说明"后续由image_worker填充"。

#### 2. FileWriter 只保存到本地文件系统

在 `crawler/output/fileWriter.py` 中，`save_image` 方法只将图片保存到本地目录：
- 路径：`storage/file_storage/image/{site}/{item_id}.{ext}`
- **没有上传到MinIO**

#### 3. 缺少MinIO上传逻辑

目前代码中没有任何将图片上传到MinIO的逻辑。

## 数据流分析

### 当前流程

```
Crawler → Extract → Record
                    ↓
            FileWriter.save_record()
                    ↓
        保存到本地文件系统 ✅
        写入数据库（图片字段为None）✅
                    ↓
        图片未上传到MinIO ❌
```

### 预期流程（根据plan_v2_detail.md）

```
Crawler → Extract → Record
                    ↓
            DBWriter.write_record()
                    ↓
        写入数据库（图片字段为None）✅
                    ↓
        Image Worker（待实现）
                    ↓
        下载图片 → 计算SHA256 → 生成缩略图
                    ↓
        上传MinIO（原图+缩略图）
                    ↓
        更新数据库（图片key）❌
```

## 解决方案

### 方案1：在DBWriter中集成图片上传（快速方案）

修改 `DBWriter.write_record()` 方法，在写入数据库时同时上传图片：

**优点**：
- 实现简单，快速可用
- 不需要额外的Worker

**缺点**：
- 耦合了抓取和图片处理逻辑
- 可能阻塞抓取流程

### 方案2：实现独立的Image Worker（推荐方案）

按照计划文档，实现独立的Image Worker：

1. **从数据库读取需要处理图片的记录**
2. **下载图片**（从 `image_source_url` 或本地文件）
3. **计算SHA256**
4. **生成缩略图**（300px和600px）
5. **上传到MinIO**
6. **更新数据库**

**优点**：
- 符合架构设计（分离关注点）
- 可以异步处理，不阻塞抓取
- 可以重试失败的任务

**缺点**：
- 需要实现Worker和任务队列（Redis）

### 方案3：在FileWriter中同时上传MinIO（折中方案）

修改 `FileWriter.save_image()` 方法，保存到本地的同时上传到MinIO：

**优点**：
- 实现相对简单
- 保持现有流程

**缺点**：
- 仍然耦合了文件系统和对象存储
- 没有生成缩略图

## 已创建的工具

### 1. MinIOClient (`storage/minio_client.py`)

提供了完整的MinIO操作接口：
- `upload_image()`: 上传原图
- `upload_thumbnail()`: 上传缩略图
- `download_image()`: 下载图片
- `list_objects()`: 列出对象
- `object_exists()`: 检查对象是否存在
- `get_presigned_url()`: 生成预签名URL

### 2. 检查脚本 (`crawler/test/test_minio.py`)

用于检查MinIO状态：
- 测试MinIO连接
- 列出所有对象
- 检查数据库中的图片key是否在MinIO中存在

## 运行检查

运行检查脚本查看当前状态：

```bash
cd crawler
pip install minio  # 如果还没安装
python test/test_minio.py
```

## 下一步建议

1. **立即**：运行检查脚本确认当前状态
2. **短期**：实现方案3（在FileWriter中同时上传MinIO），快速解决问题
3. **长期**：实现方案2（Image Worker），符合架构设计

## 代码位置

- MinIO客户端：`storage/minio_client.py`
- 检查脚本：`crawler/test/test_minio.py`
- DBWriter：`crawler/output/db_writer.py`（需要修改）
- FileWriter：`crawler/output/fileWriter.py`（可选修改）

