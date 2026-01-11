# 搜索模块

搜索模块提供了商品搜索功能，支持全文搜索、过滤、排序和分页。使用 Elasticsearch 作为搜索引擎，支持多语言搜索。

## 架构设计

### 模块结构

```
search/
├── __init__.py          # 模块初始化
├── engine.py            # 搜索引擎抽象接口
├── es_engine.py         # Elasticsearch 搜索引擎实现
├── data_manager.py      # 搜索数据管理器
├── service.py          # 搜索服务层
├── i18n/               # 国际化支持
│   ├── index_builder.py   # 索引构建器（多语言别名）
│   └── alias_resolver.py  # 别名解析器
├── sync/               # 同步模块
│   ├── index_syncer.py    # 索引同步器
│   └── alias_updater.py   # 别名更新器
├── scripts/            # 工具脚本
│   ├── create_index.py    # 创建ES索引
│   ├── sync_all_data.py   # 全量同步数据
│   ├── update_aliases.py  # 更新别名（词典更新后）
│   └── inspect_index.py   # 检查索引
└── README.md           # 本文档
```

### 核心组件

1. **SearchEngine (抽象接口)**
   - 定义了搜索引擎的统一接口
   - 支持搜索、建议、索引、删除等操作

2. **ElasticsearchSearchEngine (Elasticsearch 实现)**
   - 使用 Elasticsearch 作为搜索引擎
   - 支持中文、英文、日文搜索
   - 支持多语言别名匹配（通过 IndexBuilder 构建）

3. **IndexBuilder (索引构建器)**
   - 负责构建包含多语言同义词的ES文档
   - 集成品牌和型号的别名解析

4. **SearchDataManager (数据管理器)**
   - 负责将商品数据同步到搜索引擎
   - 支持单个和批量同步
   - 提供增量更新和删除功能

5. **SearchService (服务层)**
   - 封装搜索业务逻辑
   - 提供统一的搜索接口
   - 集成搜索建议（SUG）功能

6. **IndexSyncer (索引同步器)**
   - 负责从数据库同步商品数据到ES
   - 支持全量同步和增量同步

7. **AliasUpdater (别名更新器)**
   - 负责在词典更新后更新ES索引
   - 支持增量更新（仅更新受影响的商品）和全量重建

## 功能特性

### 搜索功能

- **全文搜索**：支持在品牌名、型号名、型号编号中搜索
- **多语言支持**：支持中文、英文、日文搜索
- **多语言别名匹配**：通过别名数组实现跨语言匹配（如"Rolex"和"ロレックス"）
- **过滤功能**：支持按状态、站点、类别、品牌、价格范围等过滤
- **排序功能**：支持按价格、最后发现时间、创建时间排序
- **分页功能**：支持分页查询

### 搜索建议（SUG）

- **自动补全**：根据用户输入的前缀提供搜索建议
- **多字段匹配**：从品牌名、型号名、型号编号、别名中匹配建议
- **实时响应**：快速返回建议列表

## 使用方法

### 在 API 中使用

搜索功能已集成到 API 服务中，提供以下端点：

- `GET /api/search` - 搜索商品
- `GET /api/search/suggest` - 获取搜索建议

### 直接使用搜索服务

```python
from search.es_engine import ElasticsearchSearchEngine
from search.service import SearchService
from search.engine import SearchFilters, SortOption

# 初始化搜索引擎
search_engine = ElasticsearchSearchEngine(
    es_host="localhost",
    es_port=9200,
    index_name="products",
    category="watch"
)

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

## 索引同步

### 全量同步

全量同步所有商品数据到ES索引：

```bash
python -m search.scripts.sync_all_data
```

### 增量同步

在商品更新后，可以手动触发增量同步（通过手动操作脚本）：

```bash
# 见 manual_operation_bash/update_search_index_after_items.sh
```

### 词典更新后更新索引

在更新词典（`i18n/dictionaries/`）后，需要更新ES索引以反映新的别名：

```bash
# 增量更新（仅更新受影响的商品）
python -m search.scripts.update_aliases --brands Rolex --models '{"Rolex": ["Submariner"]}'

# 全量重建（更新所有商品）
python -m search.scripts.update_aliases --rebuild-all
```

或使用手动操作脚本：

```bash
# 见 manual_operation_bash/update_search_index_after_dictionary.sh
```

## 环境配置

### 环境变量

```bash
ES_HOST=localhost          # Elasticsearch 主机
ES_PORT=9200              # Elasticsearch 端口
ES_INDEX_NAME=products    # ES索引名称
DATABASE_URL=postgresql://...  # 数据库连接URL（用于同步）
```

### 依赖包

搜索模块需要以下依赖：

- `elasticsearch>=8.0.0,<9.0.0` - Elasticsearch 客户端
- `sqlalchemy` - 数据库ORM（用于数据同步）
- `psycopg2-binary` - PostgreSQL 驱动（用于数据同步）

## 索引管理

### 创建索引

创建ES索引（如果不存在会自动创建）：

```bash
python -m search.scripts.create_index
```

### 检查索引

检查索引中的商品数据：

```bash
python -m search.scripts.inspect_index --product-id 123
```

## 注意事项

1. **数据同步**：商品数据需要从数据库同步到ES索引。可以使用 `sync_all_data.py` 进行全量同步，或使用手动操作脚本进行增量同步。

2. **词典更新**：更新词典后，需要运行 `update_aliases.py` 或手动操作脚本来更新ES索引中的别名信息。

3. **性能优化**：ES索引使用标准分析器。如需更好的中文分词，可以安装IK插件。

4. **索引刷新**：ES索引默认不立即刷新，如果需要立即搜索到新数据，需要手动刷新索引。

## 未来改进

- [ ] 支持IK中文分词插件
- [ ] 添加搜索历史记录
- [ ] 支持搜索高亮
- [ ] 添加搜索统计和分析
- [ ] 自动增量同步（监听数据库变化）
