from typing import Any, Optional, Dict, List, Union
from fastapi.responses import JSONResponse
from fastapi import Request
from datetime import datetime
import uuid

from core.config import settings


class StandardResponse:
    """标准化API响应格式"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        meta: Optional[Dict] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建标准化成功响应"""

        # 基础响应结构
        content = {
            "success": True,
            "code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 如果可用，添加请求ID
        if request and hasattr(request.state, "request_id"):
            content["request_id"] = request.state.request_id

        # 如果提供，添加数据
        if data is not None:
            content["data"] = data

        # 如果提供，添加元数据
        if meta:
            content["meta"] = meta

        return JSONResponse(
            content=content,
            status_code=status_code
        )

    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        status_code: int = 400,
        errors: Optional[Union[Dict, List]] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建标准化错误响应"""

        content = {
            "success": False,
            "code": status_code,
            "message": message,
            "error": {
                "code": code,
                "message": message
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 如果可用，添加请求ID
        if request and hasattr(request.state, "request_id"):
            content["request_id"] = request.state.request_id
            content["error"]["request_id"] = request.state.request_id

        # 如果提供并且不在生产环境，添加详细错误
        if errors:
            if settings.environment != "production":
                content["error"]["details"] = errors
            else:
                # 在生产环境，仅显示字段名称而不显示详情
                if isinstance(errors, dict):
                    content["error"]["fields"] = list(errors.keys())

        return JSONResponse(
            content=content,
            status_code=status_code
        )

    @staticmethod
    def validation_error(
        errors: Union[Dict, List],
        message: str = "验证失败",
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建验证错误响应"""

        # 格式化验证错误
        formatted_errors = {}

        if isinstance(errors, list):
            # Pydantic验证错误
            for error in errors:
                field = ".".join(str(loc) for loc in error.get("loc", []))
                formatted_errors[field] = error.get("msg", "无效值")
        elif isinstance(errors, dict):
            formatted_errors = errors

        return StandardResponse.error(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            errors=formatted_errors,
            request=request
        )

    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "Success",
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建分页响应"""

        # 计算分页元数据
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        meta = {
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

        return StandardResponse.success(
            data=data,
            message=message,
            meta=meta,
            request=request
        )

    @staticmethod
    def created(
        data: Any = None,
        message: str = "资源创建成功",
        location: Optional[str] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建资源已创建响应"""

        response = StandardResponse.success(
            data=data,
            message=message,
            status_code=201,
            request=request
        )

        # 如果提供，添加Location头部
        if location:
            response.headers["Location"] = location

        return response

    @staticmethod
    def no_content(message: str = "成功") -> JSONResponse:
        """创建无内容响应"""

        return JSONResponse(
            content=None,
            status_code=204
        )

    @staticmethod
    def unauthorized(
        message: str = "需要认证",
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建未授权响应"""

        response = StandardResponse.error(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            request=request
        )

        # 添加WWW-Authenticate头部
        response.headers["WWW-Authenticate"] = "Bearer"

        return response

    @staticmethod
    def forbidden(
        message: str = "权限不足",
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建禁止访问响应"""

        return StandardResponse.error(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            request=request
        )

    @staticmethod
    def not_found(
        resource: str = "资源",
        request: Optional[Request] = None
    ) -> JSONResponse:
        """创建未找到响应"""

        return StandardResponse.error(
            message=f"{resource}未找到",
            code="NOT_FOUND",
            status_code=404,
            request=request
        )


# 向后兼容
def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> JSONResponse:
    """创建标准化成功响应（已弃用）"""
    return StandardResponse.success(data=data, message=message, status_code=status_code)


def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[Dict] = None
) -> JSONResponse:
    """创建标准化错误响应（已弃用）"""
    return StandardResponse.error(message=message, status_code=status_code, errors=errors)


def validation_error_response(errors: Dict) -> JSONResponse:
    """创建验证错误响应（已弃用）"""
    return StandardResponse.validation_error(errors=errors)