# Teacher API module
from .course_design import router as course_design_router
from .assignments import router as assignments_router
from .students import router as students_router

__all__ = ["course_design_router", "assignments_router", "students_router"]