
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from models.course import Course
from models.user import User

class CourseService:
    """课程管理服务"""

    def create_course(self, db: Session, teacher_id: int, title: str,
                     description: str, subject: str, grade_level: str) -> Course:
        """创建新课程"""
        course = Course(
            title=title,
            description=description,
            subject=subject,
            grade_level=grade_level,
            teacher_id=teacher_id,
            status="draft",
            created_at=datetime.utcnow()
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    def get_course(self, db: Session, course_id: int) -> Optional[Course]:
        """获取课程详情"""
        return db.query(Course).filter(Course.id == course_id).first()

    def update_course(self, db: Session, course_id: int, **kwargs) -> Optional[Course]:
        """更新课程信息"""
        course = self.get_course(db, course_id)
        if course:
            for key, value in kwargs.items():
                if hasattr(course, key):
                    setattr(course, key, value)
            course.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(course)
        return course

    def delete_course(self, db: Session, course_id: int) -> bool:
        """删除课程"""
        course = self.get_course(db, course_id)
        if course:
            db.delete(course)
            db.commit()
            return True
        return False

    def list_courses(self, db: Session, skip: int = 0, limit: int = 20) -> List[Course]:
        """获取课程列表"""
        return db.query(Course).offset(skip).limit(limit).all()

course_service = CourseService()
