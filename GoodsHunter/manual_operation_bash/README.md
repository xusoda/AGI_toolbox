# GoodsHunter 手动操作脚本

本目录包含 GoodsHunter 项目的各种手动操作脚本。

## 脚本说明

### 启动脚本

#### `start_all.sh` - 一键启动所有服务
启动 GoodsHunter 的完整服务栈：
- PostgreSQL 数据库 (端口 5432)
- MinIO 对象存储 (API: 9000, Console: 9001)
- API 服务 (端口 8000)
- Web 前端 (端口 3000)

**使用方法：**
```bash
./start_all.sh
```

**功能特性：**
- ✅ 自动检查系统依赖 (Docker, Docker Compose, Node.js, Python3)
- ✅ 按正确顺序启动服务并等待就绪
- ✅ 创建日志目录并分别记录各服务日志
- ✅ 提供完整的服务访问地址信息
- ✅ 支持 Ctrl+C 优雅停止所有服务

**日志文件：**
- `log/docker-compose.log` - Docker 服务日志
- `log/api.log` - API 服务日志
- `log/web.log` - Web 前端日志

#### `stop_all.sh` - 停止所有服务
停止所有正在运行的 GoodsHunter 服务。

**使用方法：**
```bash
./stop_all.sh
```

### 其他脚本

#### `run_crawl.sh` - 运行爬虫
执行商品数据爬取任务。

#### `run_item_extract.sh` - 运行商品提取
执行商品信息提取和处理任务。

## 服务访问地址

启动成功后，可以通过以下地址访问服务：

| 服务 | 地址 | 说明 |
|------|------|------|
| Web 前端 | http://localhost:3000 | 商品展示界面 |
| API 服务 | http://localhost:8000 | REST API 接口 |
| API 文档 | http://localhost:8000/docs | Swagger UI 文档 |
| PostgreSQL | localhost:5432 | 数据库连接 |
| MinIO API | http://localhost:9000 | 对象存储 API |
| MinIO Console | http://localhost:9001 | 管理控制台 |

## MinIO 默认配置

- 用户名: `minioadmin`
- 密码: `minioadmin123`
- 默认存储桶: `watch-images`

## 环境要求

- Docker & Docker Compose
- Node.js (推荐 LTS 版本)
- Python 3.8+
- curl (用于健康检查)

## 故障排除

1. **端口占用**: 如果端口被占用，脚本会报错。请检查端口使用情况或修改配置。

2. **依赖缺失**: 脚本会自动检查依赖，如有缺失会给出安装指导。

3. **启动超时**: 如果服务启动时间过长，可以适当增加脚本中的超时时间。

4. **日志查看**: 所有日志都保存在 `log/` 目录下，可以实时查看启动过程和错误信息。