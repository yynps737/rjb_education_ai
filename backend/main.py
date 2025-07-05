"""
教育AI助手 - 核心启动文件
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
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
from api.knowledge import router as knowledge_router

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动教育AI助手...")

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