from sqlalchemy import Column, String, Text, Integer, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from models.base import BaseModel
class Course(BaseModel):
    __tablename__ = "courses"

    title = Column(String, nullable=False)
    description = Column(Text)
    subject = Column(String, nullable=False)
    grade_level = Column(String)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    cover_image = Column(String)
    tags = Column(JSON, default=list)

    # 关系
    teacher = relationship("User", back_populates="created_courses", foreign_keys=[teacher_id])
    users = relationship("User", secondary="user_courses", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course {self.title}>"

class Chapter(BaseModel):
    __tablename__ = "chapters"

    title = Column(String, nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))

    # 关系
    course = relationship("Course", back_populates="chapters")
    lessons = relationship("Lesson", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter {self.title}>"

class Lesson(BaseModel):
    __tablename__ = "lessons"

    title = Column(String, nullable=False)
    content = Column(Text)
    order = Column(Integer, nullable=False)
    duration_minutes = Column(Integer)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    knowledge_points = Column(JSON, default=list)
    resources = Column(JSON, default=list)

    # 关系
    chapter = relationship("Chapter", back_populates="lessons")

    def __repr__(self):
        return f"<Lesson {self.title}>"