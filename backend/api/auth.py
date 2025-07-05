"""
修复认证API以匹配前端期望
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError

from models.database import get_db
from models.user import User, UserRole
from utils.auth import (
    create_access_token,
    create_refresh_token,
    create_tokens,
    verify_token,
    get_password_hash,
    verify_password,
    get_current_user
)
from utils.response import StandardResponse
from core.logging import get_logger

router = APIRouter(tags=["认证"])
logger = get_logger(__name__)

# 请求/响应模型
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# 通用登录端点
@router.post("/login",
    summary="用户登录",
    description="验证用户身份并获取访问/刷新令牌",
    response_model=TokenResponse,
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "code": 200,
                        "message": "登录成功",
                        "data": {
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "token_type": "bearer",
                            "expires_in": 1800,
                            "user": {
                                "id": 1,
                                "username": "john_doe",
                                "email": "john@example.com",
                                "full_name": "John Doe",
                                "role": "student"
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "无效凭据",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "code": 401,
                        "message": "用户名或密码错误"
                    }
                }
            }
        }
    }
)
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    所有用户类型的通用登录端点。

    - **username**: 用户名
    - **password**: 用户密码

    验证成功后返回访问令牌和刷新令牌。
    """
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        return StandardResponse.unauthorized("用户名或密码错误", request)

    if not user.is_active:
        return StandardResponse.forbidden("账户未激活", request)

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.commit()

    # 登录成功

    # 创建令牌
    access_token, refresh_token = create_tokens(user.id, user.username)

    return StandardResponse.success(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "avatar_url": user.avatar_url
            }
        },
        message="登录成功",
        request=request
    )

# 学生专用登录端点（向后兼容）
@router.post("/student/login")
async def student_login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """学生登录端点（已弃用 - 请使用 /login）"""
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        return StandardResponse.unauthorized("用户名或密码错误", request)

    if user.role != UserRole.STUDENT:
        return StandardResponse.forbidden("此登录仅限学生使用", request)

    if not user.is_active:
        return StandardResponse.forbidden("账户未激活", request)

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.commit()

    # 登录成功

    # 创建令牌
    access_token, refresh_token = create_tokens(user.id, user.username)

    return {
        "success": True,
        "token": access_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }

# 学生注册
@router.post("/student/register",
    response_model=UserResponse,
    summary="学生注册",
    description="注册新的学生账户",
    responses={
        200: {
            "description": "注册成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "full_name": "John Doe",
                        "role": "student",
                        "created_at": "2024-01-01T00:00:00"
                    }
                }
            }
        },
        400: {
            "description": "注册失败",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "code": 400,
                        "message": "用户名已被注册"
                    }
                }
            }
        }
    }
)
async def student_register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    注册新的学生账户。

    - **username**: 唯一用户名（3-20个字母数字字符）
    - **email**: 有效的电子邮件地址
    - **password**: 强密码（至少8个字符，包含大写、小写字母和数字）
    - **full_name**: 用户全名
    """
    # 检查用户名是否存在
    if db.query(User).filter(User.username == register_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")

    # 检查邮箱是否存在
    if db.query(User).filter(User.email == register_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建新用户
    user = User(
        username=register_data.username,
        email=register_data.email,
        full_name=register_data.full_name,
        hashed_password=get_password_hash(register_data.password),
        role=UserRole.STUDENT,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

# 获取学生信息
@router.get("/student/info", response_model=UserResponse)
async def get_student_info(current_user: User = Depends(get_current_user)):
    """获取当前学生信息"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="访问被拒绝")

    return current_user


# 刷新令牌端点
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """使用刷新令牌刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = verify_token(refresh_data.refresh_token, "refresh")
        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username or not user_id:
            raise HTTPException(status_code=401, detail="无效的刷新令牌")

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="用户未找到或未激活")

        # 创建新令牌
        access_token, new_refresh_token = create_tokens(user.id, user.username)

        return StandardResponse.success(
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 1800
            },
            message="令牌刷新成功",
            request=request
        )

    except JWTError as e:
        return StandardResponse.unauthorized("无效或过期的刷新令牌", request)
    except Exception as e:
        logger.error(f"令牌刷新错误: {e}")
        return StandardResponse.error("刷新令牌失败", status_code=500, request=request)

# 登出端点（前端兼容）
@router.post("/logout")
async def logout(request: Request):
    """登出端点 - 前端处理令牌移除"""
    # 在更完整的实现中，您可能需要：
    # 1. 将令牌添加到黑名单
    # 2. 清除任何服务器端会话
    # 3. 记录登出事件

    return StandardResponse.success(
        message="登出成功",
        request=request
    )