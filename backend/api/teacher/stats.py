"""
教师统计API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, Any

from models.database import get_db
from models.user import User, user_courses, UserRole
from models.course import Course, Chapter, Lesson
from models.assignment import Assignment, Submission
from utils.auth import require_role
from utils.response import StandardResponse

router = APIRouter(prefix="/teacher", tags=["教师统计"])

@router.get("/stats")
async def get_teacher_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.TEACHER]))
):
    """获取教师的统计数据"""
    try:
        # 1. 获取教师的课程数量
        total_courses = db.query(func.count(Course.id)).filter(
            Course.created_by == current_user.id,
            Course.is_deleted == False
        ).scalar() or 0
        
        # 2. 获取学生总数（所有选修教师课程的学生）
        total_students = db.query(func.count(func.distinct(user_courses.c.user_id))).join(
            Course, Course.id == user_courses.c.course_id
        ).filter(
            Course.created_by == current_user.id,
            Course.is_deleted == False
        ).scalar() or 0
        
        # 3. 获取作业总数
        total_assignments = db.query(func.count(Assignment.id)).join(
            Lesson, Lesson.id == Assignment.lesson_id
        ).join(
            Chapter, Chapter.id == Lesson.chapter_id
        ).join(
            Course, Course.id == Chapter.course_id
        ).filter(
            Course.created_by == current_user.id,
            Assignment.is_deleted == False
        ).scalar() or 0
        
        # 4. 获取平均分数
        avg_score_result = db.query(func.avg(Submission.score)).join(
            Assignment, Assignment.id == Submission.assignment_id
        ).join(
            Lesson, Lesson.id == Assignment.lesson_id
        ).join(
            Chapter, Chapter.id == Lesson.chapter_id
        ).join(
            Course, Course.id == Chapter.course_id
        ).filter(
            Course.created_by == current_user.id,
            Submission.score.isnot(None)
        ).scalar()
        
        average_score = float(avg_score_result) if avg_score_result else 0.0
        
        # 5. 获取今日提交的作业数
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        today_questions = db.query(func.count(Submission.id)).join(
            Assignment, Assignment.id == Submission.assignment_id
        ).join(
            Lesson, Lesson.id == Assignment.lesson_id
        ).join(
            Chapter, Chapter.id == Lesson.chapter_id
        ).join(
            Course, Course.id == Chapter.course_id
        ).filter(
            Course.created_by == current_user.id,
            func.date(Submission.submitted_at) == today
        ).scalar() or 0
        
        # 6. 计算本周进度（已批改作业占比）
        week_start = today - timedelta(days=today.weekday())
        week_submissions = db.query(func.count(Submission.id)).join(
            Assignment, Assignment.id == Submission.assignment_id
        ).join(
            Lesson, Lesson.id == Assignment.lesson_id
        ).join(
            Chapter, Chapter.id == Lesson.chapter_id
        ).join(
            Course, Course.id == Chapter.course_id
        ).filter(
            Course.created_by == current_user.id,
            func.date(Submission.submitted_at) >= week_start
        ).scalar() or 0
        
        week_graded = db.query(func.count(Submission.id)).join(
            Assignment, Assignment.id == Submission.assignment_id
        ).join(
            Lesson, Lesson.id == Assignment.lesson_id
        ).join(
            Chapter, Chapter.id == Lesson.chapter_id
        ).join(
            Course, Course.id == Chapter.course_id
        ).filter(
            Course.created_by == current_user.id,
            func.date(Submission.submitted_at) >= week_start,
            Submission.score.isnot(None)
        ).scalar() or 0
        
        weekly_progress = int((week_graded / week_submissions * 100) if week_submissions > 0 else 0)
        
        return StandardResponse.success({
            "total_courses": total_courses,
            "total_students": total_students,
            "total_assignments": total_assignments,
            "average_score": round(average_score, 2),
            "today_questions": today_questions,
            "weekly_progress": weekly_progress
        })
        
    except Exception as e:
        return StandardResponse.error(f"获取统计数据失败: {str(e)}")

@router.get("/courses/stats")
async def get_teacher_courses_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.TEACHER]))
):
    """获取教师每门课程的统计数据"""
    try:
        courses = db.query(Course).filter(
            Course.created_by == current_user.id,
            Course.is_deleted == False
        ).all()
        
        course_stats = []
        for course in courses:
            # 获取课程的学生数
            student_count = db.query(func.count(user_courses.c.user_id)).filter(
                user_courses.c.course_id == course.id
            ).scalar() or 0
            
            # 获取课程的作业数
            assignment_count = db.query(func.count(Assignment.id)).join(
                Lesson, Lesson.id == Assignment.lesson_id
            ).join(
                Chapter, Chapter.id == Lesson.chapter_id
            ).filter(
                Chapter.course_id == course.id,
                Assignment.is_deleted == False
            ).scalar() or 0
            
            # 获取课程的平均分
            avg_score = db.query(func.avg(Submission.score)).join(
                Assignment, Assignment.id == Submission.assignment_id
            ).join(
                Lesson, Lesson.id == Assignment.lesson_id
            ).join(
                Chapter, Chapter.id == Lesson.chapter_id
            ).filter(
                Chapter.course_id == course.id,
                Submission.score.isnot(None)
            ).scalar()
            
            course_stats.append({
                "course_id": course.id,
                "course_title": course.title,
                "student_count": student_count,
                "assignment_count": assignment_count,
                "average_score": round(float(avg_score) if avg_score else 0, 2)
            })
        
        return StandardResponse.success({
            "courses": course_stats,
            "total": len(course_stats)
        })
        
    except Exception as e:
        return StandardResponse.error(f"获取课程统计失败: {str(e)}")