"""
自定义异常类和错误处理
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
import logging

from core.config import settings
logger = logging.getLogger(__name__)


class AppException(Exception):
    """基础应用程序异常"""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """验证错误异常"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field, **(details or {})}
        )


class AuthenticationException(AppException):
    """认证错误异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            status_code=401
        )


class AuthorizationException(AppException):
    """授权错误异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=403
        )


class ResourceNotFoundException(AppException):
    """资源未找到异常"""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource}未找到",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class BusinessLogicException(AppException):
    """业务逻辑违规异常"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="BUSINESS_LOGIC_ERROR",
            status_code=400,
            details=details
        )


class ExternalServiceException(AppException):
    """外部服务错误异常"""

    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"外部服务错误: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details={"service": service, **(details or {})}
        )


class RateLimitException(AppException):
    """速率限制超出异常"""

    def __init__(self, retry_after: int):
        super().__init__(
            message="速率限制超出",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )


def create_error_response(
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """创建标准化错误响应"""

    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id
        }
    }

    if details and settings.environment != "production":
        response["error"]["details"] = details

    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理自定义应用程序异常"""

    request_id = getattr(request.state, "request_id", "unknown")

    # 记录异常
    logger.warning(
        f"应用程序异常: {exc.code}",
        extra={
            "request_id": request_id,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

    # 创建响应
    content = create_error_response(
        request_id=request_id,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理FastAPI HTTP异常"""

    request_id = getattr(request.state, "request_id", "unknown")

    # 将状态码映射到错误代码
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }

    code = error_codes.get(exc.status_code, "HTTP_ERROR")

    # 记录异常
    logger.warning(
        f"HTTP异常: {code}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )

    # 创建响应
    content = create_error_response(
        request_id=request_id,
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers
    )


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理数据库异常"""

    request_id = getattr(request.state, "request_id", "unknown")

    # 记录异常
    logger.error(
        f"数据库异常: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "message": str(exc)
        },
        exc_info=True
    )

    # 根据异常类型确定适当的响应
    if isinstance(exc, IntegrityError):
        message = "数据完整性违规"
        code = "DATA_INTEGRITY_ERROR"
        status_code = 400
    elif isinstance(exc, DataError):
        message = "无效的数据格式"
        code = "DATA_FORMAT_ERROR"
        status_code = 400
    elif isinstance(exc, OperationalError):
        message = "数据库操作失败"
        code = "DATABASE_ERROR"
        status_code = 503
    else:
        message = "发生数据库错误"
        code = "DATABASE_ERROR"
        status_code = 500

    # 创建响应（在生产环境中隐藏详情）
    details = {"error": str(exc)} if settings.environment != "production" else None

    content = create_error_response(
        request_id=request_id,
        code=code,
        message=message,
        status_code=status_code,
        details=details
    )

    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未处理的异常"""

    request_id = getattr(request.state, "request_id", "unknown")

    # 记录异常
    logger.error(
        f"未处理的异常: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "message": str(exc)
        },
        exc_info=True
    )

    # 创建通用响应
    if settings.environment == "production":
        message = "发生内部错误"
        details = None
    else:
        message = f"内部错误: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "message": str(exc)
        }

    content = create_error_response(
        request_id=request_id,
        code="INTERNAL_ERROR",
        message=message,
        status_code=500,
        details=details
    )

    return JSONResponse(
        status_code=500,
        content=content
    )


def register_exception_handlers(app):
    """向FastAPI应用注册所有异常处理器"""

    # 自定义异常
    app.add_exception_handler(AppException, app_exception_handler)

    # FastAPI异常
    app.add_exception_handler(HTTPException, http_exception_handler)

    # 数据库异常
    app.add_exception_handler(IntegrityError, database_exception_handler)
    app.add_exception_handler(DataError, database_exception_handler)
    app.add_exception_handler(OperationalError, database_exception_handler)

    # 全局处理器
    app.add_exception_handler(Exception, global_exception_handler)