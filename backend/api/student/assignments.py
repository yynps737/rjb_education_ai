from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from models.user import User, UserRole
from models.assignment import Assignment, Submission, AssignmentStatus
from utils.auth import require_role
from utils.response import success_response, error_response
from services.assignment_service import assignment_service

router = APIRouter()

class AssignmentListResponse(BaseModel):
    id: int
    title: str
    course_title: str
    due_date: Optional[datetime]
    total_points: float
    status: str
    submission_status: Optional[str]
    score: Optional[float]

class QuestionResponse(BaseModel):
    id: int
    question_type: str
    content: str
    options: Optional[List[str]]
    points: float
    order: int

class AnswerSubmission(BaseModel):
    question_id: int
    content: Any

class SubmissionRequest(BaseModel):
    answers: List[AnswerSubmission]

@router.get("", response_model=List[AssignmentListResponse])
async def get_assignments(
    course_id: Optional[int] = None,
    status: Optional[str] = Query(None, enum=["pending", "submitted", "graded"]),
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get assignments for the student"""
    # Base 查询 for published assignments in enrolled courses
    from models.course import Course
    query = db.query(Assignment).join(Assignment.course).join(Course.users).filter(
        Assignment.status == AssignmentStatus.PUBLISHED,
        Course.users.contains(current_user)
    )

    if course_id:
        query = query.filter(Assignment.course_id == course_id)

    assignments = query.all()

    # 获取 submission status for each 作业
    response = []
    for assignment in assignments:
        submission = db.query(Submission).filter(
            Submission.assignment_id == assignment.id,
            Submission.student_id == current_user.id
        ).first()

        submission_status = None
        score = None

        if submission:
            submission_status = submission.status
            score = submission.score
        elif assignment.due_date and assignment.due_date < datetime.utcnow():
            submission_status = "overdue"
        else:
            submission_status = "pending"

        # 过滤 by status if requested
        if status and submission_status != status:
            continue

        response.append(AssignmentListResponse(
            id=assignment.id,
            title=assignment.title,
            course_title=assignment.course.title,
            due_date=assignment.due_date,
            total_points=assignment.total_points,
            status=assignment.status.value,
            submission_status=submission_status,
            score=score
        ))

    return response

@router.get("/{assignment_id}")
async def get_assignment_details(
    assignment_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get assignment details with questions"""
    assignment = assignment_service.get_assignment_with_questions(db, assignment_id)

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 检查 if student is enrolled in the course
    if current_user not in assignment.course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    # 检查 if already submitted
    submission = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == current_user.id
    ).first()

    # 格式化 questions (hide correct answers)
    questions = []
    for question in assignment.questions:
        questions.append(QuestionResponse(
            id=question.id,
            question_type=question.question_type.value,
            content=question.content,
            options=question.options,
            points=question.points,
            order=question.order
        ))

    return success_response(data={
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "instructions": assignment.instructions,
            "due_date": assignment.due_date,
            "total_points": assignment.total_points,
            "course": {
                "id": assignment.course.id,
                "title": assignment.course.title
            }
        },
        "questions": questions,
        "submission": {
            "submitted": submission is not None,
            "submitted_at": submission.submitted_at if submission else None,
            "status": submission.status if submission else None,
            "score": submission.score if submission else None
        }
    })

@router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    submission_data: SubmissionRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Submit assignment answers"""
    try:
        # 转换 answer 格式化
        answers = [
            {
                "question_id": answer.question_id,
                "content": answer.content
            }
            for answer in submission_data.answers
        ]

        submission = assignment_service.submit_assignment(
            db,
            assignment_id=assignment_id,
            student_id=current_user.id,
            answers=answers
        )

        # Auto-grade if possible
        from services.grading_service import grading_service
        submission = await grading_service.grade_submission(db, submission.id)

        return success_response(
            message="Assignment submitted successfully",
            data={
                "submission_id": submission.id,
                "status": submission.status,
                "score": submission.score
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return error_response(f"Failed to submit assignment: {str(e)}")

@router.get("/{assignment_id}/submission")
async def get_submission_details(
    assignment_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get submission details with feedback"""
    submission = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == current_user.id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    from services.grading_service import grading_service
    details = grading_service.get_submission_details(db, submission.id)

    return success_response(data=details)

@router.get("/upcoming", response_model=List[AssignmentListResponse])
async def get_upcoming_assignments(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get upcoming assignments due in the next N days"""
    from datetime import timedelta

    cutoff_date = datetime.utcnow() + timedelta(days=days)

    # 获取 assignments due soon that haven't been submitted
    assignments = db.query(Assignment).join(Assignment.course).filter(
        Assignment.status == AssignmentStatus.PUBLISHED,
        Assignment.course.has(users=current_user),
        Assignment.due_date.isnot(None),
        Assignment.due_date <= cutoff_date,
        Assignment.due_date >= datetime.utcnow()
    ).order_by(Assignment.due_date).all()

    # 过滤 out submitted assignments
    upcoming = []
    for assignment in assignments:
        submission = db.query(Submission).filter(
            Submission.assignment_id == assignment.id,
            Submission.student_id == current_user.id
        ).first()

        if not submission:
            upcoming.append({
                "id": assignment.id,
                "title": assignment.title,
                "course_title": assignment.course.title,
                "due_date": assignment.due_date,
                "total_points": assignment.total_points,
                "days_remaining": (assignment.due_date - datetime.utcnow()).days
            })

    return success_response(data={
        "upcoming_assignments": upcoming,
        "count": len(upcoming)
    })