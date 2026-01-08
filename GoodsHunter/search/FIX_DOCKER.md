# Docker 环境搜索模块修复指南

## 问题描述

在 Docker 环境中，搜索模块无法导入，报错：`No module named 'search'`

## 原因

Docker Compose 配置中缺少 `search` 目录的挂载。

## 解决方案

### 1. 更新 docker-compose.yml

已在 `docker-compose.yml` 中添加搜索模块的挂载：

```yaml
volumes:
  - ./services/api:/app
  - ./storage:/app/../storage
  - ./i18n:/app/../i18n
  - ./search:/app/../search  # 新增
```

### 2. 重启 API 服务

```bash
cd /Users/xushuda/WorkSpace/GoodsHunter
docker compose restart api
```

或者重新构建并启动：

```bash
docker compose up -d --build api
```

### 3. 验证修复

查看 API 日志，应该看到：

```
INFO: 找到搜索模块路径: /app/../search
```

而不是：

```
WARNING: 搜索模块不可用: No module named 'search'
```

### 4. 测试搜索功能

```bash
# 测试搜索建议
curl "http://localhost:8000/api/search/suggest?q=Role&size=5"

# 测试搜索
curl "http://localhost:8000/api/search?q=Rolex&page=1&page_size=20"
```

## 路径说明

在 Docker 容器中，目录结构如下：

```
/app                    # services/api (挂载点)
/app/../search         # 项目根目录下的 search 模块
/app/../i18n           # 项目根目录下的 i18n 模块
/app/../storage        # 项目根目录下的 storage 模块
```

搜索路由会自动查找这些路径，并将项目根目录添加到 Python 路径中。

## 故障排查

如果仍然无法导入搜索模块：

1. **检查挂载是否正确**：
   ```bash
   docker compose exec api ls -la /app/../search
   ```
   应该能看到搜索模块的文件。

2. **检查 Python 路径**：
   查看 API 日志中的路径信息。

3. **手动验证**：
   ```bash
   docker compose exec api python -c "import sys; sys.path.insert(0, '/app/..'); from search.engine import SearchEngine; print('OK')"
   ```

## 相关文件

- `docker-compose.yml` - Docker Compose 配置
- `services/api/app/routers/search.py` - 搜索路由（包含路径查找逻辑）
