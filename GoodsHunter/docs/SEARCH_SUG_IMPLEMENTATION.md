# 搜索建议（SUG）实现对比

## 问题2：目前SUG是如何实现的？

### PostgreSQL实现（已废弃）

之前PostgreSQL的SUG实现方式：

1. **索引**：使用 `text_pattern_ops` 操作符类创建索引，支持前缀匹配
   ```sql
   CREATE INDEX idx_crawler_item_brand_name_text 
       ON crawler_item(brand_name text_pattern_ops) 
       WHERE brand_name IS NOT NULL;
   
   CREATE INDEX idx_crawler_item_model_name_text 
       ON crawler_item(model_name text_pattern_ops) 
       WHERE model_name IS NOT NULL;
   
   CREATE INDEX idx_crawler_item_model_no_text 
       ON crawler_item(model_no text_pattern_ops) 
       WHERE model_no IS NOT NULL;
   
   CREATE INDEX idx_crawler_item_search_suggest 
       ON crawler_item(brand_name, model_name, model_no);
   ```

2. **查询方式**：使用 `ILIKE` 进行前缀匹配
   ```sql
   SELECT DISTINCT suggestion
   FROM (
       SELECT brand_name as suggestion FROM crawler_item 
       WHERE brand_name ILIKE :query_like AND brand_name IS NOT NULL
       UNION
       SELECT model_name as suggestion FROM crawler_item 
       WHERE model_name ILIKE :query_like AND model_name IS NOT NULL
       UNION
       SELECT model_no as suggestion FROM crawler_item 
       WHERE model_no ILIKE :query_like AND model_no IS NOT NULL
   ) as suggestions
   ORDER BY suggestion
   LIMIT :size
   ```

3. **特点**：
   - 使用 `text_pattern_ops` 索引优化 `ILIKE` 前缀查询性能
   - 大小写不敏感（使用 `ILIKE`）
   - 在品牌名、型号名、型号编号三个字段上搜索
   - 使用 `UNION` 合并结果并去重

### Elasticsearch实现（当前 - 使用Completion Suggester）

现在ES的SUG实现方式（基于ES的Completion Suggester）：

1. **索引字段**：在ES索引中包含以下字段
   - `brand_name` (text)
   - `model_name` (text)
   - `model_no` (keyword)
   - `brand_aliases` (text) - 品牌的多语言别名数组
   - `model_aliases` (text) - 型号的多语言别名数组
   - `suggest` (completion) - **新增的Completion字段，用于搜索建议**

2. **索引mapping**：`suggest`字段使用completion类型
   ```json
   {
     "suggest": {
       "type": "completion",
       "analyzer": "simple",
       "preserve_separators": true,
       "preserve_position_increments": true,
       "max_input_length": 50
     }
   }
   ```

3. **数据构建**：在IndexBuilder中构建completion字段数据
   ```python
   # 代码位置：search/i18n/index_builder.py
   # 构建completion字段的输入词（包含品牌名、型号名、型号编号和所有别名）
   suggest_inputs = []
   if brand_name:
       suggest_inputs.append(brand_name)
   if model_name:
       suggest_inputs.append(model_name)
   if model_no:
       suggest_inputs.append(model_no)
   # 添加品牌和型号的所有别名
   
   doc["suggest"] = {
       "input": suggest_inputs
   }
   ```

4. **查询方式**：使用ES的Completion Suggester API
   ```python
   # 代码位置：search/es_engine.py
   def suggest(self, query: str, size: int = 5) -> List[str]:
       query_clean = query.strip()
       
       es_query = {
           "suggest": {
               "product-suggest": {
                   "prefix": query_clean,
                   "completion": {
                       "field": "suggest",
                       "size": size,
                       "skip_duplicates": True
                   }
               }
           }
       }
       
       response = self.es_client.search(index=self.index_name, body=es_query)
       
       # 解析Completion Suggester的响应
       suggestions = []
       if "suggest" in response:
           options = response["suggest"]["product-suggest"][0].get("options", [])
           for option in options:
               suggestions.append(option.get("text", ""))
       
       return suggestions
   ```

5. **特点**：
   - 使用ES的**Completion Suggester**，这是ES专门用于自动补全的功能
   - **性能更优**：Completion Suggester使用FST（有限状态转换器）数据结构，查询速度更快
   - **自动去重**：使用`skip_duplicates`参数自动跳过重复项
   - 支持多语言别名匹配（通过将别名添加到completion字段的input中）
   - 支持前缀匹配和模糊匹配
   - **更适合搜索建议场景**：Completion Suggester专门为自动补全场景优化

### 对比总结

| 特性 | PostgreSQL实现 | Elasticsearch实现（旧） | Elasticsearch实现（当前） |
|------|---------------|----------------------|------------------------|
| **索引类型** | `text_pattern_ops` 索引 | ES倒排索引 | ES Completion字段（FST） |
| **查询方式** | `ILIKE` 前缀匹配 | `prefix` 查询 | Completion Suggester API |
| **搜索字段** | 3个：brand_name, model_name, model_no | 5个字段的prefix查询 | completion字段（包含所有字段值） |
| **多语言支持** | ❌ 不支持 | ✅ 支持（通过别名数组） | ✅ 支持（通过别名数组） |
| **去重方式** | SQL UNION | Python set | ES skip_duplicates参数 |
| **性能** | 依赖索引，中等 | 优秀 | **更优秀，专为自动补全优化** |
| **实现位置** | `search/postgres_engine.py`（已删除） | `search/es_engine.py`（旧版本） | `search/es_engine.py`（当前版本） |

### ES实现的主要优势

