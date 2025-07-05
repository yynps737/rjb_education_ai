from contextlib import contextmanager
from models.base import SessionLocal, engine, Base
from . import *  # 导入全部模型

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI依赖项"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()