from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from models.user import User, UserRole
from models.course import Course
from models.assignment import Assignment
from utils.auth import require_role
from utils.response import success_response, error_response
from utils.pagination import paginate
from services.course_service import course_service

router = APIRouter()

class CourseCreateRequest(BaseModel):
    title: str
    description: str
    subject: str
    teacher_id: int
    grade_level: Optional[str] = None
    tags: Optional[List[str]] = None

class CourseUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    teacher_id: Optional[int] = None
    tags: Optional[List[str]] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    subject: str
    grade_level: Optional[str]
    teacher_id: int
    teacher_name: str
    student_count: int
    chapter_count: int
    assignment_count: int
    created_at: str

@router.get("")
async def get_all_courses(
    subject: Optional[str] = None,
    teacher_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all courses with filtering"""
    query = db.query(Course)

    if subject:
        query = query.filter(Course.subject == subject)

    if teacher_id:
        query = query.filter(Course.teacher_id == teacher_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Course.title.ilike(search_term)) |
            (Course.description.ilike(search_term))
        )

    result = paginate(query, page, page_size)

    courses = []
    for course in result["items"]:
        # Calculate completion rate (mock for now)
        completion_rate = 85 if len(course.users) > 0 else 0
        
        # Calculate average score (mock for now)
        average_score = 78 if len(course.users) > 0 else 0
        
        courses.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level or 1,
            "teacher_id": course.teacher_id,
            "teacher_name": course.teacher.full_name,
            "student_count": len(course.users),
            "chapter_count": len(course.chapters),
            "assignment_count": len(course.assignments),
            "is_published": True,  # Add published status
            "created_at": course.created_at.isoformat(),
            "updated_at": course.updated_at.isoformat() if hasattr(course, 'updated_at') else course.created_at.isoformat(),
            "completion_rate": completion_rate,
            "average_score": average_score
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

@router.post("", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    try:
        course = course_service.create_course(
            db,
            title=course_data.title,
            description=course_data.description,
            subject=course_data.subject,
            teacher_id=course_data.teacher_id,
            grade_level=course_data.grade_level,
            tags=course_data.tags
        )

        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            subject=course.subject,
            grade_level=course.grade_level,
            teacher_id=course.teacher_id,
            teacher_name=course.teacher.full_name,
            student_count=0,
            chapter_count=0,
            assignment_count=0,
            created_at=course.created_at.isoformat()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{course_id}")
async def get_course_details(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get detailed course information"""
    course = course_service.get_course_with_chapters(db, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 获取 enrollment details
    students = [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email
        }
        for user in course.users if user.role == UserRole.STUDENT
    ]

    # 获取 chapters
    chapters = [
        {
            "id": chapter.id,
            "title": chapter.title,
            "order": chapter.order,
            "lessons_count": len(chapter.lessons)
        }
        for chapter in course.chapters
    ]

    # 获取 assignments
    assignments = [
        {
            "id": assignment.id,
            "title": assignment.title,
            "status": assignment.status.value,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "submissions_count": len(assignment.submissions)
        }
        for assignment in course.assignments
    ]

    return success_response(data={
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level,
            "tags": course.tags,
            "created_at": course.created_at.isoformat()
        },
        "teacher": {
            "id": course.teacher.id,
            "username": course.teacher.username,
            "full_name": course.teacher.full_name,
            "email": course.teacher.email
        },
        "students": students,
        "chapters": chapters,
        "assignments": assignments
    })

@router.put("/{course_id}")
async def update_course(
    course_id: int,
    course_data: CourseUpdateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update course details"""
    course = course_service.get(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = {}

    if course_data.title is not None:
        update_data["title"] = course_data.title

    if course_data.description is not None:
        update_data["description"] = course_data.description

    if course_data.subject is not None:
        update_data["subject"] = course_data.subject

    if course_data.grade_level is not None:
        update_data["grade_level"] = course_data.grade_level

    if course_data.teacher_id is not None:
        # 验证 teacher exists
        teacher = db.query(User).filter(
            User.id == course_data.teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")
        update_data["teacher_id"] = course_data.teacher_id

    if course_data.tags is not None:
        update_data["tags"] = course_data.tags

    course = course_service.update(db, course, **update_data)

    return success_response(
        message="Course updated successfully",
        data={
            "id": course.id,
            "title": course.title
        }
    )

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a course"""
    course = course_service.get(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 检查 if course has enrolled students
    if course.users:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete course with {len(course.users)} enrolled students"
        )

    course_service.delete(db, course_id)

    return success_response(message="Course deleted successfully")

@router.post("/{course_id}/students/{student_id}")
async def enroll_student_admin(
    course_id: int,
    student_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Enroll a student in a course (admin action)"""
    try:
        course = course_service.enroll_student(db, course_id, student_id)
        return success_response(
            message=f"Student enrolled in {course.title} successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return error_response(str(e))

@router.delete("/{course_id}/students/{student_id}")
async def unenroll_student_admin(
    course_id: int,
    student_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Unenroll a student from a course (admin action)"""
    try:
        course = course_service.unenroll_student(db, course_id, student_id)
        return success_response(
            message=f"Student unenrolled from {course.title} successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return error_response(str(e))

@router.get("/stats/summary")
async def get_course_statistics(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get course statistics summary"""
    total_courses = db.query(Course).count()
    published_courses = total_courses  # Mock all as published for now

    # Courses by subject
    subjects = db.query(Course.subject, db.func.count(Course.id)).group_by(Course.subject).all()
    subject_distribution = [{"subject": subject, "count": count} for subject, count in subjects if subject]

    # Grade distribution
    grades = db.query(Course.grade_level, db.func.count(Course.id)).group_by(Course.grade_level).all()
    grade_distribution = [{"grade": int(grade) if grade else 1, "count": count} for grade, count in grades]

    # Total students
    total_students = db.query(User).filter(User.role == UserRole.STUDENT).count()

    # Total assignments
    total_assignments = db.query(Assignment).count()

    # Monthly courses (mock data for now)
    from datetime import datetime
    current_month = datetime.utcnow().strftime("%Y-%m")
    monthly_courses = [
        {"month": "2024-01", "count": 3},
        {"month": "2024-02", "count": 5},
        {"month": "2024-03", "count": 4},
        {"month": current_month, "count": total_courses}
    ]

    return success_response(data={
        "total_courses": total_courses,
        "published_courses": published_courses,
        "total_students": total_students,
        "total_assignments": total_assignments,
        "subject_distribution": subject_distribution,
        "grade_distribution": grade_distribution,
        "monthly_courses": monthly_courses
    })