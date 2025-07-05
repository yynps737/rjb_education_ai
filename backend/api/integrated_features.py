
"""
整合所有功能的API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

# 简化导入，避免依赖问题
try:
    from models.database import get_db
except:
    def get_db():
        pass

# 占位符 - 从主应用注入
def get_current_user():
    pass

try:
    from services.course_crud import course_service
    from services.assignment_crud import assignment_service
    from services.progress_tracking import progress_service
    from services.ai_integration import ai_service
    services_available = True
except:
    services_available = False

# 课程管理路由
course_router = APIRouter(prefix="/courses", tags=["课程管理"])

@course_router.post("/")
async def create_course(
    title: str,
    description: str,
    subject: str,
    grade_level: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新课程"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create courses")

    course = course_service.create_course(
        db, current_user.id, title, description, subject, grade_level
    )
    return {"success": True, "data": course}

@course_router.get("/{course_id}")
async def get_course(
    course_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程详情"""
    course = course_service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"success": True, "data": course}

# 作业管理路由
assignment_router = APIRouter(prefix="/assignments", tags=["作业管理"])

@assignment_router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    content: str,
    file_url: str = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交作业"""
    submission = assignment_service.submit_assignment(
        db, assignment_id, current_user.id, content, file_url
    )
    return {"success": True, "data": submission}

# AI功能路由
ai_router = APIRouter(prefix="/ai", tags=["AI功能"])

@ai_router.post("/question")
async def ask_ai(
    question: str,
    context: str = "",
    current_user=Depends(get_current_user)
):
    """向AI提问"""
    answer = await ai_service.answer_question(question, context)
    return {"success": True, "data": {"answer": answer}}

# 学习进度路由
progress_router = APIRouter(prefix="/progress", tags=["学习进度"])

@progress_router.post("/update")
async def update_progress(
    lesson_id: int,
    progress_percent: float,
    time_spent: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新学习进度"""
    progress = progress_service.update_progress(
        db, current_user.id, lesson_id, progress_percent, time_spent
    )
    return {"success": True, "data": progress}
