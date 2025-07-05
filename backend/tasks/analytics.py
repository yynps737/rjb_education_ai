from celery import shared_task
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from models.database import get_db_session
from models.user import User, UserRole
from models.course import Course
from models.analytics import LearningProgress, PerformanceMetrics
from models.assignment import Submission
from services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

@shared_task
def generate_course_report(course_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive analytics report for a course
    """
    try:
        with get_db_session() as db:
            course = db.query(Course).filter(Course.id == course_id).first()

            if not course:
                return {"status": "error", "message": "Course not found"}

            logger.info(f"Generating report for course {course_id}: {course.title}")

            # 获取 analytics
            analytics = analytics_service.get_course_analytics(db, course_id)

            # Additional metrics
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)

            # Weekly 激活 students
            weekly_active = db.query(LearningProgress.user_id).filter(
                LearningProgress.course_id == course_id,
                LearningProgress.last_accessed >= week_ago
            ).distinct().count()

            # Completion rate
            completed_students = db.query(LearningProgress.user_id).filter(
                LearningProgress.course_id == course_id,
                LearningProgress.progress_percentage >= 100,
                LearningProgress.chapter_id.is_(None)
            ).count()

            analytics["weekly_active_students"] = weekly_active
            analytics["completion_rate"] = (
                completed_students / analytics["total_students"] * 100
                if analytics["total_students"] > 0 else 0
            )

            # Store report
            report_metric = PerformanceMetrics(
                user_id=course.teacher_id,
                course_id=course_id,
                metric_type="course_report",
                value=analytics["average_progress"],
                metadata=analytics,
                recorded_at=datetime.utcnow()
            )

            db.add(report_metric)
            db.commit()

            return {
                "status": "success",
                "course_id": course_id,
                "report_generated": True,
                "key_metrics": {
                    "total_students": analytics["total_students"],
                    "active_students": analytics["active_students"],
                    "average_progress": analytics["average_progress"],
                    "completion_rate": analytics["completion_rate"]
                }
            }

    except Exception as e:
        logger.error(f"Error generating course report: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def generate_student_report(student_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive analytics report for a student
    """
    try:
        with get_db_session() as db:
            student = db.query(User).filter(
                User.id == student_id,
                User.role == UserRole.STUDENT
            ).first()

            if not student:
                return {"status": "error", "message": "Student not found"}

            logger.info(f"Generating report for student {student_id}: {student.username}")

            # 获取 analytics
            analytics = analytics_service.get_student_analytics(db, student_id)

            # Calculate additional insights
            insights = {
                "strength_areas": [],
                "improvement_areas": [],
                "recommendations": []
            }

            # Analyze performance by course
            for course_data in analytics.get("courses", []):
                avg_score = course_data.get("assignments", {}).get("average_score", 0)

                if avg_score >= 80:
                    insights["strength_areas"].append({
                        "course": course_data["course_title"],
                        "score": avg_score
                    })
                elif avg_score < 60 and avg_score > 0:
                    insights["improvement_areas"].append({
                        "course": course_data["course_title"],
                        "score": avg_score
                    })

            # 生成 recommendations
            if insights["improvement_areas"]:
                insights["recommendations"].append(
                    "Focus on courses where average score is below 60%"
                )

            if analytics.get("overall_performance", {}).get("active_courses", 0) == 0:
                insights["recommendations"].append(
                    "Start engaging with course materials regularly"
                )

            # Store report
            report_data = {
                **analytics,
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat()
            }

            return {
                "status": "success",
                "student_id": student_id,
                "report_generated": True,
                "summary": {
                    "total_courses": len(analytics.get("courses", [])),
                    "average_score": analytics.get("overall_performance", {}).get("average_score", 0),
                    "insights_count": len(insights["recommendations"])
                }
            }

    except Exception as e:
        logger.error(f"Error generating student report: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def generate_daily_report() -> Dict[str, Any]:
    """
    Generate daily platform-wide analytics report
    """
    try:
        with get_db_session() as db:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)

            logger.info(f"Generating daily report for {yesterday}")

            # Daily 激活 users
            daily_active_users = db.query(LearningProgress.user_id).filter(
                func.date(LearningProgress.last_accessed) == yesterday
            ).distinct().count()

            # Daily submissions
            daily_submissions = db.query(Submission).filter(
                func.date(Submission.submitted_at) == yesterday
            ).count()

            # Daily learning time
            daily_learning_time = db.query(
                func.sum(LearningProgress.time_spent_minutes)
            ).filter(
                func.date(LearningProgress.last_accessed) == yesterday
            ).scalar() or 0

            # New enrollments
            from models.user import User
            new_enrollments = db.query(func.count(func.distinct(User.id))).select_from(User).join(
                User.courses
            ).filter(
                func.date(User.created_at) == yesterday
            ).scalar() or 0

            # 平均 scores for graded submissions
            daily_avg_score = db.query(func.avg(Submission.score)).filter(
                func.date(Submission.submitted_at) == yesterday,
                Submission.score.isnot(None)
            ).scalar() or 0

            report = {
                "date": yesterday.isoformat(),
                "active_users": daily_active_users,
                "submissions": daily_submissions,
                "learning_hours": round(daily_learning_time / 60, 1),
                "new_enrollments": new_enrollments,
                "average_score": round(daily_avg_score, 1),
                "generated_at": datetime.utcnow().isoformat()
            }

            # Store in metrics
            metric = PerformanceMetrics(
                user_id=1,
                # 系统 user
                course_id=0,
                # 平台-wide
                metric_type="daily_report",
                value=daily_active_users,
                # 主 metric
                metadata=report,
                recorded_at=datetime.utcnow()
            )

            db.add(metric)
            db.commit()

            logger.info(f"Daily report generated: {report}")

            return {
                "status": "success",
                "report": report
            }

    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def calculate_learning_paths() -> Dict[str, Any]:
    """
    Calculate optimal learning paths for students based on performance
    """
    try:
        with get_db_session() as db:
            # 获取 全部 激活 students
            students = db.query(User).filter(
                User.role == UserRole.STUDENT,
                User.is_active == True
            ).all()

            paths_calculated = 0

            for student in students:
                # 获取 student's performance 数据
                analytics = analytics_service.get_student_analytics(db, student.id)

                # Simple learning 路径 logic
                recommendations = []

                for course_data in analytics.get("courses", []):
                    progress = course_data.get("progress", 0)
                    avg_score = course_data.get("assignments", {}).get("average_score", 0)

                    if progress < 50:
                        recommendations.append({
                            "course_id": course_data["course_id"],
                            "action": "continue_learning",
                            "priority": "high" if progress < 25 else "medium"
                        })
                    elif avg_score < 70 and avg_score > 0:
                        recommendations.append({
                            "course_id": course_data["course_id"],
                            "action": "review_materials",
                            "priority": "medium"
                        })

                if recommendations:
                    # Store learning 路径
                    metric = PerformanceMetrics(
                        user_id=student.id,
                        course_id=0,
                        metric_type="learning_path",
                        value=len(recommendations),
                        metadata={
                            "recommendations": recommendations,
                            "generated_at": datetime.utcnow().isoformat()
                        },
                        recorded_at=datetime.utcnow()
                    )
                    db.add(metric)
                    paths_calculated += 1

            db.commit()

            return {
                "status": "success",
                "students_processed": len(students),
                "paths_calculated": paths_calculated
            }

    except Exception as e:
        logger.error(f"Error calculating learning paths: {str(e)}")
        return {"status": "error", "message": str(e)}