from .courses import router as courses_router
from .assignments import router as assignments_router
from .learning import router as learning_router
from .profile import router as profile_router
__all__ = ['courses_router', 'assignments_router', 'learning_router', 'profile_router']