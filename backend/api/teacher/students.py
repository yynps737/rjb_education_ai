"""
教师端 - 学生管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models.database import get_db
from models.user import User, UserRole
from models.course import Course
from models.analytics import LearningProgress
from utils.auth import require_role
from services.analytics_service import analytics_service

router = APIRouter(tags=["Teacher - Students"])


@router.get("/")
async def get_teacher_students(
    course_id: Optional[int] = None,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取教师的学生列表"""
    # 获取教师的所有课程
    teacher_courses = db.query(Course).filter(Course.teacher_id == current_user.id)
    
    if course_id:
        teacher_courses = teacher_courses.filter(Course.id == course_id)
    
    teacher_courses = teacher_courses.all()
    
    if not teacher_courses:
        return {"students": []}
    
    # 收集所有学生
    students_dict = {}
    for course in teacher_courses:
        for student in course.users:
            if student.role == UserRole.STUDENT:
                if student.id not in students_dict:
                    students_dict[student.id] = {
                        "id": student.id,
                        "username": student.username,
                        "full_name": student.full_name,
                        "email": student.email,
                        "courses": []
                    }
                students_dict[student.id]["courses"].append({
                    "id": course.id,
                    "title": course.title
                })
    
    return {"students": list(students_dict.values())}


@router.get("/{student_id}")
async def get_student_details(
    student_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取学生详细信息"""
    # 验证学生是否在教师的课程中
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 检查是否有共同课程
    teacher_courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    shared_courses = [c for c in teacher_courses if student in c.users]
    
    if not shared_courses:
        raise HTTPException(status_code=403, detail="无权查看该学生信息")
    
    # 获取学生在共同课程中的表现
    analytics = analytics_service.get_student_analytics(db, student_id)
    
    return {
        "student": {
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "email": student.email
        },
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "progress": analytics.get("courses", [{}])[0].get("progress", 0),
                "average_score": analytics.get("courses", [{}])[0].get("average_score", 0)
            }
            for c in shared_courses
        ],
        "overall_performance": analytics.get("overall_performance", {})
    }


@router.get("/{student_id}/progress")
async def get_student_progress(
    student_id: int,
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取学生在特定课程的进度"""
    # 验证权限
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.teacher_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在或无权限")
    
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student or student not in course.users:
        raise HTTPException(status_code=404, detail="学生未选修此课程")
    
    # 获取进度信息
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == student_id,
        LearningProgress.course_id == course_id
    ).first()
    
    if not progress:
        return {
            "student_id": student_id,
            "course_id": course_id,
            "progress": 0,
            "completed_lessons": [],
            "time_spent_minutes": 0
        }
    
    return {
        "student_id": student_id,
        "course_id": course_id,
        "progress": progress.progress_percentage,
        "completed_lessons": progress.completed_lessons or [],
        "time_spent_minutes": progress.time_spent_minutes,
        "last_accessed": progress.last_accessed
    }


@router.get("/{student_id}/assignments")
async def get_student_assignments(
    student_id: int,
    course_id: Optional[int] = None,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取学生的作业情况"""
    # 验证权限
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 获取共同课程
    teacher_courses = db.query(Course).filter(Course.teacher_id == current_user.id)
    if course_id:
        teacher_courses = teacher_courses.filter(Course.id == course_id)
    teacher_courses = teacher_courses.all()
    
    shared_courses = [c for c in teacher_courses if student in c.users]
    if not shared_courses:
        raise HTTPException(status_code=403, detail="无权查看该学生作业")
    
    # 获取作业提交情况
    assignments_data = []
    for course in shared_courses:
        for assignment in course.assignments:
            submission = next((s for s in assignment.submissions if s.student_id == student_id), None)
            assignments_data.append({
                "assignment_id": assignment.id,
                "assignment_title": assignment.title,
                "course_title": course.title,
                "due_date": assignment.due_date,
                "total_points": assignment.total_points,
                "submitted": submission is not None,
                "submitted_at": submission.submitted_at if submission else None,
                "score": submission.score if submission else None,
                "status": submission.status if submission else "pending"
            })
    
    return {
        "student": {
            "id": student.id,
            "full_name": student.full_name
        },
        "assignments": assignments_data
    }