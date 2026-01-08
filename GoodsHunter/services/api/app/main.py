"""FastAPI 应用主入口"""
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import items

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 获取 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 设置 uvicorn 日志级别
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

app = FastAPI(
    title="GoodsHunter API",
    description="商品浏览 API 服务",
    version="1.0.0"
)

logger.info("FastAPI 应用初始化完成")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(items.router, prefix="/api", tags=["items"])


@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": "GoodsHunter API", "status": "ok"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

