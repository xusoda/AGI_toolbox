# 搜索建议(SUG)中文前缀匹配问题修复

## 问题描述

输入中文前缀（如"劳"）时，无法匹配到完整词条（如"劳力士"），即使"劳力士"存在于ES文档的suggest字段中。

## 问题原因

Elasticsearch的Completion Suggester对于中文前缀匹配存在限制：

1. **Completion Suggester的限制**：Completion Suggester使用FST（有限状态转换器）数据结构，它是基于单词边界的前缀匹配，对于中文这种没有明确单词边界的语言，支持不够理想。

2. **中文字符的特殊性**：中文是表意文字，每个字符通常都是独立的，Completion Suggester默认可能不会正确处理中文字符的前缀匹配。

## 解决方案

将Completion Suggester改为使用`match_phrase_prefix`查询，这样可以更好地支持中文前缀匹配。

### 修改内容

1. **修改`suggest`方法** (`search/es_engine.py`)：
   - 移除Completion Suggester API调用
   - 使用`match_phrase_prefix`查询在`brand_name`、`brand_aliases`、`model_name`、`model_aliases`、`search_text`等字段上进行前缀匹配
   - 从返回的文档中提取所有可能的词条（品牌名、型号名、别名等）
   - 检查每个词条是否以查询前缀开头，支持中英文混合匹配

2. **优势**：
   - 对中文前缀匹配支持更好
   - 可以匹配到别名中的词条（如"劳力士"）
   - 不需要特殊的mapping配置
   - 实现相对简单

3. **劣势**：
   - 性能可能略低于Completion Suggester（但对于中小规模数据影响不大）
   - 需要从返回的文档中提取词条，增加了处理逻辑

## 测试验证

修复后，使用以下命令测试：

```bash
# 测试API
curl "http://localhost:8000/api/search/suggest?q=劳&size=10"

# 或使用Python脚本
cd GoodsHunter
source ../.venv/bin/activate
python -m search.scripts.test_suggest --query "劳" --test-engine
```

应该能够返回包含"劳力士"的建议列表。

## 注意事项

1. **不需要重建索引**：由于使用了现有的text字段（如`brand_aliases`、`model_aliases`），不需要重建索引。

2. **性能考虑**：`match_phrase_prefix`查询的性能取决于数据量和查询复杂度。对于中小规模数据（< 100万文档），性能应该可以接受。

3. **去重处理**：代码中已经实现了去重逻辑，确保不会返回重复的建议。

4. **大小写不敏感**：匹配时使用大小写不敏感的比较，支持中英文混合查询。

## 相关文件

- `search/es_engine.py` - suggest方法实现
- `search/i18n/index_builder.py` - 索引构建（alias处理）
- `docs/TROUBLESHOOTING_SUG_CHINESE.md` - 排查指南