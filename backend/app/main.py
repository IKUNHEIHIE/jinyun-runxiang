import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import (
    auth, home, course, ai_workshop, community,
    teacher, activity, mall, device, admin
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="《津韵润乡——天津非遗赋能乡村美育智能应用》统一后端服务API",
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

# 链路追踪中间件
@app.middleware("http")
async def add_trace_id_header(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex)
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

# 统一异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 5000, "message": f"服务器开小差了: {str(exc)}", "data": None}
    )

# 挂载业务路由
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(home.router, prefix=settings.API_V1_PREFIX)
app.include_router(course.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_workshop.router, prefix=settings.API_V1_PREFIX)
app.include_router(community.router, prefix=settings.API_V1_PREFIX)
app.include_router(teacher.router, prefix=settings.API_V1_PREFIX)
app.include_router(activity.router, prefix=settings.API_V1_PREFIX)
app.include_router(mall.router, prefix=settings.API_V1_PREFIX)
app.include_router(device.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["基础监控"])
def health_check():
    return {"status": "UP", "version": settings.VERSION, "project": settings.PROJECT_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
