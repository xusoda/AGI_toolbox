# GoodsHunter Web 前端

React + TypeScript + Vite 前端应用，移动端优先设计。

## 功能

- 商品列表页：两列网格布局（移动端），支持分页和排序
- 商品详情页：大图展示、字段信息、外链跳转

## 安装和运行

```bash
# 安装依赖
npm install

# 开发模式运行
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 环境变量

创建 `.env` 文件（可选）：

```bash
VITE_API_BASE_URL=/api
```

默认会使用 Vite 的代理配置（`vite.config.ts`），将 `/api` 请求代理到 `http://localhost:8000`。

## 开发

- 开发服务器运行在 `http://localhost:3000`
- API 请求会自动代理到后端服务（`http://localhost:8000`）

