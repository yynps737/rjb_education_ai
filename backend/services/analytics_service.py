from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models.analytics import LearningProgress, PerformanceMetrics
from models.assignment import Submission, Assignment
from models.course import Course, Chapter, Lesson
from models.user import User

class AnalyticsService:
    def track_learning_progress(
        self,
        db: Session,
        user_id: int,
        course_id: int,
        chapter_id: Optional[int] = None,
        lesson_id: Optional[int] = None,
        time_spent: int = 0
    ) -> LearningProgress:
        """Track user's learning progress"""
        # Find or 创建 progress 记录
        query = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.course_id == course_id
        )

        if lesson_id:
            query = query.filter(LearningProgress.lesson_id == lesson_id)
        elif chapter_id:
            query = query.filter(
                LearningProgress.chapter_id == chapter_id,
                LearningProgress.lesson_id.is_(None)
            )
        else:
            query = query.filter(
                LearningProgress.chapter_id.is_(None),
                LearningProgress.lesson_id.is_(None)
            )

        progress = query.first()

        if not progress:
            progress = LearningProgress(
                user_id=user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                lesson_id=lesson_id,
                progress_percentage=0,
                time_spent_minutes=0
            )
            db.add(progress)

        # 更新 progress
        progress.time_spent_minutes += time_spent
        progress.last_accessed = datetime.utcnow()

        # Calculate progress percentage if lesson
        if lesson_id:
            progress.progress_percentage = 100  # Lesson viewed = 100%

            # 更新 chapter progress
            self._update_chapter_progress(db, user_id, course_id, chapter_id)

            # 更新 course progress
            self._update_course_progress(db, user_id, course_id)

        db.commit()
        db.refresh(progress)

        return progress

    def _update_chapter_progress(
        self,
        db: Session,
        user_id: int,
        course_id: int,
        chapter_id: int
    ):
        """Update chapter progress based on lesson completion"""
        # 获取 全部 lessons in chapter
        total_lessons = db.query(Lesson).filter(
            Lesson.chapter_id == chapter_id
        ).count()

        if total_lessons == 0:
            return

        # 获取 已完成 lessons
        completed_lessons = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.chapter_id == chapter_id,
            LearningProgress.lesson_id.isnot(None),
            LearningProgress.progress_percentage >= 100
        ).count()

        # 更新 or 创建 chapter progress
        chapter_progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.course_id == course_id,
            LearningProgress.chapter_id == chapter_id,
            LearningProgress.lesson_id.is_(None)
        ).first()

        if not chapter_progress:
            chapter_progress = LearningProgress(
                user_id=user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                progress_percentage=0
            )
            db.add(chapter_progress)

        chapter_progress.progress_percentage = (completed_lessons / total_lessons) * 100
        chapter_progress.last_accessed = datetime.utcnow()

    def _update_course_progress(
        self,
        db: Session,
        user_id: int,
        course_id: int
    ):
        """Update course progress based on chapter completion"""
        # 获取 全部 chapters in course
        total_chapters = db.query(Chapter).filter(
            Chapter.course_id == course_id
        ).count()

        if total_chapters == 0:
            return

        # 获取 平均 chapter progress
        avg_progress = db.query(func.avg(LearningProgress.progress_percentage)).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.course_id == course_id,
            LearningProgress.chapter_id.isnot(None),
            LearningProgress.lesson_id.is_(None)
        ).scalar() or 0

        # 更新 or 创建 course progress
        course_progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.course_id == course_id,
            LearningProgress.chapter_id.is_(None),
            LearningProgress.lesson_id.is_(None)
        ).first()

        if not course_progress:
            course_progress = LearningProgress(
                user_id=user_id,
                course_id=course_id,
                progress_percentage=0
            )
            db.add(course_progress)

        course_progress.progress_percentage = avg_progress
        course_progress.last_accessed = datetime.utcnow()

    def record_performance_metric(
        self,
        db: Session,
        user_id: int,
        course_id: int,
        metric_type: str,
        value: float,
        metadata: Optional[Dict] = None
    ) -> PerformanceMetrics:
        """Record a performance metric"""
        metric = PerformanceMetrics(
            user_id=user_id,
            course_id=course_id,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {},
            recorded_at=datetime.utcnow()
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    def get_student_analytics(
        self,
        db: Session,
        student_id: int,
        course_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a student"""
        analytics = {
            "student_id": student_id,
            "courses": [],
            "overall_performance": {}
        }

        # 获取 courses
        query = db.query(Course).join(Course.users).filter(
            Course.users.any(id=student_id)
        )

        if course_id:
            query = query.filter(Course.id == course_id)

        courses = query.all()

        total_score = 0
        total_assignments = 0

        for course in courses:
            course_data = {
                "course_id": course.id,
                "course_title": course.title,
                "progress": 0,
                "time_spent": 0,
                "assignments": {
                    "total": 0,
                    "completed": 0,
                    "average_score": 0
                },
                "recent_activity": []
            }

            # 获取 course progress
            progress = db.query(LearningProgress).filter(
                LearningProgress.user_id == student_id,
                LearningProgress.course_id == course.id,
                LearningProgress.chapter_id.is_(None)
            ).first()

            if progress:
                course_data["progress"] = progress.progress_percentage
                course_data["time_spent"] = progress.time_spent_minutes

            # 获取 作业 performance
            submissions = db.query(Submission).join(Assignment).filter(
                Assignment.course_id == course.id,
                Submission.student_id == student_id
            ).all()

            course_data["assignments"]["total"] = len(submissions)
            course_data["assignments"]["completed"] = len([s for s in submissions if s.status == "graded"])

            if submissions:
                scores = [s.score for s in submissions if s.score is not None]
                if scores:
                    course_data["assignments"]["average_score"] = sum(scores) / len(scores)
                    total_score += sum(scores)
                    total_assignments += len(scores)

            # 获取 recent activity
            recent_progress = db.query(LearningProgress).filter(
                LearningProgress.user_id == student_id,
                LearningProgress.course_id == course.id,
                LearningProgress.last_accessed >= datetime.utcnow() - timedelta(days=7)
            ).order_by(LearningProgress.last_accessed.desc()).limit(5).all()

            for p in recent_progress:
                activity = {
                    "type": "learning",
                    "timestamp": p.last_accessed.isoformat() if p.last_accessed else None,
                    "description": f"Studied {'lesson' if p.lesson_id else 'chapter' if p.chapter_id else 'course'}"
                }
                course_data["recent_activity"].append(activity)

            analytics["courses"].append(course_data)

        # Overall performance
        if total_assignments > 0:
            analytics["overall_performance"]["average_score"] = total_score / total_assignments

        analytics["overall_performance"]["total_courses"] = len(courses)
        analytics["overall_performance"]["active_courses"] = len([
            c for c in analytics["courses"] if c["progress"] > 0
        ])

        return analytics

    def get_course_analytics(
        self,
        db: Session,
        course_id: int
    ) -> Dict[str, Any]:
        """Get analytics for a course"""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return None

        analytics = {
            "course_id": course_id,
            "course_title": course.title,
            "total_students": 0,
            "active_students": 0,
            "average_progress": 0,
            "assignment_stats": {},
            "chapter_stats": []
        }

        # 获取 enrolled students
        students = db.query(User).join(User.courses).filter(
            User.courses.any(id=course_id)
        ).all()

        analytics["total_students"] = len(students)

        # 获取 激活 students (accessed in 最后一个 7 days)
        active_students = db.query(LearningProgress.user_id).filter(
            LearningProgress.course_id == course_id,
            LearningProgress.last_accessed >= datetime.utcnow() - timedelta(days=7)
        ).distinct().count()

        analytics["active_students"] = active_students

        # 平均 progress
        avg_progress = db.query(func.avg(LearningProgress.progress_percentage)).filter(
            LearningProgress.course_id == course_id,
            LearningProgress.chapter_id.is_(None),
            LearningProgress.lesson_id.is_(None)
        ).scalar() or 0

        analytics["average_progress"] = avg_progress

        # 作业 statistics
        assignments = db.query(Assignment).filter(
            Assignment.course_id == course_id
        ).all()

        total_submissions = 0
        total_score = 0
        graded_submissions = 0

        for assignment in assignments:
            submissions = db.query(Submission).filter(
                Submission.assignment_id == assignment.id
            ).all()

            total_submissions += len(submissions)

            for submission in submissions:
                if submission.score is not None:
                    total_score += submission.score
                    graded_submissions += 1

        analytics["assignment_stats"] = {
            "total_assignments": len(assignments),
            "total_submissions": total_submissions,
            "average_score": total_score / graded_submissions if graded_submissions > 0 else 0,
            "submission_rate": total_submissions / (len(assignments) * len(students)) if assignments and students else 0
        }

        # Chapter statistics
        chapters = db.query(Chapter).filter(
            Chapter.course_id == course_id
        ).order_by(Chapter.order).all()

        for chapter in chapters:
            chapter_stat = {
                "chapter_id": chapter.id,
                "chapter_title": chapter.title,
                "average_progress": 0,
                "total_time_spent": 0
            }

            # 获取 chapter progress stats
            progress_stats = db.query(
                func.avg(LearningProgress.progress_percentage),
                func.sum(LearningProgress.time_spent_minutes)
            ).filter(
                LearningProgress.course_id == course_id,
                LearningProgress.chapter_id == chapter.id,
                LearningProgress.lesson_id.is_(None)
            ).first()

            if progress_stats[0]:
                chapter_stat["average_progress"] = progress_stats[0]
            if progress_stats[1]:
                chapter_stat["total_time_spent"] = progress_stats[1]

            analytics["chapter_stats"].append(chapter_stat)

        return analytics

analytics_service = AnalyticsService()