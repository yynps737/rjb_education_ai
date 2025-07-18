"""
教育AI助手 - 核心启动文件
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('../.env')
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging

# 设置Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入路由
from api.auth import router as auth_router
from api.admin import analytics_router, courses_router as admin_courses_router, system_router, users_router
from api.student import assignments_router, courses_router as student_courses_router, learning_router, profile_router
from api.teacher.course_design import router as teacher_router
from api.teacher.assignments import router as teacher_assignments_router
from api.teacher.students import router as teacher_students_router
from api.teacher.stats import router as teacher_stats_router
from api.knowledge import router as knowledge_router

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动教育AI助手...")
    
    # 确保必要的目录存在
    try:
        from ensure_directories import ensure_directories
        ensure_directories()
        logger.info("目录结构检查完成")
    except Exception as e:
        logger.error(f"创建目录失败: {e}")

    # 初始化数据库
    try:
        from models.database import init_db
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    yield

    logger.info("关闭教育AI助手...")

# 创建FastAPI应用
app = FastAPI(
    title="教育AI助手",
    description="基于千问API的智能教育平台",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # 暴露所有响应头
)

# 添加中间件确保流式响应不被缓冲
@app.middleware("http")
async def disable_buffering(request: Request, call_next):
    """禁用响应缓冲，特别是对于SSE端点"""
    response = await call_next(request)
    
    # 如果是SSE端点，确保不缓冲
    if request.url.path.endswith("-stream"):
        response.headers["X-Accel-Buffering"] = "no"
        response.headers["Cache-Control"] = "no-cache"
        
    return response

# 导入错误处理
from utils.error_handler import AppError, create_error_response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 全局异常处理器
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """处理应用自定义错误"""
    return create_error_response(
        error_code=exc.error_code,
        status_code=exc.status_code,
        detail=exc.detail.get("message") if isinstance(exc.detail, dict) else None,
        request=request
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return create_error_response(
        error_code="INVALID_INPUT",
        status_code=422,
        detail="; ".join(errors),
        request=request
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理HTTP异常"""
    return create_error_response(
        error_code="HTTP_ERROR",
        status_code=exc.status_code,
        detail=exc.detail,
        request=request
    )

# 配置信任的主机
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["知识库"])

# 管理员路由
app.include_router(users_router, prefix="/api/admin/users", tags=["管理员-用户"])
app.include_router(admin_courses_router, prefix="/api/admin/courses", tags=["管理员-课程"])
app.include_router(analytics_router, prefix="/api/admin/analytics", tags=["管理员-分析"])
app.include_router(system_router, prefix="/api/admin/system", tags=["管理员-系统"])

# 学生路由
app.include_router(student_courses_router, prefix="/api/student/courses", tags=["学生-课程"])
app.include_router(assignments_router, prefix="/api/student/assignments", tags=["学生-作业"])
app.include_router(learning_router, prefix="/api/student/learning", tags=["学生-学习"])
app.include_router(profile_router, prefix="/api/student/profile", tags=["学生-个人资料"])

# 教师路由
app.include_router(teacher_router, prefix="/api/teacher/course", tags=["教师-课程设计"])
app.include_router(teacher_assignments_router, prefix="/api/teacher/assignments", tags=["教师-作业"])
app.include_router(teacher_students_router, prefix="/api/teacher/students", tags=["教师-学生"])
app.include_router(teacher_stats_router, prefix="/api", tags=["教师-统计"])

# 挂载静态文件目录
from pathlib import Path
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 根路由
@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "教育AI助手API",
        "version": "1.0.0",
        "status": "运行中"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 运行服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )