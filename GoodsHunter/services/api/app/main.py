"""FastAPI 应用主入口"""
import logging
import sys
from pathlib import Path

# 先配置基础日志（在使用 logging 之前）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 在导入其他模块之前，添加项目根目录到 sys.path
# 这样所有模块都可以导入 enums、i18n、search 等全局模块
# 注意：避免在 Docker 环境中使用 resolve()，可能导致路径问题
possible_roots = [
    Path(__file__).parent.parent.parent.parent,  # 从 services/api/app/main.py 向上4级到 GoodsHunter
    Path(__file__).parent.parent.parent,  # 从 services/api/app/main.py 向上3级
    Path("/app").parent,  # Docker 容器中，/app 的父目录（不使用 resolve）
]

# 查找项目根目录（通过 enums 目录）
project_root = None
for root in possible_roots:
    try:
        # 避免使用 resolve()，直接检查路径
        enums_path = root / "enums"
        if enums_path.exists() and enums_path.is_dir():
            project_root = str(root.absolute()) if hasattr(root, 'absolute') else str(root)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                logger.info(f"[Main] 添加项目根目录到 sys.path: {project_root}")
            break
    except (OSError, PermissionError) as e:
        # 忽略权限错误或路径访问错误，继续尝试下一个路径
        logger.debug(f"[Main] 检查路径 {root} 时出错: {e}")
        continue
    except Exception as e:
        logger.debug(f"[Main] 检查路径 {root} 时出错: {e}")
        continue

if project_root is None:
    logger.warning("[Main] 警告: 未找到项目根目录，enums 模块可能无法导入")
    logger.debug(f"[Main] 当前工作目录: {Path.cwd()}")
    logger.debug(f"[Main] Python 路径: {sys.path}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import items, search

# 设置日志级别
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
app.include_router(search.router, prefix="/api", tags=["search"])


@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": "GoodsHunter API", "status": "ok"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

