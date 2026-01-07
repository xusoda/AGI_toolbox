# GoodsHunter API 服务

FastAPI 后端服务，提供商品浏览 API。

## 功能

- GET `/api/items` - 获取商品列表（分页、排序）
- GET `/api/items/{id}` - 获取商品详情

## 环境变量

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

## 安装和运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker 运行

```bash
docker build -t goodshunter-api .
docker run -p 8000:8000 goodshunter-api
```

