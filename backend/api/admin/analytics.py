from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.user import User, UserRole
from models.course import Course
from models.assignment import Assignment, Submission
from models.analytics import LearningProgress, PerformanceMetrics
from utils.auth import require_role
from utils.response import success_response
from services.analytics_service import analytics_service

router = APIRouter()

@router.get("/overview")
async def get_platform_overview(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get platform-wide analytics overview"""
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(LearningProgress.user_id).filter(
        LearningProgress.last_accessed >= datetime.utcnow() - timedelta(days=7)
    ).distinct().count()

    users_by_role = {}
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        users_by_role[role.value] = count

    # Course statistics
    total_courses = db.query(Course).count()
    courses_with_students = db.query(Course.id).join(Course.users).distinct().count()

    # 作业 statistics
    total_assignments = db.query(Assignment).count()
    total_submissions = db.query(Submission).count()
    graded_submissions = db.query(Submission).filter(
        Submission.status == "graded"
    ).count()

    # Calculate 平均 scores
    avg_score = db.query(func.avg(Submission.score)).filter(
        Submission.score.isnot(None)
    ).scalar() or 0

    # Learning time
    total_learning_minutes = db.query(
        func.sum(LearningProgress.time_spent_minutes)
    ).scalar() or 0

    return success_response(data={
        "users": {
            "total": total_users,
            "active_last_7_days": active_users,
            "by_role": users_by_role
        },
        "courses": {
            "total": total_courses,
            "active": courses_with_students,
            "utilization_rate": round(courses_with_students / total_courses * 100, 1) if total_courses > 0 else 0
        },
        "assignments": {
            "total": total_assignments,
            "submissions": total_submissions,
            "graded": graded_submissions,
            "average_score": round(avg_score, 1)
        },
        "engagement": {
            "total_learning_hours": round(total_learning_minutes / 60, 1),
            "average_learning_hours_per_user": (
                round(total_learning_minutes / 60 / total_users, 1) if total_users > 0 else 0
            )
        }
    })

@router.get("/courses/{course_id}")
async def get_course_analytics(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific course"""
    analytics = analytics_service.get_course_analytics(db, course_id)

    if not analytics:
        return success_response(data={"error": "Course not found"}, status_code=404)

    return success_response(data=analytics)

@router.get("/students/{student_id}")
async def get_student_analytics(
    student_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific student"""
    # 验证 student exists
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT
    ).first()

    if not student:
        return success_response(data={"error": "Student not found"}, status_code=404)

    analytics = analytics_service.get_student_analytics(db, student_id)

    # Add student 信息
    analytics["student_info"] = {
        "id": student.id,
        "username": student.username,
        "full_name": student.full_name,
        "email": student.email,
        "created_at": student.created_at.isoformat()
    }

    return success_response(data=analytics)

@router.get("/trends/enrollment")
async def get_enrollment_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get enrollment trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 获取 daily enrollment counts
    enrollments = []
    current = start_date

    while current <= end_date:
        next_day = current + timedelta(days=1)

        # 计数 enrollments for this day
        count = db.query(func.count(func.distinct(User.id))).select_from(User).join(
            User.courses
        ).filter(
            User.created_at >= current,
            User.created_at < next_day
        ).scalar() or 0

        enrollments.append({
            "date": current.strftime("%Y-%m-%d"),
            "enrollments": count
        })

        current = next_day

    return success_response(data={
        "period_days": days,
        "enrollments": enrollments
    })

@router.get("/trends/performance")
async def get_performance_trends(
    days: int = Query(30, ge=7, le=365),
    metric_type: str = Query("assignment_score", enum=["assignment_score", "quiz_score", "participation"]),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get performance trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 获取 daily 平均 performance
    performance = []
    current = start_date

    while current <= end_date:
        next_day = current + timedelta(days=1)

        # 获取 平均 metric for this day
        avg_value = db.query(func.avg(PerformanceMetrics.value)).filter(
            PerformanceMetrics.metric_type == metric_type,
            PerformanceMetrics.recorded_at >= current,
            PerformanceMetrics.recorded_at < next_day
        ).scalar() or 0

        performance.append({
            "date": current.strftime("%Y-%m-%d"),
            "average": round(avg_value, 2)
        })

        current = next_day

    return success_response(data={
        "period_days": days,
        "metric_type": metric_type,
        "performance": performance
    })

@router.get("/top/students")
async def get_top_students(
    limit: int = Query(10, ge=1, le=50),
    course_id: Optional[int] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get top performing students"""
    # Base 查询 for students with submissions
    query = db.query(
        User.id,
        User.username,
        User.full_name,
        func.avg(Submission.score).label('avg_score'),
        func.count(Submission.id).label('submission_count')
    ).join(
        Submission, User.id == Submission.student_id
    ).filter(
        User.role == UserRole.STUDENT,
        Submission.score.isnot(None)
    )

    if course_id:
        query = query.join(Assignment).filter(Assignment.course_id == course_id)

    # 分组 by student and order by 平均 score
    top_students = query.group_by(
        User.id, User.username, User.full_name
    ).order_by(
        func.avg(Submission.score).desc()
    ).limit(limit).all()

    return success_response(data={
        "top_students": [
            {
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "average_score": round(student.avg_score, 1),
                "submissions": student.submission_count
            }
            for student in top_students
        ]
    })

@router.get("/top/courses")
async def get_popular_courses(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get most popular courses by enrollment"""
    courses = db.query(
        Course.id,
        Course.title,
        Course.subject,
        func.count(User.id).label('student_count')
    ).join(
        Course.users
    ).filter(
        User.role == UserRole.STUDENT
    ).group_by(
        Course.id, Course.title, Course.subject
    ).order_by(
        func.count(User.id).desc()
    ).limit(limit).all()

    return success_response(data={
        "popular_courses": [
            {
                "id": course.id,
                "title": course.title,
                "subject": course.subject,
                "enrolled_students": course.student_count
            }
            for course in courses
        ]
    })

@router.get("/engagement/heatmap")
async def get_engagement_heatmap(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get hourly engagement heatmap"""
    since = datetime.utcnow() - timedelta(days=days)

    # 初始化 heatmap 数据 (24 hours x 7 days)
    heatmap = {}
    for hour in range(24):
        heatmap[hour] = {}
        for day in range(7):
            heatmap[hour][day] = 0

    # 获取 learning activities
    activities = db.query(
        LearningProgress.last_accessed
    ).filter(
        LearningProgress.last_accessed >= since
    ).all()

    # Populate heatmap
    for activity in activities:
        hour = activity.last_accessed.hour
        day = activity.last_accessed.weekday()
        heatmap[hour][day] += 1

    # 格式化 for 响应
    formatted_heatmap = []
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for hour in range(24):
        for day in range(7):
            formatted_heatmap.append({
                "hour": hour,
                "day": days_of_week[day],
                "activity_count": heatmap[hour][day]
            })

    return success_response(data={
        "period_days": days,
        "heatmap": formatted_heatmap
    })