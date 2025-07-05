from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Query
import math

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

def paginate(
    query: Query,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """Paginate a SQLAlchemy query"""
    # Ensure positive values
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    # 最大 100 items per 页
    total = query.count()
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size

    items = query.offset(offset).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }