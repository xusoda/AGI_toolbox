# 修复 Docker 镜像构建问题

## 问题

API 服务启动时报错：
```
ImportError: elasticsearch 库未安装，请运行: pip install 'elasticsearch>=8.0.0,<9.0.0'
```

## 原因

修改了 `services/api/requirements.txt` 后，Docker 镜像没有重新构建，容器内还是旧的依赖。

## 解决方案

### 1. 修改启动脚本

已修改 `manual_operation_bash/start_all.sh`：

```diff
- docker compose up -d 2>&1 | tee "$DOCKER_LOG" &
+ docker compose up -d --build 2>&1 | tee "$DOCKER_LOG" &
```

`--build` 参数会检查代码或依赖是否有变化，如果有变化会自动重新构建镜像。

### 2. 手动重新构建镜像（如果需要）

如果需要强制重新构建（不使用缓存）：

```bash
# 重新构建 API 服务镜像
docker compose build --no-cache api

# 然后启动服务
docker compose up -d
```

或者使用启动脚本（已包含构建）：

```bash
./manual_operation_bash/start_all.sh
```

### 3. 验证依赖安装

检查容器内的依赖是否安装正确：

```bash
# 进入 API 容器
docker compose exec api bash

# 检查 elasticsearch 版本
pip show elasticsearch

# 或者直接测试导入
python -c "import elasticsearch; print(elasticsearch.__version__)"

# 退出容器
exit
```

### 4. 查看构建日志

如果构建失败，查看详细日志：

```bash
# 查看构建日志
docker compose build api

# 查看容器日志
docker compose logs api
```

## 注意事项

1. **首次启动或依赖更新后**：使用 `--build` 参数确保镜像是最新的
2. **开发环境**：使用 `--build` 可以自动检测变化并重新构建
3. **生产环境**：建议固定版本号，并在部署时显式构建镜像
4. **构建缓存**：Docker 会缓存构建层，只有变化的层才会重新构建，所以不会太慢

## 验证修复

1. 重新运行启动脚本：
   ```bash
   ./manual_operation_bash/start_all.sh
   ```

2. 等待服务启动完成后，检查 API 服务是否正常：
   ```bash
   curl http://localhost:8000/health
   ```

3. 测试搜索功能（需要先创建索引和同步数据）：
   ```bash
   curl "http://localhost:8000/api/search?q=test"
   ```