1. **多语言别名支持**：
   - 搜索"Rolex"时，可以匹配到别名数组中的"ロレックス"、"劳力士"等
   - PostgreSQL实现只能在单一字段上匹配

2. **更好的性能**（Completion Suggester）：
   - 使用FST（有限状态转换器）数据结构，查询速度更快
   - 专为自动补全场景优化，比prefix查询性能更好
   - 支持大量数据的快速前缀匹配

3. **更灵活的查询**：
   - 可以轻松扩展搜索字段
   - 支持更复杂的查询逻辑
   - 自动去重，无需手动处理

4. **ES原生支持**：
   - Completion Suggester是ES专门为自动补全设计的功能
   - 代码更简洁，逻辑更清晰
   - 更好的可维护性

## 相关代码位置

- **ES SUG实现**：`search/es_engine.py` 的 `suggest()` 方法
- **索引构建**：`search/i18n/index_builder.py` 的 `build_document()` 方法（构建completion字段）
- **索引mapping**：`search/es_engine.py` 的 `_create_index()` 方法（定义completion字段）
- **API端点**：`services/api/app/routers/search.py` 的 `/search/suggest` 路由
- **已删除的PostgreSQL实现**：`search/postgres_engine.py`（已删除）

## 启用新SUG功能

### 前提条件

- Elasticsearch服务正常运行
- 已更新代码（包含completion字段的mapping和IndexBuilder修改）
- 数据库中有商品数据

### 启用步骤

#### 方法1：使用一键重建脚本（最简单，推荐）

我们提供了一个一键重建脚本，可以自动完成删除旧索引、创建新索引和同步数据的全过程：

```bash
# 激活虚拟环境（如果需要）
source ../.venv/bin/activate

# 设置环境变量（如果需要）
export DATABASE_URL="postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter"
export ES_HOST="localhost"
export ES_PORT="9200"
export ES_INDEX_NAME="products"

# 运行一键重建脚本
cd GoodsHunter
python -m search.scripts.rebuild_index_with_sug

# 或使用--force参数跳过确认（适用于自动化脚本）
python -m search.scripts.rebuild_index_with_sug --force

# 或指定批量大小
python -m search.scripts.rebuild_index_with_sug --batch-size 200
```

这个脚本会：
1. 检查并删除现有索引（会提示确认，除非使用`--force`）
2. 创建包含completion字段的新索引
3. 全量同步所有商品数据
4. 刷新索引使数据立即可搜索

#### 方法2：手动重建索引（适用于需要更多控制的情况）

如果需要手动控制每个步骤：

1. **删除旧索引**（如果存在）：
   ```bash
   # 使用curl直接删除索引
   curl -X DELETE "http://localhost:9200/products"
   
   # 或者使用Python脚本（需要ES客户端）
   python -c "
   from elasticsearch import Elasticsearch
   es = Elasticsearch(['http://localhost:9200'])
   if es.indices.exists(index='products'):
       es.indices.delete(index='products')
       print('索引已删除')
   "
   ```

2. **创建新索引**（会自动包含completion字段）：
   ```bash
   # 激活虚拟环境（如果需要）
   source ../.venv/bin/activate
   
   # 运行创建索引脚本
   cd GoodsHunter
   python -m search.scripts.create_index
   ```
   
   这会自动创建包含`completion`类型`suggest`字段的新索引。

3. **全量同步数据**：
   ```bash
   # 设置环境变量（如果需要）
   export DATABASE_URL="postgresql://goodshunter:goodshunter123@localhost:5432/goodshunter"
   export ES_HOST="localhost"
   export ES_PORT="9200"
   export ES_INDEX_NAME="products"
   
   # 运行全量同步脚本
   python -m search.scripts.sync_all_data
   ```

4. **验证新SUG功能**：
   ```bash
   # 测试搜索建议API
   curl "http://localhost:8000/api/search/suggest?q=Role&size=5"
   ```

#### 方法2：保留现有索引（适用于生产环境，需要零停机）

**注意**：ES的mapping一旦创建后不能直接修改字段类型。如果现有索引中没有`completion`类型的`suggest`字段，需要：

1. **创建新索引**（使用不同的名称）：
   ```bash
   export ES_INDEX_NAME="products_new"
   python -m search.scripts.create_index
   ```

2. **同步数据到新索引**：
   ```bash
   export ES_INDEX_NAME="products_new"
   python -m search.scripts.sync_all_data
   ```

3. **使用别名切换**（需要实现别名管理逻辑）：
   - 创建别名指向新索引
   - 验证新索引功能正常
   - 切换到新索引

**注意**：如果现有索引已经存在且没有completion字段，建议使用方法1重建索引。

### 验证新功能

启用新SUG后，可以通过以下方式验证：

1. **API测试**：
   ```bash
   # 测试搜索建议
   curl "http://localhost:8000/api/search/suggest?q=Role&size=10"
   ```

2. **检查索引mapping**：
   ```bash
   curl "http://localhost:9200/products/_mapping" | jq '.products.mappings.properties.suggest'
   ```
   
   应该能看到`completion`类型的`suggest`字段。

3. **检查文档数据**：
   ```bash
   # 查看一个文档的suggest字段
   curl "http://localhost:9200/products/_search?size=1" | jq '.hits.hits[0]._source.suggest'
   ```

### 迁移说明

如果从旧的prefix查询方式迁移到Completion Suggester：

1. **代码已更新**：新的代码已经使用Completion Suggester API
2. **索引需要更新**：现有索引需要重建或更新，添加completion字段
3. **数据需要重新同步**：所有文档需要重新索引，以包含completion字段数据
