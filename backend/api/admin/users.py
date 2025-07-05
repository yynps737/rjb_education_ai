from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from models.database import get_db
from models.user import User, UserRole
from utils.auth import require_role, get_password_hash
from utils.response import success_response, error_response
from utils.pagination import paginate
from services.user_service import user_service

router = APIRouter()

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

@router.get("", response_model=List[UserResponse])
async def get_users(
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get all users with filtering and pagination"""
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if search:
        users = user_service.search_users(db, search, role, (page-1)*page_size, page_size)
        total = len(users)  # Approximate
    else:
        result = paginate(query, page, page_size)
        users = result["items"]
        total = result["total"]

    response_users = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]

    return response_users

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new user"""
    # 检查 if user exists
    if user_service.get_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    if user_service.get_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    # 创建 user
    user = user_service.create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role
    )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get user details"""
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )

@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update user details"""
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from changing their own role
    if user_id == current_user.id and user_data.role and user_data.role != current_user.role:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role"
        )

    # 更新 fields
    update_data = {}
    if user_data.full_name is not None:
        update_data["full_name"] = user_data.full_name

    if user_data.email is not None and user_data.email != user.email:
        # 检查 if 邮箱 exists
        if user_service.get_by_email(db, user_data.email):
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data["email"] = user_data.email

    if user_data.role is not None:
        update_data["role"] = user_data.role

    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active

    user = user_service.update(db, user, **update_data)

    return success_response(
        message="User updated successfully",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a user (soft delete by deactivating)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Soft 删除
    user.is_active = False
    db.commit()

    return success_response(message="User deactivated successfully")

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=8),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Reset user password"""
    user = user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 更新 密码
    user.hashed_password = get_password_hash(new_password)
    db.commit()

    return success_response(message="Password reset successfully")

@router.get("/stats/summary")
async def get_user_statistics(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get user statistics summary"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    role_counts = {}
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        role_counts[role.value] = count

    # Recent registrations (最后一个 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_registrations = db.query(User).filter(
        User.created_at >= week_ago
    ).count()

    return success_response(data={
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "users_by_role": role_counts,
        "recent_registrations": recent_registrations
    })