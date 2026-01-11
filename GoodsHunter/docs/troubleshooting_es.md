# Elasticsearch 问题排查指南

## 检查ES是否正常运行

### 1. 检查ES服务状态

```bash
# 检查Docker容器状态
docker ps | grep elasticsearch

# 或使用docker-compose
docker-compose ps elasticsearch

# 查看ES容器日志
docker-compose logs elasticsearch
```

### 2. 检查ES连接

```bash
# 检查ES是否响应
curl http://localhost:9200

# 检查集群健康状态
curl http://localhost:9200/_cluster/health

# 检查节点信息
curl http://localhost:9200/_nodes
```

### 3. 使用Python脚本测试连接

```bash
# 运行测试脚本
python search/test_es_connection.py
```

## 常见错误和解决方法

### 错误1: BadRequestError(400, 'None')

**原因**: ES 8.x API参数传递方式有问题

**解决方法**: 
1. 检查代码是否使用了正确的API参数
2. 在ES 8.x中，`indices.create`应该使用直接参数而不是body参数

**修复后的代码**:
```python
# 错误的方式（ES 8.x不支持）
self.es_client.indices.create(index=index_name, body=mapping)

# 正确的方式（ES 8.x）
self.es_client.indices.create(
    index=index_name,
    mappings=mappings,
    settings=settings
)
```

### 错误2: ConnectionError

**原因**: ES服务未启动或无法连接

**解决方法**:
1. 检查ES容器是否运行: `docker ps | grep elasticsearch`
2. 检查ES端口是否被占用: `lsof -i :9200`
3. 查看ES日志: `docker-compose logs elasticsearch`

### 错误3: RequestError(400, 'illegal_argument_exception')

**原因**: 索引映射或设置参数有问题

**解决方法**:
1. 检查mappings和settings的格式是否正确
2. 确保所有字段类型都有效
3. 检查是否有不支持的设置

### 错误4: 索引已存在

**解决方法**:
```bash
# 删除已存在的索引
curl -X DELETE http://localhost:9200/products

# 或使用Python
python -c "from elasticsearch import Elasticsearch; es = Elasticsearch(['http://localhost:9200']); es.indices.delete(index='products', ignore=[404])"
```

## 调试技巧

### 1. 启用详细日志

在代码中添加日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 测试ES API

使用curl测试ES API：
```bash
# 创建索引
curl -X PUT "http://localhost:9200/test_index" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "name": {"type": "text"}
    }
  }
}'

# 查看索引
curl -X GET "http://localhost:9200/test_index"

# 删除索引
curl -X DELETE "http://localhost:9200/test_index"
```

### 3. 检查ES版本

```bash
curl http://localhost:9200 | python -m json.tool
```

确认elasticsearch-py版本与ES版本兼容：
- ES 8.x 需要 elasticsearch-py >= 8.0.0

## 验证索引创建

### 1. 检查索引是否存在

```bash
curl http://localhost:9200/_cat/indices?v
```

### 2. 查看索引映射

```bash
curl http://localhost:9200/products/_mapping | python -m json.tool
```

### 3. 测试搜索

```bash
curl -X GET "http://localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  }
}'
```
