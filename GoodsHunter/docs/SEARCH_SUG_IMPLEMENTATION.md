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

### Elasticsearch实现（当前）

现在ES的SUG实现方式：

1. **索引字段**：在ES索引中包含以下字段
   - `brand_name` (text)
   - `model_name` (text)
   - `model_no` (keyword)
   - `brand_aliases` (text) - 品牌的多语言别名数组
   - `model_aliases` (text) - 型号的多语言别名数组

2. **查询方式**：使用 `prefix` 查询进行前缀匹配
   ```python
   # 代码位置：search/es_engine.py
   def suggest(self, query: str, size: int = 5) -> List[str]:
       query_clean = query.strip().lower()
       
       es_query = {
           "query": {
               "bool": {
                   "should": [
                       {"prefix": {"brand_name": query_clean}},
                       {"prefix": {"model_name": query_clean}},
                       {"prefix": {"model_no": query_clean}},
                       {"prefix": {"brand_aliases": query_clean}},
                       {"model_aliases": {"model_aliases": query_clean}}
                   ]
               }
           },
           "size": size * 3,  # 多取一些以便去重
           "_source": ["brand_name", "model_name", "model_no"]
       }
       
       response = self.es_client.search(index=self.index_name, body=es_query)
       
       suggestions = set()
       for hit in response["hits"]["hits"]:
           source = hit["_source"]
           if source.get("brand_name"):
               suggestions.add(source["brand_name"])
           if source.get("model_name"):
               suggestions.add(source["model_name"])
           if source.get("model_no"):
               suggestions.add(source["model_no"])
       
       return sorted(list(suggestions))[:size]
   ```

3. **特点**：
   - 使用ES的 `prefix` 查询进行前缀匹配
   - 在5个字段上搜索：`brand_name`, `model_name`, `model_no`, `brand_aliases`, `model_aliases`
   - **支持多语言别名匹配**（这是ES实现的主要优势）
   - 使用Python的 `set` 去重，然后排序并截取前N个结果
   - 性能更好，支持更大的数据集

### 对比总结

| 特性 | PostgreSQL实现 | Elasticsearch实现 |
|------|---------------|-------------------|
| **索引类型** | `text_pattern_ops` 索引 | ES倒排索引（自动） |
| **查询方式** | `ILIKE` 前缀匹配 | `prefix` 查询 |
| **搜索字段** | 3个：brand_name, model_name, model_no | 5个：brand_name, model_name, model_no, brand_aliases, model_aliases |
| **多语言支持** | ❌ 不支持 | ✅ 支持（通过别名数组） |
| **去重方式** | SQL UNION | Python set |
| **性能** | 依赖索引，中等 | 优秀，支持大数据集 |
| **实现位置** | `search/postgres_engine.py`（已删除） | `search/es_engine.py` |

### ES实现的主要优势

1. **多语言别名支持**：
   - 搜索"Rolex"时，可以匹配到别名数组中的"ロレックス"、"劳力士"等
   - PostgreSQL实现只能在单一字段上匹配

2. **更好的性能**：
   - ES的倒排索引天然支持前缀查询
   - 不需要特殊的操作符类

3. **更灵活的查询**：
   - 可以轻松扩展搜索字段
   - 支持更复杂的查询逻辑

## 相关代码位置

- **ES SUG实现**：`search/es_engine.py` 的 `suggest()` 方法（第313-359行）
- **API端点**：`services/api/app/routers/search.py` 的 `/search/suggest` 路由（第278-296行）
- **已删除的PostgreSQL实现**：`search/postgres_engine.py`（已删除）
