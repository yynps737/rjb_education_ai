from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from utils.error_handler import AppError, not_found

from services.base import BaseService
from models.course import Course, Chapter, Lesson
from models.user import User, UserRole

class CourseService(BaseService[Course]):
    def __init__(self):
        super().__init__(Course)

    def create_course(
        self,
        db: Session,
        title: str,
        description: str,
        subject: str,
        teacher_id: int,
        grade_level: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Course:
        """创建新课程"""
        # 验证教师存在且具有教师角色
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()

        if not teacher:
            raise HTTPException(status_code=404, detail="教师未找到")

        return self.create(
            db,
            title=title,
            description=description,
            subject=subject,
            teacher_id=teacher_id,
            grade_level=grade_level,
            tags=tags or []
        )

    def get_course_with_chapters(self, db: Session, course_id: int) -> Optional[Course]:
        """获取包含所有章节和课程的课程"""
        return db.query(Course).options(
            joinedload(Course.chapters).joinedload(Chapter.lessons)
        ).filter(Course.id == course_id).first()

    def get_courses_by_teacher(self, db: Session, teacher_id: int) -> List[Course]:
        """获取教师的所有课程"""
        return db.query(Course).filter(Course.teacher_id == teacher_id).all()

    def get_courses_by_student(self, db: Session, student_id: int) -> List[Course]:
        """Get all courses a student is enrolled in"""
        return db.query(Course).join(Course.users).filter(
            Course.users.any(id=student_id)
        ).all()

    def enroll_student(self, db: Session, course_id: int, student_id: int) -> Course:
        """Enroll a student in a course"""
        course = self.get(db, course_id)
        if not course:
            raise not_found("课程")

        student = db.query(User).filter(
            User.id == student_id,
            User.role == UserRole.STUDENT
        ).first()

        if not student:
            raise not_found("学生")

        if student in course.users:
            raise AppError("ALREADY_ENROLLED")
            
        course.users.append(student)
        db.commit()
        db.refresh(course)

        return course

    def unenroll_student(self, db: Session, course_id: int, student_id: int) -> Course:
        """Unenroll a student from a course"""
        course = self.get(db, course_id)
        if not course:
            raise not_found("课程")

        student = db.query(User).filter(User.id == student_id).first()
        if student and student in course.users:
            course.users.remove(student)
            db.commit()
            db.refresh(course)

        return course

    def add_chapter(
        self,
        db: Session,
        course_id: int,
        title: str,
        description: Optional[str] = None,
        order: Optional[int] = None
    ) -> Chapter:
        """Add a chapter to a course"""
        course = self.get(db, course_id)
        if not course:
            raise not_found("课程")

        if order is None:
            # 获取 the 下一个 order number
            max_order = db.query(Chapter).filter(
                Chapter.course_id == course_id
            ).count()
            order = max_order + 1

        chapter = Chapter(
            title=title,
            description=description,
            order=order,
            course_id=course_id
        )

        db.add(chapter)
        db.commit()
        db.refresh(chapter)

        return chapter

    def search_courses(
        self,
        db: Session,
        query: Optional[str] = None,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Course]:
        """Search courses"""
        q = db.query(Course)

        if query:
            search = f"%{query}%"
            q = q.filter(
                (Course.title.ilike(search)) |
                (Course.description.ilike(search))
            )

        if subject:
            q = q.filter(Course.subject == subject)

        if grade_level:
            q = q.filter(Course.grade_level == grade_level)

        return q.offset(skip).limit(limit).all()

course_service = CourseService()