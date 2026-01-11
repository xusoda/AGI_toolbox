# 搜索架构迁移实现总结

## 实现完成情况

### ✅ 阶段1：环境准备

1. **docker-compose.yml**
   - ✅ 添加 Elasticsearch 服务（8.11.0版本）
   - ✅ 配置环境变量（ES_HOST, ES_PORT, ES_INDEX_NAME）
   - ✅ 添加健康检查
   - ✅ 添加数据卷（es_data）
   - ✅ API服务添加ES依赖

2. **requirements.txt**
   - ✅ 添加 elasticsearch>=8.11.0

3. **settings.py**
   - ✅ 添加ES配置项（ES_HOST, ES_PORT, ES_INDEX_NAME）

### ✅ 阶段2：实现核心模块

1. **search/i18n/alias_resolver.py** ✅
   - 基于词表解析品牌/型号别名
   - `get_brand_aliases()`: 获取品牌别名列表
   - `get_model_aliases()`: 获取型号别名列表

2. **search/i18n/index_builder.py** ✅
   - 构建包含多语言同义词的ES文档
   - `build_document()`: 构建ES索引文档（包含别名数组）

3. **search/es_engine.py** ✅
   - 完整实现 ElasticsearchSearchEngine 类
   - 实现 SearchEngine 接口的所有方法
   - 支持多语言搜索（通过 multi_match 在别名字段中搜索）
   - 支持索引创建、搜索、建议、索引文档、删除文档、批量索引

4. **search/sync/index_syncer.py** ✅
   - 索引同步器
   - `sync_all()`: 全量同步
   - `sync_items()`: 同步指定商品
   - `sync_incremental()`: 增量同步

5. **search/sync/alias_updater.py** ✅
   - 别名更新器
   - `update_affected_items()`: 增量更新受影响的商品
   - `rebuild_all()`: 全量重建索引

### ✅ 阶段3：数据迁移脚本

1. **search/scripts/create_index.py** ✅
   - 创建ES索引脚本
   - 支持从环境变量读取配置

2. **search/scripts/sync_all_data.py** ✅
   - 全量同步数据到ES脚本
   - 支持批量大小配置

3. **search/scripts/update_aliases.py** ✅
   - 词表更新后更新索引脚本
   - 支持全量重建和增量更新
   - 支持指定更新的品牌/型号

### ✅ 阶段4：API层切换

1. **services/api/app/routers/search.py** ✅
   - 修改 `get_search_service()` 函数
   - 从 PostgresSearchEngine 切换到 ElasticsearchSearchEngine
   - 使用 settings 中的ES配置

### ✅ 阶段5：词表更新机制

1. **search/scripts/update_aliases.py** ✅
   - 已实现（见阶段3）

## 核心特性

### 1. 多语言搜索支持

- **索引时扩展**：在索引中存储多语言同义词数组（brand_aliases, model_aliases）
- **查询时匹配**：使用 multi_match 在多个字段中搜索，实现跨语言匹配
- **示例**：搜索"rolex"可以找到"劳力士"商品（因为索引中存储了["劳力士", "rolex", "ロレックス"]）

### 2. 词表更新机制

- **手动触发**：运行 `python search/scripts/update_aliases.py --rebuild-all` 全量重建
- **增量更新**：运行 `python search/scripts/update_aliases.py --brands Rolex --models '{"Rolex": ["Submariner"]}'` 增量更新
- **自动同步**：通过 IndexSyncer 和 AliasUpdater 实现

### 3. 数据同步

- **全量同步**：`python search/scripts/sync_all_data.py`
- **批量处理**：支持批量大小配置，提高性能
- **增量同步**：支持基于时间的增量同步

## 使用方法

### 1. 启动服务

```bash
# 启动所有服务（包括ES）
docker-compose up -d

# 等待ES启动完成
docker-compose logs -f elasticsearch
```

### 2. 创建索引

```bash
# 在容器内执行
docker-compose exec api python /app/../search/scripts/create_index.py

# 或本地执行（需要配置环境变量）
python search/scripts/create_index.py
```

### 3. 全量同步数据

```bash
# 在容器内执行
docker-compose exec api python /app/../search/scripts/sync_all_data.py

# 或本地执行
python search/scripts/sync_all_data.py --batch-size 100
```

