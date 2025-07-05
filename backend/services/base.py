from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseService(Generic[ModelType]):
    """Base service class with common CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, **kwargs) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**kwargs)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        **kwargs
    ) -> ModelType:
        """Update a record"""
        for field, value in kwargs.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> bool:
        """Delete a record"""
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

    def count(self, db: Session) -> int:
        """Count total records"""
        return db.query(self.model).count()