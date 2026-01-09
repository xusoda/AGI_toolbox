# 存储系统设置指南

本指南将帮助您设置 Postgres 数据库和 MinIO 对象存储系统。

## 步骤 1: 启动 Docker 服务

在项目根目录运行以下命令启动 Postgres 和 MinIO：

```bash
cd /Users/xushuda/WorkSpace/GoodsHunter
docker compose up -d
```

等待服务启动完成（约 10-30 秒），可以使用以下命令检查状态：

```bash
docker compose ps
```

## 步骤 2: 验证服务运行

### 检查 Postgres

```bash
# 检查容器日志
docker logs goodshunter-postgres

# 测试连接（需要安装 psql 客户端）
psql postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter -c "SELECT version();"

# 外部没有psql客户端，也可以直接用docker内置的psql链接：
docker exec -it goodshunter-postgres psql -U goodshunter -d goodshunter -c "SELECT version();"
```
### 检查 MinIO

1. 打开浏览器访问：http://localhost:9001
2. 使用以下凭据登录：
   - 用户名: `minioadmin`
   - 密码: `minioadmin123`
3. 创建 bucket：`watch-images`

## 步骤 3: 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter

# MinIO配置
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=watch-images
MINIO_USE_SSL=false
```

## 步骤 4: 安装 Python 依赖

```bash
cd crawler
pip install -r requirements.txt
```

## 步骤 5: 使用 DBWriter

### 在代码中使用

修改 `crawler/app/run.py` 或创建新的脚本：

```python
import os
from dotenv import load_dotenv
from storage.output.db_writer import DBWriter
from crawler.core.types import Record

# 加载环境变量
load_dotenv()

# 初始化DBWriter
db_writer = DBWriter()

# 写入记录（record 是从 crawler 获取的 Record 对象）
db_writer.write_record(record, site="commit-watch.co.jp")
```

### 集成到现有流程

在 `crawler/app/run.py` 的 `process_urls` 函数中，可以在保存文件后添加数据库写入：

```python
from storage.output.db_writer import DBWriter

# 在 process_urls 函数中
db_writer = DBWriter()

# 在保存记录后
stats = FileWriter.save_record(...)
db_writer.write_record(record, site=profile.site)
```

## 步骤 6: 验证数据写入

```bash
# 连接到数据库查看数据
psql postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter

# 在 psql 中执行
SELECT COUNT(*) FROM crawler_log;
SELECT site, item_id, brand_name, price FROM crawler_log LIMIT 10;
```

## 常见问题

### 1. Docker 服务无法启动

- 检查端口是否被占用：`lsof -i :5432` 和 `lsof -i :9000`
- 检查 Docker 是否运行：`docker ps`

### 2. 数据库连接失败

- 确认 Postgres 容器正在运行：`docker ps | grep postgres`
- 检查环境变量 `DATABASE_URL` 是否正确
- 查看容器日志：`docker logs goodshunter-postgres`

### 3. 表不存在

- 确认 `init.sql` 已正确挂载到容器
- 检查容器日志中是否有 SQL 执行错误
- 可以手动执行 SQL：`docker exec -i goodshunter-postgres psql -U goodshunter -d goodshunter < storage/db/init.sql`

### 4. psycopg2 安装失败

如果 `psycopg2-binary` 安装失败，可以尝试：

```bash
# macOS
brew install postgresql
pip install psycopg2-binary

# 或者使用 conda
conda install psycopg2
```

## 停止服务

```bash
# 停止服务（保留数据）
docker compose stop

# 停止并删除容器（保留数据卷）
docker compose down

# 停止并删除所有数据
docker compose down -v
```

## 下一步

- 配置 MinIO bucket 和访问策略
- 实现图片下载和缩略图生成 Worker
- 创建 API 服务查询数据库
- 构建 Web 前端界面

