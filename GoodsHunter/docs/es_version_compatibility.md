# Elasticsearch 版本兼容性说明

## 问题

如果遇到以下错误：
```
BadRequestError(400, 'media_type_header_exception', 'Invalid media-type value on headers [Content-Type, Accept]', Accept version must be either version 8 or 7, but found 9)
```

说明 elasticsearch-py 客户端版本与 ES 服务器版本不兼容。

## 版本兼容性

- **ES 8.x 服务器** 需要 **elasticsearch-py 8.x** 客户端（版本范围：8.0.0 <= version < 9.0.0）
- **ES 9.x 服务器** 需要 **elasticsearch-py 9.x** 客户端（版本范围：9.0.0 <= version < 10.0.0）

## 解决方案

### 1. 检查当前版本

```bash
# 检查elasticsearch-py版本
python -c "import elasticsearch; print(elasticsearch.__version__)"

# 检查ES服务器版本
curl http://localhost:9200 | python -m json.tool | grep number
```

### 2. 修改requirements.txt

如果ES服务器是8.x，确保requirements.txt中指定：

```txt
elasticsearch>=8.0.0,<9.0.0
```

如果ES服务器是9.x，确保requirements.txt中指定：

```txt
elasticsearch>=9.0.0,<10.0.0
```

### 3. 重新安装依赖

```bash
# 卸载旧版本
pip uninstall elasticsearch -y

# 安装兼容版本
pip install "elasticsearch>=8.0.0,<9.0.0"
```

或者在虚拟环境中：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 重新安装依赖
pip install -r services/api/requirements.txt --force-reinstall
```

### 4. 验证

```bash
# 验证版本
python -c "import elasticsearch; print(elasticsearch.__version__)"

# 测试连接
python search/test_es_connection.py
```

## 当前配置

- **ES服务器版本**: 8.11.0 (docker-compose.yml中指定)
- **elasticsearch-py客户端版本**: 8.0.0 <= version < 9.0.0 (requirements.txt中指定)

## 注意事项

1. 确保客户端版本与服务器版本兼容
2. 如果升级ES服务器版本，需要同步升级客户端版本
3. 在生产环境中，建议固定具体版本号，而不是使用范围
