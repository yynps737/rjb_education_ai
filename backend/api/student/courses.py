from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from models.user import User, UserRole
from models.course import Course
from models.analytics import LearningProgress
from utils.auth import get_current_active_user, require_role
from utils.response import success_response, error_response
from utils.pagination import paginate, PaginationParams
from services.course_service import course_service
from services.analytics_service import analytics_service

router = APIRouter()

class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    subject: str
    grade_level: Optional[str]
    teacher_name: str
    enrolled_students: int
    progress: float = 0.0

    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    chapters: List[dict]
    assignments_count: int
    completed_assignments: int

@router.get("/enrolled", response_model=List[CourseResponse])
async def get_enrolled_courses(
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get all courses the student is enrolled in"""
    courses = course_service.get_courses_by_student(db, current_user.id)

    response = []
    for course in courses:
        # 获取progress
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == current_user.id,
            LearningProgress.course_id == course.id,
            LearningProgress.chapter_id.is_(None)
        ).first()

        course_data = CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            subject=course.subject,
            grade_level=course.grade_level,
            teacher_name=course.teacher.full_name,
            enrolled_students=len(course.users),
            progress=progress.progress_percentage if progress else 0.0
        )
        response.append(course_data)

    return response

@router.get("/available")
async def get_available_courses(
    subject: Optional[str] = None,
    grade_level: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get available courses to enroll in"""
    # 获取courses not enrolled in
    enrolled_ids = [c.id for c in course_service.get_courses_by_student(db, current_user.id)]

    query = db.query(Course)

    if enrolled_ids:
        query = query.filter(~Course.id.in_(enrolled_ids))

    if subject:
        query = query.filter(Course.subject == subject)

    if grade_level:
        query = query.filter(Course.grade_level == grade_level)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Course.title.ilike(search_term)) |
            (Course.description.ilike(search_term))
        )

    result = paginate(query, page, page_size)

    courses = []
    for course in result["items"]:
        courses.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level,
            "teacher_name": course.teacher.full_name,
            "enrolled_students": len(course.users)
        })

    return success_response(data={
        "courses": courses,
        "pagination": {
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"]
        }
    })

@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Enroll in a course"""
    try:
        course = course_service.enroll_student(db, course_id, current_user.id)

        # 初始化learning progress
        analytics_service.track_learning_progress(
            db,
            user_id=current_user.id,
            course_id=course_id
        )

        return success_response(
            message=f"Successfully enrolled in {course.title}",
            data={"course_id": course.id}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return error_response(str(e))

@router.delete("/{course_id}/unenroll")
async def unenroll_from_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Unenroll from a course"""
    try:
        course = course_service.unenroll_student(db, course_id, current_user.id)
        return success_response(
            message=f"Successfully unenrolled from {course.title}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return error_response(str(e))

@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course_details(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get detailed course information"""
    course = course_service.get_course_with_chapters(db, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 检查if student is enrolled
    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in this course to view details"
        )

    # 获取progress
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
        LearningProgress.course_id == course.id,
        LearningProgress.chapter_id.is_(None)
    ).first()

    # 获取作业stats
    from models.assignment import Assignment, Submission
    total_assignments = db.query(Assignment).filter(
        Assignment.course_id == course_id,
        Assignment.status == "published"
    ).count()

    completed_assignments = db.query(Submission).join(Assignment).filter(
        Assignment.course_id == course_id,
        Submission.student_id == current_user.id,
        Submission.status == "graded"
    ).count()

    # 格式化chapters
    chapters = []
    for chapter in course.chapters:
        chapter_progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == current_user.id,
            LearningProgress.chapter_id == chapter.id,
            LearningProgress.lesson_id.is_(None)
        ).first()

        chapters.append({
            "id": chapter.id,
            "title": chapter.title,
            "description": chapter.description,
            "order": chapter.order,
            "progress": chapter_progress.progress_percentage if chapter_progress else 0.0,
            "lessons_count": len(chapter.lessons)
        })

    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        subject=course.subject,
        grade_level=course.grade_level,
        teacher_name=course.teacher.full_name,
        enrolled_students=len(course.users),
        progress=progress.progress_percentage if progress else 0.0,
        chapters=chapters,
        assignments_count=total_assignments,
        completed_assignments=completed_assignments
    )