# 搜索模块

搜索模块提供了商品搜索功能，支持全文搜索、过滤、排序和分页。采用抽象设计，可以无缝切换不同的搜索引擎实现。

## 架构设计

### 模块结构

```
search/
├── __init__.py          # 模块初始化
├── engine.py            # 搜索引擎抽象接口
├── postgres_engine.py   # PostgreSQL 搜索引擎实现
├── es_engine.py         # Elasticsearch 搜索引擎实现（预留）
├── data_manager.py      # 搜索数据管理器
├── service.py          # 搜索服务层
└── README.md           # 本文档
```

### 核心组件

1. **SearchEngine (抽象接口)**
   - 定义了搜索引擎的统一接口
   - 支持搜索、建议、索引、删除等操作
   - 便于切换不同的搜索引擎实现

2. **PostgresSearchEngine (PostgreSQL 实现)**
   - 使用 PostgreSQL 的全文搜索功能（tsvector/tsquery）
   - 支持中文、英文、日文搜索
   - 使用 `plainto_tsquery` 和 `to_tsvector` 实现全文搜索

3. **SearchDataManager (数据管理器)**
   - 负责将商品数据同步到搜索引擎
   - 支持单个和批量同步
   - 提供增量更新和删除功能

4. **SearchService (服务层)**
   - 封装搜索业务逻辑
   - 提供统一的搜索接口
   - 集成搜索建议（SUG）功能

## 功能特性

### 搜索功能

- **全文搜索**：支持在品牌名、型号名、型号编号中搜索
- **多语言支持**：支持中文、英文、日文搜索
- **过滤功能**：支持按状态、站点、类别、品牌、价格范围等过滤
- **排序功能**：支持按价格、最后发现时间、创建时间排序
- **分页功能**：支持分页查询

### 搜索建议（SUG）

- **自动补全**：根据用户输入的前缀提供搜索建议
- **多字段匹配**：从品牌名、型号名、型号编号中匹配建议
- **实时响应**：快速返回建议列表

## 使用方法

### 在 API 中使用

搜索功能已集成到 API 服务中，提供以下端点：

- `GET /api/search` - 搜索商品
- `GET /api/search/suggest` - 获取搜索建议

### 直接使用搜索服务

```python
from search.postgres_engine import PostgresSearchEngine
from search.service import SearchService
from search.engine import SearchFilters, SortOption

# 初始化搜索引擎
search_engine = PostgresSearchEngine(database_url="postgresql://...")

# 创建搜索服务
search_service = SearchService(search_engine)

# 执行搜索
filters = SearchFilters(status="active", min_price=1000)
sort = SortOption(field="price", order="asc")
result = search_service.search_products(
    query="Rolex",
    filters=filters,
    sort=sort,
    page=1,
    page_size=20
)

# 获取搜索建议
suggestions = search_service.suggest_products(query="Role", size=5)
```

## 迁移到 Elasticsearch

当需要迁移到 Elasticsearch 时，只需：

1. 实现 `ElasticsearchSearchEngine` 类（继承 `SearchEngine`）
2. 在 API 路由中替换搜索引擎实例：

```python
# 从
search_engine = PostgresSearchEngine(database_url=settings.DATABASE_URL)

# 改为
search_engine = ElasticsearchSearchEngine(es_host="localhost", es_port=9200)
```

API 层和前端无需修改，因为接口保持一致。

## 数据库优化

为了优化搜索性能，在 `crawler_item` 表上创建了以下索引：

- `idx_crawler_item_brand_name_text` - 品牌名文本索引（text_pattern_ops）
- `idx_crawler_item_model_name_text` - 型号名文本索引（text_pattern_ops）
- `idx_crawler_item_model_no_text` - 型号编号文本索引（text_pattern_ops）
- `idx_crawler_item_search_suggest` - 搜索建议组合索引

## 注意事项

1. **中文搜索**：PostgreSQL 的全文搜索对中文支持有限，如果需要更好的中文搜索效果，建议：
   - 安装 `zhparser` 扩展
   - 或迁移到 Elasticsearch（对中文支持更好）

2. **性能优化**：如果搜索性能成为瓶颈，可以考虑：
   - 添加 `search_vector` 列并创建 GIN 索引
   - 迁移到 Elasticsearch

3. **数据同步**：当前实现中，商品数据已经在 `crawler_item` 表中，PostgreSQL 搜索引擎直接查询该表。如果迁移到 Elasticsearch，需要实现数据同步机制。

## 未来改进

- [ ] 实现 Elasticsearch 搜索引擎
- [ ] 添加搜索历史记录
- [ ] 支持搜索高亮
- [ ] 添加搜索统计和分析
- [ ] 优化中文搜索（安装 zhparser 扩展或迁移到 ES）
