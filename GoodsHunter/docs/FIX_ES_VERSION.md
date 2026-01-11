# 修复 Elasticsearch 版本兼容性问题

## 问题

错误信息：
```
BadRequestError(400, 'media_type_header_exception', 'Invalid media-type value on headers [Content-Type, Accept]', Accept version must be either version 8 or 7, but found 9. Accept=application/vnd.elasticsearch+json; compatible-with=9)
```

**原因**: elasticsearch-py 客户端版本（9.x）与 ES 服务器版本（8.x）不兼容。

## 解决方案

### 1. 修改 requirements.txt

已修改 `services/api/requirements.txt`：

```diff
- elasticsearch>=8.11.0
+ elasticsearch>=8.0.0,<9.0.0
```

这样会确保只安装 8.x 版本的客户端，与 ES 8.11.0 服务器兼容。

### 2. 重新安装依赖

需要重新安装 elasticsearch 库以匹配正确的版本：

```bash
# 激活虚拟环境（如果使用）
source .venv/bin/activate

# 卸载当前版本
pip uninstall elasticsearch -y

# 安装兼容版本
pip install "elasticsearch>=8.0.0,<9.0.0"

# 或者重新安装所有依赖
pip install -r services/api/requirements.txt --force-reinstall
```

### 3. 验证版本

```bash
# 检查安装的版本
python -c "import elasticsearch; print(elasticsearch.__version__)"

# 应该显示 8.x.x，例如：8.11.0
```

### 4. 测试连接

```bash
# 运行测试脚本
python search/test_es_connection.py

# 或者创建索引
python search/scripts/create_index.py
```

## 版本兼容性说明

- **ES 8.x 服务器** 需要 **elasticsearch-py 8.x** 客户端（8.0.0 <= version < 9.0.0）
- **ES 9.x 服务器** 需要 **elasticsearch-py 9.x** 客户端（9.0.0 <= version < 10.0.0）

当前配置：
- ES服务器：8.11.0（docker-compose.yml）
- elasticsearch-py客户端：8.0.0 <= version < 9.0.0（requirements.txt）

## 注意事项

1. **不要使用 `>=8.11.0`**：这会安装最新的 9.x 版本，与 ES 8.x 不兼容
2. **使用版本范围**：`>=8.0.0,<9.0.0` 确保只安装 8.x 版本
3. **在生产环境**：建议固定具体版本号，例如 `elasticsearch==8.11.0`
