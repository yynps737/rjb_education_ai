"""
教师端 - 作业管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models.database import get_db
from models.user import User, UserRole
from models.assignment import Assignment, AssignmentStatus
from utils.auth import require_role
from services.assignment_service import assignment_service

router = APIRouter(tags=["Teacher - Assignments"])


class AssignmentCreateRequest(BaseModel):
    """作业创建请求"""
    course_id: int
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    total_points: float = 100.0


class AssignmentUpdateRequest(BaseModel):
    """作业更新请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    total_points: Optional[float] = None
    status: Optional[AssignmentStatus] = None


@router.get("/")
async def get_teacher_assignments(
    course_id: Optional[int] = None,
    status: Optional[AssignmentStatus] = None,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取教师的作业列表"""
    query = db.query(Assignment).filter(
        Assignment.course.has(teacher_id=current_user.id)
    )
    
    if course_id:
        query = query.filter(Assignment.course_id == course_id)
    
    if status:
        query = query.filter(Assignment.status == status)
    
    assignments = query.all()
    
    return {
        "assignments": [
            {
                "id": a.id,
                "course_id": a.course_id,
                "course_title": a.course.title,
                "title": a.title,
                "description": a.description,
                "due_date": a.due_date,
                "total_points": a.total_points,
                "status": a.status.value,
                "submission_count": len(a.submissions),
                "created_at": a.created_at
            }
            for a in assignments
        ]
    }


@router.post("/")
async def create_assignment(
    request: AssignmentCreateRequest,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """创建新作业"""
    # 验证课程所有权
    from models.course import Course
    course = db.query(Course).filter(
        Course.id == request.course_id,
        Course.teacher_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在或无权限")
    
    assignment = assignment_service.create_assignment(
        db,
        course_id=request.course_id,
        title=request.title,
        description=request.description,
        instructions=request.instructions,
        due_date=request.due_date,
        total_points=request.total_points
    )
    
    return {
        "message": "作业创建成功",
        "assignment_id": assignment.id
    }


@router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    request: AssignmentUpdateRequest,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """更新作业"""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.course.has(teacher_id=current_user.id)
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在或无权限")
    
    update_data = request.dict(exclude_unset=True)
    assignment = assignment_service.update(db, assignment, **update_data)
    
    return {"message": "作业更新成功"}


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """删除作业"""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.course.has(teacher_id=current_user.id)
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在或无权限")
    
    if assignment.submissions:
        raise HTTPException(status_code=400, detail="已有学生提交，无法删除")
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "作业删除成功"}


@router.get("/{assignment_id}/submissions")
async def get_assignment_submissions(
    assignment_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取作业提交列表"""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.course.has(teacher_id=current_user.id)
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在或无权限")
    
    submissions = [
        {
            "id": s.id,
            "student_id": s.student_id,
            "student_name": s.student.full_name,
            "submitted_at": s.submitted_at,
            "status": s.status,
            "score": s.score,
            "feedback": s.feedback
        }
        for s in assignment.submissions
    ]
    
    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "total_points": assignment.total_points
        },
        "submissions": submissions,
        "statistics": {
            "total": len(submissions),
            "graded": len([s for s in submissions if s["score"] is not None]),
            "average_score": sum(s["score"] or 0 for s in submissions) / len(submissions) if submissions else 0
        }
    }