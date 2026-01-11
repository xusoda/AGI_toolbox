# 搜索调试指南

本文档说明如何检查搜索索引、查询改写和日志。

## 一、检查商品索引结构和多语言词表

### 1.1 检查单个商品的索引数据

使用 `search/scripts/inspect_index.py` 脚本可以查看指定商品的索引数据：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 查看商品ID为123的索引数据
python search/scripts/inspect_index.py --product-id 123
```

这会显示：
- 商品的基本信息（品牌名、型号名等）
- `brand_aliases`: 品牌的多语言别名数组
- `model_aliases`: 型号的多语言别名数组
- `search_text`: 合并的搜索文本（包含所有同义词）
- 完整的ES文档结构

### 1.2 检查Rolex品牌的所有商品，验证是否包含"劳力士"

```bash
# 查看Rolex品牌的所有商品索引，并检查是否包含"劳力士"
python search/scripts/inspect_index.py --brand Rolex --search-term 劳力士
```

这会显示：
- Rolex品牌的总商品数
- 每个商品是否包含"劳力士"这个搜索词
- 每个商品的品牌别名和型号别名
- 统计：包含/不包含该搜索词的商品数

### 1.3 检查词表中的品牌别名映射

```bash
# 查看词表中Rolex的别名映射
python search/scripts/inspect_index.py --check-word-mapping Rolex
```

这会显示从 `i18n/dictionaries/watch.yaml` 词表中加载的品牌别名列表。

### 1.4 使用Elasticsearch API直接查看索引

你也可以直接使用Elasticsearch API查看索引数据：

```bash
# 查看指定商品ID的文档
curl "http://localhost:9200/products/_doc/123?pretty"

# 查看Rolex品牌的所有商品（前10个）
curl -X POST "http://localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {"brand_name.keyword": "Rolex"}
  },
  "size": 10,
  "_source": ["id", "brand_name", "brand_aliases", "model_name", "model_aliases", "search_text"]
}
'

# 查看索引的mapping（字段结构）
curl "http://localhost:9200/products/_mapping?pretty"
```

## 二、查看搜索Query的改写和扩展过程

### 2.1 使用脚本解释查询结构

```bash
# 解释搜索查询"爱彼"是如何被构建的
python search/scripts/inspect_index.py --explain-query 爱彼
```

这会显示：
- ES查询的完整JSON结构
- 各个搜索字段的权重配置
- 查询类型和参数说明

### 2.2 查看搜索日志

搜索查询的日志记录在以下位置：

#### API服务日志（如果使用Docker）

```bash
# 查看API服务的日志
docker-compose logs -f api

# 或者查看最近的日志
docker-compose logs --tail=100 api
```

#### 本地开发环境

日志输出到标准输出（stdout），可以在运行API服务的终端中查看。

搜索相关的日志位置：
- **查询构建**: `search/es_engine.py` 中的 `_build_search_query` 方法
- **搜索执行**: `search/es_engine.py` 中的 `search` 方法
- **API路由**: `services/api/app/routers/search.py` 中的 `search_products` 函数

### 2.3 启用详细日志

要查看更详细的搜索日志，可以在代码中添加日志输出。搜索查询的构建过程在 `search/es_engine.py` 的 `_build_search_query` 方法中。

要查看实际执行的ES查询，可以在 `search/es_engine.py` 的 `search` 方法中添加日志：

```python
# 在 search 方法中，执行搜索前添加
logger.info(f"执行搜索查询: query={query}, ES查询={json.dumps(es_query, ensure_ascii=False)}")
```

### 2.4 使用Elasticsearch的查询分析功能

Elasticsearch提供了 `_validate` 和 `_explain` API来分析查询：

```bash
# 验证查询语法
curl -X POST "http://localhost:9200/products/_validate/query?explain&pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "爱彼",
      "fields": ["brand_name^3", "brand_aliases^2.5", "model_name^2", "model_aliases^1.5", "search_text^1", "model_no^1"],
      "type": "best_fields",
      "operator": "or",
      "fuzziness": "AUTO"
    }
  }
}
'

# 解释为什么某个文档被匹配（需要提供文档ID）
curl -X POST "http://localhost:9200/products/_explain/DOCUMENT_ID?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "爱彼",
      "fields": ["brand_name^3", "brand_aliases^2.5", "model_name^2", "model_aliases^1.5", "search_text^1", "model_no^1"],
      "type": "best_fields",
      "operator": "or",
      "fuzziness": "AUTO"
    }
  }
}
'
```

## 三、调试"爱彼"搜索出现"爱马仕"的问题

### 3.1 问题分析

根据词表文件 `i18n/dictionaries/watch.yaml`：
- **Audemars Piguet (爱彼)**: 别名包含 `["オーデマ ピゲ", "オーデマ・ピゲ", "爱彼", "AP","オーデマピゲ"]`
- **Hermes (爱马仕)**: 别名包含 `["エルメス", "Hermès", "爱马仕"]`

这两个品牌的中文别名完全不同，不应该互相匹配。

### 3.2 排查步骤

#### 步骤1: 检查索引中的别名数据

```bash
# 检查爱彼(Audemars Piguet)商品的索引
python search/scripts/inspect_index.py --brand "Audemars Piguet"

