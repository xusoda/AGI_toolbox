# 搜索功能设置指南

本文档说明如何设置和初始化搜索功能。

## 前置要求

### 1. Python 依赖

搜索功能使用的依赖已经包含在 `services/api/requirements.txt` 中，主要包括：

- `sqlalchemy` - ORM 框架
- `psycopg2-binary` - PostgreSQL 驱动
- `fastapi` - Web 框架

无需额外安装依赖包。

### 2. 数据库

确保 PostgreSQL 数据库已启动并可以连接。

## 设置步骤

### 方法一：使用自动化脚本（推荐）

```bash
# 进入项目根目录
cd /Users/xushuda/WorkSpace/GoodsHunter

# 运行完整设置脚本
./search/scripts/setup_search.sh
```

脚本会自动：
1. 初始化数据库索引
2. 重启 API 服务

### 方法二：手动设置

#### 步骤 1: 初始化数据库索引

```bash
# 进入项目根目录
cd /Users/xushuda/WorkSpace/GoodsHunter

# 运行数据库索引初始化脚本
./search/scripts/init_search_indexes.sh
```

或者手动执行 SQL：

```bash
# 使用 psql 执行
psql -h localhost -p 5432 -U goodshunter -d goodshunter -f search/scripts/init_search_indexes.sql
```

#### 步骤 2: 更新服务

**如果使用 Docker Compose：**

```bash
# 重启 API 服务
docker compose restart api

# 或者重新构建并启动
docker compose up -d --build api
```

**如果使用本地运行：**

```bash
# 进入 API 目录
cd services/api

# 重启服务
./run.sh
```

## 验证设置

### 1. 检查 API 服务

访问健康检查端点：

```bash
curl http://localhost:8000/health
```

应该返回：`{"status":"healthy"}`

### 2. 测试搜索功能

**测试搜索：**

```bash
curl "http://localhost:8000/api/search?q=Rolex&page=1&page_size=20"
```

**测试搜索建议：**

```bash
curl "http://localhost:8000/api/search/suggest?q=Role&size=5"
```

### 3. 检查数据库索引

```sql
-- 连接到数据库
psql -h localhost -p 5432 -U goodshunter -d goodshunter

-- 检查索引是否创建
\di idx_crawler_item_*_text
\di idx_crawler_item_search_suggest
```

## 故障排查

### 问题 1: `NameError: name 'SearchService' is not defined`

**原因：** 搜索模块导入失败

**解决方法：**
1. 确保 `search/` 目录在项目根目录下
2. 检查 Python 路径配置
3. 重启 API 服务

### 问题 2: 搜索功能不可用

**原因：** 搜索模块未正确导入

**解决方法：**
1. 检查 API 日志，查看具体错误信息
2. 确保 `search/` 目录存在且包含所有必要文件
3. 检查数据库连接是否正常

### 问题 3: 数据库索引创建失败

**原因：** 数据库连接问题或权限不足

**解决方法：**
1. 检查数据库连接配置
2. 确保数据库用户有创建索引的权限
3. 手动执行 SQL 脚本查看具体错误

### 问题 4: 搜索性能慢

**原因：** 数据库索引未创建或数据量大

**解决方法：**
1. 确认索引已创建：`\di idx_crawler_item_*_text`
2. 分析查询计划：`EXPLAIN ANALYZE SELECT ...`
3. 考虑添加更多索引或迁移到 Elasticsearch

## 数据库索引说明

搜索功能创建了以下索引：

1. **idx_crawler_item_brand_name_text** - 品牌名文本索引（text_pattern_ops）
   - 优化品牌名搜索和搜索建议

2. **idx_crawler_item_model_name_text** - 型号名文本索引（text_pattern_ops）
   - 优化型号名搜索和搜索建议

3. **idx_crawler_item_model_no_text** - 型号编号文本索引（text_pattern_ops）
   - 优化型号编号搜索和搜索建议

4. **idx_crawler_item_search_suggest** - 搜索建议组合索引
   - 优化搜索建议查询性能

## API 端点说明

### 搜索商品

```
GET /api/search
```

**查询参数：**
- `q` (必需) - 搜索关键词（支持中英日文）
- `page` (可选) - 页码，默认 1
- `page_size` (可选) - 每页数量，默认 20，最大 100
- `sort_field` (可选) - 排序字段：`price`/`last_seen_dt`/`created_at`，默认 `last_seen_dt`
- `sort_order` (可选) - 排序方向：`asc`/`desc`，默认 `desc`
- `status` (可选) - 商品状态：`active`/`sold`/`removed`
- `site` (可选) - 站点域名
- `category` (可选) - 商品类别
- `brand_name` (可选) - 品牌名称
- `min_price` (可选) - 最低价格
- `max_price` (可选) - 最高价格
- `currency` (可选) - 货币单位
- `lang` (可选) - 语言代码：`en`/`zh`/`ja`，默认 `en`

**示例：**
```bash
curl "http://localhost:8000/api/search?q=Rolex&page=1&page_size=20&sort_field=price&sort_order=asc"
```

### 搜索建议

```
GET /api/search/suggest
```

**查询参数：**
- `q` (必需) - 搜索关键词前缀
- `size` (可选) - 返回建议数量，默认 5，最大 20

**示例：**
```bash
curl "http://localhost:8000/api/search/suggest?q=Role&size=5"
```

## 后续优化

如果搜索性能成为瓶颈，可以考虑：

1. **添加 search_vector 列**：在 `crawler_item` 表中添加 `search_vector tsvector` 列，并创建 GIN 索引
2. **安装中文分词扩展**：安装 PostgreSQL 的 `zhparser` 扩展以改善中文搜索
3. **迁移到 Elasticsearch**：实现 `ElasticsearchSearchEngine` 并切换搜索引擎

## 相关文档

- [搜索模块 README](../search/README.md)
- [架构文档](../../docs/architecture/architecture.md)
- [搜索引擎方案文档](../../docs/关于搜索引擎的方案.md)
