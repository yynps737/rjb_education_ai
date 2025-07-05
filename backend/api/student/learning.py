from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from models.user import User, UserRole
from models.course import Chapter, Lesson
from utils.auth import require_role
from utils.response import success_response, error_response
from services.analytics_service import analytics_service
from services.knowledge_service import knowledge_service

router = APIRouter()

class LessonResponse(BaseModel):
    id: int
    title: str
    content: str
    order: int
    duration_minutes: Optional[int]
    knowledge_points: List[str]
    resources: List[dict]
    progress: float

class ChapterWithLessons(BaseModel):
    id: int
    title: str
    description: Optional[str]
    order: int
    progress: float
    lessons: List[LessonResponse]

class TrackProgressRequest(BaseModel):
    time_spent: int = 0  # minutes

class AskQuestionRequest(BaseModel):
    question: str
    course_id: Optional[int] = None

@router.get("/courses/{course_id}/chapters", response_model=List[ChapterWithLessons])
async def get_course_chapters_with_progress(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get all chapters with lessons and progress for a course"""
    # 验证enrollment
    from services.course_service import course_service
    course = course_service.get_course_with_chapters(db, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    chapters_data = []

    for chapter in course.chapters:
        # 获取chapter progress
        chapter_progress = db.query(analytics_service.LearningProgress).filter(
            analytics_service.LearningProgress.user_id == current_user.id,
            analytics_service.LearningProgress.chapter_id == chapter.id,
            analytics_service.LearningProgress.lesson_id.is_(None)
        ).first()

        # 获取lessons with progress
        lessons_data = []
        for lesson in chapter.lessons:
            lesson_progress = db.query(analytics_service.LearningProgress).filter(
                analytics_service.LearningProgress.user_id == current_user.id,
                analytics_service.LearningProgress.lesson_id == lesson.id
            ).first()

            lessons_data.append(LessonResponse(
                id=lesson.id,
                title=lesson.title,
                content=lesson.content,
                order=lesson.order,
                duration_minutes=lesson.duration_minutes,
                knowledge_points=lesson.knowledge_points or [],
                resources=lesson.resources or [],
                progress=lesson_progress.progress_percentage if lesson_progress else 0.0
            ))

        chapters_data.append(ChapterWithLessons(
            id=chapter.id,
            title=chapter.title,
            description=chapter.description,
            order=chapter.order,
            progress=chapter_progress.progress_percentage if chapter_progress else 0.0,
            lessons=lessons_data
        ))

    return chapters_data

@router.get("/lessons/{lesson_id}")
async def get_lesson_content(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get lesson content and mark as accessed"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # 验证enrollment
    course = lesson.chapter.course
    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    # Track access
    analytics_service.track_learning_progress(
        db,
        user_id=current_user.id,
        course_id=course.id,
        chapter_id=lesson.chapter_id,
        lesson_id=lesson_id,
        time_spent=1  # Initial access
    )

    # 获取related knowledge base内容
    related_content = []
    if lesson.knowledge_points:
        for point in lesson.knowledge_points[:3]:  # Top 3 knowledge points
            results = await knowledge_service.search_knowledge(
                query=point,
                course_id=course.id,
                top_k=2
            )
            related_content.extend(results)

    return success_response(data={
        "lesson": {
            "id": lesson.id,
            "title": lesson.title,
            "content": lesson.content,
            "duration_minutes": lesson.duration_minutes,
            "knowledge_points": lesson.knowledge_points or [],
            "resources": lesson.resources or []
        },
        "chapter": {
            "id": lesson.chapter.id,
            "title": lesson.chapter.title
        },
        "course": {
            "id": course.id,
            "title": course.title
        },
        "related_content": related_content
    })

@router.post("/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    lesson_id: int,
    progress_data: TrackProgressRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Update learning progress for a lesson"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # 验证enrollment
    course = lesson.chapter.course
    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    # 更新progress
    progress = analytics_service.track_learning_progress(
        db,
        user_id=current_user.id,
        course_id=course.id,
        chapter_id=lesson.chapter_id,
        lesson_id=lesson_id,
        time_spent=progress_data.time_spent
    )

    # 记录performance metric
    analytics_service.record_performance_metric(
        db,
        user_id=current_user.id,
        course_id=course.id,
        metric_type="lesson_completion",
        value=progress.progress_percentage,
        metadata={
            "lesson_id": lesson_id,
            "time_spent": progress_data.time_spent
        }
    )

    return success_response(
        message="Progress updated",
        data={
            "lesson_progress": progress.progress_percentage,
            "total_time_spent": progress.time_spent_minutes
        }
    )

@router.post("/ask")
async def ask_question(
    request: AskQuestionRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Ask a question and get AI-powered answer"""
    # If course_id provided, 验证enrollment
    if request.course_id:
        from services.course_service import course_service
        course = course_service.get(db, request.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if current_user not in course.users:
            raise HTTPException(
                status_code=403,
                detail="You are not enrolled in this course"
            )

    try:
        # 获取answer using RAG
        answer = await knowledge_service.ask_question(
            question=request.question,
            course_id=request.course_id
        )

        # Log the question for analytics
        analytics_service.record_performance_metric(
            db,
            user_id=current_user.id,
            course_id=request.course_id or 0,
            metric_type="question_asked",
            value=1,
            metadata={
                "question": request.question[:200]
                # 前200 chars
            }
        )

        return success_response(data={
            "question": request.question,
            "answer": answer
        })
    except Exception as e:
        return error_response(f"Failed to process question: {str(e)}")

@router.get("/progress/summary")
async def get_learning_summary(
    course_id: Optional[int] = None,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get learning progress summary"""
    summary = analytics_service.get_student_analytics(
        db,
        student_id=current_user.id,
        course_id=course_id
    )

    return success_response(data=summary)

@router.get("/progress")
async def get_learning_progress(
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get overall learning progress"""
    summary = analytics_service.get_student_analytics(
        db,
        student_id=current_user.id
    )
    
    return success_response(data=summary)