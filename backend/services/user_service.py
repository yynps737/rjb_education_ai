from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from services.base import BaseService
from models.user import User, UserRole
from utils.auth import get_password_hash

class UserService(BaseService[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    def create_user(
        self,
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.STUDENT
    ) -> User:
        """创建新用户（密码已加密）"""
        hashed_password = get_password_hash(password)
        return self.create(
            db,
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role
        )

    def search_users(
        self,
        db: Session,
        query: str,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """根据用户名、邮箱或全名搜索用户"""
        search = f"%{query}%"
        q = db.query(User).filter(
            or_(
                User.username.ilike(search),
                User.email.ilike(search),
                User.full_name.ilike(search)
            )
        )

        if role:
            q = q.filter(User.role == role)

        return q.offset(skip).limit(limit).all()

    def get_teachers(self, db: Session) -> List[User]:
        """Get all teachers"""
        return db.query(User).filter(User.role == UserRole.TEACHER).all()

    def get_students_in_course(self, db: Session, course_id: int) -> List[User]:
        """Get all students enrolled in a course"""
        return db.query(User).join(User.courses).filter(
            User.role == UserRole.STUDENT,
            User.courses.any(id=course_id)
        ).all()

    def toggle_user_active(self, db: Session, user_id: int) -> Optional[User]:
        """Toggle user active status"""
        user = self.get(db, user_id)
        if user:
            user.is_active = not user.is_active
            db.commit()
            db.refresh(user)
        return user

user_service = UserService()