# 检查爱马仕(Hermes)商品的索引
python search/scripts/inspect_index.py --brand Hermes

# 查看词表中的映射
python search/scripts/inspect_index.py --check-word-mapping "Audemars Piguet"
python search/scripts/inspect_index.py --check-word-mapping Hermes
```

#### 步骤2: 查看实际执行的ES查询

在 `search/es_engine.py` 的 `search` 方法中添加日志：

```python
logger.info(f"搜索查询: '{query}', ES查询JSON: {json.dumps(es_query, ensure_ascii=False)}")
```

#### 步骤3: 使用ES API测试查询

```bash
# 测试"爱彼"查询会返回哪些商品
curl -X POST "http://localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "爱彼",
      "fields": ["brand_name^3", "brand_aliases^2.5", "model_name^2", "model_aliases^1.5", "search_text^1", "model_no^1"],
      "type": "best_fields",
      "operator": "or",
      "fuzziness": "AUTO"
    }
  },
  "size": 20,
  "_source": ["id", "brand_name", "brand_aliases", "model_name"]
}
'
```

#### 步骤4: 检查模糊匹配问题

ES查询中使用了 `"fuzziness": "AUTO"`，这可能导致相似字符的误匹配。可以尝试：

1. **临时禁用模糊匹配**来测试是否是模糊匹配导致的问题
2. **检查分词器**：如果使用了IK分词器，"爱彼"和"爱马仕"可能被分词为相似的词

#### 步骤5: 查看日志中的错误信息

```bash
# 查看API服务的日志
docker-compose logs api | grep -i "爱彼\|爱马仕\|error\|warning"

# 或者查看搜索模块的日志
docker-compose logs api | grep -i "search"
```

### 3.3 可能的原因

1. **模糊匹配 (fuzziness)**：`"fuzziness": "AUTO"` 可能导致"爱彼"和"爱马仕"被误匹配
2. **分词问题**：如果使用了不适当的分词器，可能导致中文分词错误
3. **索引数据错误**：某些商品的 `brand_aliases` 字段可能包含了错误的别名
4. **查询权重问题**：`search_text` 字段权重较低，但如果该字段包含了其他品牌的关键词，仍可能被匹配

### 3.4 解决方案

1. **调整模糊匹配参数**：如果确认是模糊匹配导致的问题，可以：
   - 移除 `"fuzziness": "AUTO"`
   - 或者使用更严格的模糊匹配策略

2. **检查索引数据**：确保每个商品的 `brand_aliases` 字段只包含该品牌的正确别名

3. **重新索引数据**：如果索引数据有问题，可以重新同步：
   ```bash
   python search/scripts/update_aliases.py --rebuild-all
   ```

## 四、日志位置总结

### 4.1 API服务日志

- **Docker环境**: `docker-compose logs api`
- **本地开发**: 标准输出（运行API服务的终端）
- **日志级别**: INFO（可在 `services/api/app/main.py` 中配置）

### 4.2 搜索模块日志

搜索相关的日志记录位置：
- `search/es_engine.py`: ES搜索执行日志
- `search/service.py`: 搜索服务层日志
- `services/api/app/routers/search.py`: API路由层日志

### 4.3 启用DEBUG日志

要启用更详细的日志，可以在代码中临时添加：

```python
import logging
logging.getLogger('search').setLevel(logging.DEBUG)
logging.getLogger('search.es_engine').setLevel(logging.DEBUG)
```

或者在 `services/api/app/main.py` 中配置：

```python
logging.getLogger("search").setLevel(logging.DEBUG)
```

## 五、快速检查命令汇总

```bash
# 1. 检查Rolex商品是否包含"劳力士"
python search/scripts/inspect_index.py --brand Rolex --search-term 劳力士

# 2. 查看词表中Rolex的别名
python search/scripts/inspect_index.py --check-word-mapping Rolex

# 3. 解释"爱彼"查询的结构
python search/scripts/inspect_index.py --explain-query 爱彼

# 4. 查看API服务日志（Docker）
docker-compose logs -f api

# 5. 直接查询ES索引（查看Rolex商品）
curl -X POST "http://localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'{"query":{"term":{"brand_name.keyword":"Rolex"}},"size":5}'

# 6. 重新索引所有数据
python search/scripts/update_aliases.py --rebuild-all
```
