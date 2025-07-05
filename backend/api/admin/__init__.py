from .users import router as users_router
from .courses import router as courses_router
from .system import router as system_router
from .analytics import router as analytics_router
__all__ = ['users_router', 'courses_router', 'system_router', 'analytics_router']