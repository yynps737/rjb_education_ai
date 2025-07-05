
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.learning import LearningProgress
from models.course import Course, Lesson

class ProgressService:
    """学习进度服务"""

    def update_progress(self, db: Session, student_id: int, lesson_id: int,
                       progress_percent: float, time_spent: int):
        """更新学习进度"""
        progress = db.query(LearningProgress).filter(
            LearningProgress.student_id == student_id,
            LearningProgress.lesson_id == lesson_id
        ).first()

        if progress:
            progress.progress_percent = progress_percent
            progress.time_spent += time_spent
            progress.last_accessed = datetime.utcnow()
            if progress_percent >= 100:
                progress.completed_at = datetime.utcnow()
        else:
            progress = LearningProgress(
                student_id=student_id,
                lesson_id=lesson_id,
                progress_percent=progress_percent,
                time_spent=time_spent,
                last_accessed=datetime.utcnow()
            )
            db.add(progress)

        db.commit()
        return progress

    def get_course_progress(self, db: Session, student_id: int, course_id: int) -> Dict:
        """获取课程进度"""
        # 获取课程的所有课时
        total_lessons = db.query(func.count(Lesson.id)).join(Course).filter(
            Course.id == course_id
        ).scalar()

        # 获取已完成的课时
        completed_lessons = db.query(func.count(LearningProgress.id)).join(Lesson).join(Course).filter(
            Course.id == course_id,
            LearningProgress.student_id == student_id,
            LearningProgress.progress_percent >= 100
        ).scalar()

        progress_percent = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        return {
            "course_id": course_id,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percent": progress_percent
        }

progress_service = ProgressService()
