import os
import uuid
from loguru import logger
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api import api_router

# 初始化企业级规范 FastAPI 实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="《津韵润乡——天津非遗赋能乡村美育智能应用》工业化后端服务架构",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载真实多模态资产静态目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 链路追踪与结构化访问日志中间件
@app.middleware("http")
async def add_trace_id_and_log(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex)
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    logger.info(f"[{request_id[:8]}] {request.method} {request.url.path} -> {response.status_code}")
    return response

# 统一异常拦截处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 4220, "message": "请求参数校验失败", "detail": exc.errors(), "data": None}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"code": 5000, "message": f"服务器开小差了: {str(exc)}", "data": None}
    )

# 挂载业务路由：同时挂载 /api 与 /api/v1，确保完美向前与向后兼容
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["基础监控"])
def health_check():
    return {
        "status": "UP",
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME,
        "architecture": "FastAPI-Production-Enterprise-V1"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