### 4. 更新词表后重建索引

```bash
# 全量重建
python search/scripts/update_aliases.py --rebuild-all

# 增量更新（指定品牌）
python search/scripts/update_aliases.py --brands Rolex

# 增量更新（指定品牌和型号）
python search/scripts/update_aliases.py --brands Rolex --models '{"Rolex": ["Submariner", "Datejust"]}'
```

### 5. 测试搜索

```bash
# 测试API搜索
curl "http://localhost:8000/api/search?q=rolex"

# 应该能搜索到"劳力士"的商品（如果索引中有的话）
```

## 架构说明

### ES索引结构

```json
{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "brand_name": {"type": "text", "analyzer": "standard"},
      "model_name": {"type": "text", "analyzer": "standard"},
      "model_no": {"type": "keyword"},
      "brand_aliases": {"type": "text", "analyzer": "standard"},  // 多语言别名数组
      "model_aliases": {"type": "text", "analyzer": "standard"},  // 多语言别名数组
      "search_text": {"type": "text", "analyzer": "standard"},    // 合并搜索文本
      "price": {"type": "integer"},
      "currency": {"type": "keyword"},
      "site": {"type": "keyword"},
      "category": {"type": "keyword"},
      "status": {"type": "keyword"},
      "last_seen_dt": {"type": "date"},
      "created_at": {"type": "date"},
      "image_thumb_300_key": {"type": "keyword"},
      "product_url": {"type": "keyword"}
    }
  }
}
```

### 文档示例

```json
{
  "id": 123,
  "brand_name": "Rolex",
  "model_name": "Submariner",
  "model_no": "116610LN",
  "brand_aliases": ["Rolex", "rolex", "劳力士", "ロレックス", "ROLEX"],
  "model_aliases": ["Submariner", "潜航者", "サブマリナー"],
  "search_text": "Rolex rolex 劳力士 ロレックス ROLEX Submariner 潜航者 サブマリナー 116610LN",
  "price": 1000000,
  "currency": "JPY",
  "site": "commit-watch.co.jp",
  "category": "watch",
  "status": "active",
  "last_seen_dt": "2024-01-15",
  "created_at": "2024-01-01T00:00:00Z",
  "image_thumb_300_key": "watchnian/gik-00-0702136.jpg",
  "product_url": "https://..."
}
```

### 搜索查询

使用 multi_match 在多个字段中搜索，实现跨语言匹配：

```json
{
  "multi_match": {
    "query": "rolex",
    "fields": [
      "brand_name^3",
      "brand_aliases^2.5",
      "model_name^2",
      "model_aliases^1.5",
      "search_text^1",
      "model_no^1"
    ],
    "type": "best_fields",
    "operator": "or",
    "fuzziness": "AUTO"
  }
}
```

## 下一步工作（可选）

1. **IK分词插件**：如果需要更好的中文分词效果，可以安装IK分词插件
2. **索引优化**：生产环境建议配置更多的分片和副本
3. **监控和告警**：添加ES集群监控和告警
4. **性能优化**：根据实际使用情况优化查询和索引配置
5. **自动化**：可以考虑添加词表文件变更监听，自动触发索引更新

## 注意事项

1. **ES 8.x API**：代码使用 `body` 参数，兼容 ES 8.x API
2. **索引刷新**：批量索引后需要调用 `refresh_index()` 使数据立即可搜索
3. **词表更新**：词表更新后需要运行更新脚本，索引才会生效
4. **数据同步**：当前是批量同步，如果需要实时同步，可以集成到 item_extract 模块
5. **回退方案**：PostgreSQL 搜索引擎保留，可以作为 fallback

## 测试建议

1. **功能测试**：
   - 测试多语言搜索（如搜索"rolex"可以找到"劳力士"商品）
   - 测试词表更新后的搜索能力
   - 测试搜索建议功能

2. **性能测试**：
   - 对比 PostgreSQL 和 ES 的搜索性能
   - 测试并发搜索性能
   - 测试大批量数据同步性能

3. **数据一致性测试**：
   - 验证 ES 索引与数据库数据的一致性
   - 测试增量同步的正确性
