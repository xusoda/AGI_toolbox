# 搜索建议(SUG)中文前缀匹配问题排查指南

## 问题描述

输入中文前缀（如"劳"）时，无法匹配到完整词条（如"劳力士"），即使"劳力士"存在于ES文档的suggest字段中。

## 原因分析

Elasticsearch的Completion Suggester对于中文前缀匹配存在限制：

1. **Completion Suggester的限制**：Completion Suggester使用FST（有限状态转换器）数据结构，它是基于单词边界的前缀匹配，对于中文这种没有明确单词边界的语言，支持不够理想。

2. **中文字符的特殊性**：中文是表意文字，每个字符通常都是独立的，Completion Suggester默认可能不会正确处理中文字符的前缀匹配。

## 排查步骤

### 1. 检查ES文档结构

检查suggest字段是否正确包含"劳力士"：

```bash
# 使用curl查询包含Rolex的文档
curl -X GET "http://localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {"brand_name.keyword": "Rolex"}
  },
  "size": 1
}'

# 检查返回文档的suggest字段
# 确认suggest.input数组中是否包含"劳力士"
```

或使用Python脚本：

```bash
cd GoodsHunter
source ../.venv/bin/activate
python -m search.scripts.inspect_index --brand Rolex --search-term 劳力士
```

### 2. 检查索引mapping

检查suggest字段的mapping配置：

```bash
curl -X GET "http://localhost:9200/products/_mapping?pretty" | grep -A 10 suggest
```

确认suggest字段：
- 类型为`completion`
- **没有**使用analyzer（或使用keyword analyzer）

### 3. 测试Completion Suggester查询

直接测试Completion Suggester查询：

```bash
curl -X POST "http://localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "suggest": {
    "product-suggest": {
      "prefix": "劳",
      "completion": {
        "field": "suggest",
        "size": 10,
        "skip_duplicates": true
      }
    }
  }
}'
```

如果返回空结果，说明Completion Suggester确实无法匹配中文前缀。

### 4. 检查alias是否正确添加

检查alias解析是否正确：

```bash
cd GoodsHunter
source ../.venv/bin/activate
python -m search.scripts.inspect_index --check-word-mapping Rolex
```

确认返回的别名列表中包含"劳力士"。

## 解决方案

### 方案1：使用prefix查询替代Completion Suggester（推荐）

Completion Suggester对中文支持有限，可以改用普通的prefix查询配合text字段。需要修改`suggest`方法使用prefix查询：

**优点**：
- 对中文前缀匹配支持更好
- 实现简单
- 不需要特殊的mapping配置

**缺点**：
- 性能可能略低于Completion Suggester（但对于中小规模数据影响不大）

**实现方式**：
1. 在suggest字段所在的文本字段（如`brand_aliases`、`model_aliases`或`search_text`）上进行prefix查询
2. 或者创建一个专门的text字段用于suggest查询

### 方案2：在input中添加字符级前缀（复杂，不推荐）

在构建suggest字段时，不仅添加完整词条（如"劳力士"），还添加前缀（如"劳"、"劳力"）。但这会显著增加存储和索引的复杂度。

### 方案3：使用拼音或拼音首字母

在suggest字段的input中添加拼音或拼音首字母（如"laolishi"或"lls"），这样可以通过拼音前缀匹配。但需要额外的拼音转换逻辑。

## 推荐方案：使用prefix查询

考虑到Completion Suggester对中文的限制，推荐改用prefix查询。这样可以：
1. 保持对中文的良好支持
2. 实现相对简单
3. 对于中小规模数据，性能影响可接受

## 测试验证

修复后，使用以下命令测试：

```bash
# 测试API
curl "http://localhost:8000/api/search/suggest?q=劳&size=10"

# 或使用Python脚本
python -m search.scripts.test_suggest --query "劳" --test-engine
```

应该能够返回包含"劳力士"的建议列表。