"""
统一错误处理工具
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 错误消息映射
ERROR_MESSAGES = {
    # 认证相关
    "USER_NOT_FOUND": "用户不存在",
    "INVALID_CREDENTIALS": "用户名或密码错误",
    "USER_EXISTS": "用户名已被注册",
    "EMAIL_EXISTS": "邮箱已被注册",
    "INVALID_TOKEN": "无效的认证令牌",
    "TOKEN_EXPIRED": "认证令牌已过期",
    "PERMISSION_DENIED": "权限不足",
    "NOT_AUTHENTICATED": "未认证，请先登录",
    "USER_INACTIVE": "账户已被禁用",
    
    # 资源相关
    "RESOURCE_NOT_FOUND": "请求的资源不存在",
    "COURSE_NOT_FOUND": "课程不存在",
    "ASSIGNMENT_NOT_FOUND": "作业不存在",
    "LESSON_NOT_FOUND": "课程章节不存在",
    "DOCUMENT_NOT_FOUND": "文档不存在",
    
    # 业务逻辑相关
    "NOT_ENROLLED": "您未注册此课程",
    "ALREADY_ENROLLED": "您已经注册了此课程",
    "ALREADY_SUBMITTED": "您已经提交过此作业",
    "SUBMISSION_DEADLINE": "作业提交已截止",
    "INVALID_ANSWER_FORMAT": "答案格式不正确",
    
    # 验证相关
    "INVALID_INPUT": "输入数据无效",
    "MISSING_FIELD": "缺少必填字段",
    "INVALID_FORMAT": "数据格式不正确",
    "FILE_TOO_LARGE": "文件大小超过限制",
    "INVALID_FILE_TYPE": "不支持的文件类型",
    
    # 系统相关
    "SERVER_ERROR": "服务器内部错误",
    "DATABASE_ERROR": "数据库操作失败",
    "EXTERNAL_SERVICE_ERROR": "外部服务调用失败",
    "RATE_LIMIT_EXCEEDED": "请求过于频繁，请稍后再试"
}

class AppError(HTTPException):
    """应用自定义错误类"""
    def __init__(
        self,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        # 获取错误消息
        message = ERROR_MESSAGES.get(error_code, error_code)
        if detail:
            message = f"{message}: {detail}"
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers=headers
        )
        self.error_code = error_code

def create_error_response(
    error_code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    detail: Optional[str] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """创建标准错误响应"""
    message = ERROR_MESSAGES.get(error_code, error_code)
    if detail:
        message = f"{message}: {detail}"
    
    error_data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    # 添加请求ID（如果有）
    if request and hasattr(request.state, "request_id"):
        error_data["error"]["request_id"] = request.state.request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )

# 便捷函数
def not_found(resource: str = "资源") -> AppError:
    """资源未找到错误"""
    return AppError(
        "RESOURCE_NOT_FOUND",
        status_code=status.HTTP_404_NOT_FOUND,
        detail=resource
    )

def permission_denied(detail: Optional[str] = None) -> AppError:
    """权限不足错误"""
    return AppError(
        "PERMISSION_DENIED",
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )

def validation_error(field: str, reason: str) -> AppError:
    """验证错误"""
    return AppError(
        "INVALID_INPUT",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"{field}: {reason}"
    )

def auth_error(error_code: str = "NOT_AUTHENTICATED") -> AppError:
    """认证错误"""
    return AppError(
        error_code,
        status_code=status.HTTP_401_UNAUTHORIZED
    )

def server_error(detail: Optional[str] = None) -> AppError:
    """服务器错误"""
    return AppError(
        "SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )