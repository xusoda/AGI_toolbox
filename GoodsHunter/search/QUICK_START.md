# 搜索功能快速开始指南

## 问题修复

已修复 `NameError: name 'SearchService' is not defined` 错误。现在搜索模块的导入更加健壮。

## 快速设置（3 步）

### 1. 初始化数据库索引

```bash
cd /Users/xushuda/WorkSpace/GoodsHunter
./search/scripts/init_search_indexes.sh
```

或者使用 Docker Compose 环境：

```bash
# 如果使用环境变量
DB_HOST=localhost DB_PORT=5432 DB_NAME=goodshunter DB_USER=goodshunter DB_PASSWORD=goodshunter123 ./search/scripts/init_search_indexes.sh
```

### 2. 重启 API 服务

**Docker Compose 环境：**

```bash
docker compose restart api
```

**本地运行：**

```bash
cd services/api
./run.sh
```

### 3. 验证功能

```bash
# 测试搜索
curl "http://localhost:8000/api/search?q=Rolex&page=1&page_size=20"

# 测试搜索建议
curl "http://localhost:8000/api/search/suggest?q=Role&size=5"
```

## 一键设置脚本

```bash
cd /Users/xushuda/WorkSpace/GoodsHunter
./search/scripts/setup_search.sh
```

这个脚本会自动完成所有设置步骤。

## 依赖包

**无需安装额外依赖！** 搜索功能使用的所有依赖包已经包含在 `services/api/requirements.txt` 中：

- `sqlalchemy` - ORM 框架（已安装）
- `psycopg2-binary` - PostgreSQL 驱动（已安装）
- `fastapi` - Web 框架（已安装）

## 数据库索引

搜索功能会创建以下索引来优化性能：

1. `idx_crawler_item_brand_name_text` - 品牌名文本索引
2. `idx_crawler_item_model_name_text` - 型号名文本索引
3. `idx_crawler_item_model_no_text` - 型号编号文本索引
4. `idx_crawler_item_search_suggest` - 搜索建议组合索引

## API 端点

### 搜索商品

```
GET /api/search?q=<关键词>&page=1&page_size=20
```

### 搜索建议

```
GET /api/search/suggest?q=<关键词前缀>&size=5
```

## 故障排查

如果遇到问题，请查看 [SETUP.md](./SETUP.md) 中的详细故障排查指南。
