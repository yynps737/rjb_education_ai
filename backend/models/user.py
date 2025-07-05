from sqlalchemy import Column, String, Boolean, Enum, Integer, ForeignKey, Table, DateTime, Index, CheckConstraint
from sqlalchemy.orm import relationship
import enum
from models.base import BaseModel, Base
class UserRole(enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

user_courses = Table(
    'user_courses',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        # 为基于角色的查询创建组合索引        Index('idx_user_role_active', 'role', 'is_active'),
        # 邮箱格式的检查约束（基本）        CheckConstraint("email LIKE '%@%.%'", name='check_email_format'),
    )

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)

    # 关系
    courses = relationship("Course", secondary=user_courses, back_populates="users")
    created_courses = relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    submissions = relationship("Submission", back_populates="student")
    learning_progress = relationship("LearningProgress", back_populates="user")

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"