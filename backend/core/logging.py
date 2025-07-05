"""
集中式日志配置
"""
import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Any, Dict
import traceback

from core.config import settings

class JSONFormatter(logging.Formatter):
    """用于结构化日志的自定义JSON格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # 如果存在异常信息则添加
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)


class SensitiveDataFilter(logging.Filter):
    """用于从日志中移除敏感数据的过滤器"""

    SENSITIVE_FIELDS = [
        "password", "token", "secret", "api_key", "authorization",
        "credit_card", "ssn", "email", "phone"
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """从日志记录中过滤敏感数据"""
        # 在消息中屏蔽敏感数据
        message = record.getMessage()
        for field in self.SENSITIVE_FIELDS:
            if field in message.lower():
                # 简单屏蔽 - 可以改进
                message = message.replace(field, f"{field}=***MASKED***")

        record.msg = message
        return True


def setup_logging():
    """配置应用程序日志"""

    # 根据环境确定日志格式
    if settings.log_format == "json":
        formatter_class = "backend.core.logging.JSONFormatter"
    else:
        formatter_class = "logging.Formatter"

    # 日志配置字典
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "sensitive_data_filter": {
                "()": SensitiveDataFilter
            }
        },
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json" if settings.log_format == "json" else "default",
                "filters": ["sensitive_data_filter"]
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json" if settings.log_format == "json" else "default",
                "filters": ["sensitive_data_filter"]
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": "ERROR",
                "filters": ["sensitive_data_filter"]
            }
        },
        "loggers": {
            "backend": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING" if settings.environment == "production" else "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }

    # 如果不存在则创建日志目录
    import os
    os.makedirs("logs", exist_ok=True)

    # 应用配置
    logging.config.dictConfig(LOGGING_CONFIG)

    # 记录启动
    startup_logger = logging.getLogger(__name__)
    startup_logger.info(f"日志已配置。环境: {settings.environment}, 级别: {settings.log_level}")


class LoggerMixin:
    """用于向类添加日志记录器的Mixin"""

    @property
    def logger(self) -> logging.Logger:
        """获取类的日志记录器"""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器实例"""
    return logging.getLogger(name)


def log_performance(func):
    """记录函数性能的装饰器"""
    import functools
    import time

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"函数 {func.__name__} 完成",
                extra={
                    "extra_data": {
                        "function": func.__name__,
                        "duration": duration,
                        "status": "success"
                    }
                }
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                f"函数 {func.__name__} 失败",
                extra={
                    "extra_data": {
                        "function": func.__name__,
                        "duration": duration,
                        "status": "error",
                        "error": str(e)
                    }
                },
                exc_info=True
            )

            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"函数 {func.__name__} 完成",
                extra={
                    "extra_data": {
                        "function": func.__name__,
                        "duration": duration,
                        "status": "success"
                    }
                }
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                f"函数 {func.__name__} 失败",
                extra={
                    "extra_data": {
                        "function": func.__name__,
                        "duration": duration,
                        "status": "error",
                        "error": str(e)
                    }
                },
                exc_info=True
            )

            raise

    # 根据函数类型返回适当的包装器
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# 创建默认日志记录器实例
logger = get_logger(__name__)