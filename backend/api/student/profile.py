from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import os
from pathlib import Path

from models.database import get_db
from models.user import User, UserRole
from utils.auth import get_current_active_user, require_role, get_password_hash, verify_password
from utils.response import success_response, error_response
from utils.validators import validate_password, sanitize_filename
from services.analytics_service import analytics_service

router = APIRouter()

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(require_role([UserRole.STUDENT]))
):
    """Get current student profile"""
    return ProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at.isoformat()
    )

@router.put("/me")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Update student profile"""
    if profile_data.full_name:
        current_user.full_name = profile_data.full_name

    if profile_data.email and profile_data.email != current_user.email:
        # 检查 if 邮箱 already exists
        existing = db.query(User).filter(
            User.email == profile_data.email,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        current_user.email = profile_data.email

    db.commit()
    db.refresh(current_user)

    return success_response(
        message="Profile updated successfully",
        data=ProfileResponse.from_orm(current_user)
    )

@router.post("/me/password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Change password"""
    # 验证 当前 密码
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    # 校验 new 密码
    is_valid, error_msg = validate_password(password_data.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # 更新 密码
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return success_response(message="Password changed successfully")

@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Upload profile avatar"""
    # 校验 文件 type
    allowed_types = ['.jpg', '.jpeg', '.png', '.gif']
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {allowed_types}"
        )

    # 校验 文件 size (最大 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5MB"
        )

    # 保存 文件
    avatar_dir = Path("static/avatars")
    avatar_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{current_user.id}_{sanitize_filename(file.filename)}"
    file_path = avatar_dir / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    # 更新 user 头像 链接
    current_user.avatar_url = f"/static/avatars/{filename}"
    db.commit()

    return success_response(
        message="Avatar uploaded successfully",
        data={"avatar_url": current_user.avatar_url}
    )

@router.get("/me/stats")
async def get_learning_stats(
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get overall learning statistics"""
    stats = analytics_service.get_student_analytics(db, current_user.id)

    # Calculate additional stats
    total_time = sum(
        course.get("time_spent", 0)
        for course in stats.get("courses", [])
    )

    active_courses = len([
        c for c in stats.get("courses", [])
        if c.get("progress", 0) > 0
    ])

    completed_courses = len([
        c for c in stats.get("courses", [])
        if c.get("progress", 0) >= 100
    ])

    total_assignments = sum(
        c.get("assignments", {}).get("total", 0)
        for c in stats.get("courses", [])
    )

    completed_assignments = sum(
        c.get("assignments", {}).get("completed", 0)
        for c in stats.get("courses", [])
    )

    return success_response(data={
        "overview": {
            "total_courses": stats["overall_performance"].get("total_courses", 0),
            "active_courses": active_courses,
            "completed_courses": completed_courses,
            "total_learning_hours": round(total_time / 60, 1),
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "average_score": stats["overall_performance"].get("average_score", 0)
        },
        "recent_activity": [
            activity
            for course in stats.get("courses", [])
            for activity in course.get("recent_activity", [])
        ][:10]
        # 最后一个 10 activities
    })

@router.delete("/me")
async def delete_account(
    password: str = Body(..., embed=True),
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Delete student account (requires password confirmation)"""
    # 验证 密码
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )

    # Soft 删除 - just deactivate
    current_user.is_active = False
    db.commit()

    return success_response(message="Account deactivated successfully")