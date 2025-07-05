from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.pool import NullPool
from datetime import datetime
from core.config import settings
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = settings.database_url

# 配置生产就绪的引擎设置
engine_args = {
    "pool_size": settings.db_pool_size,
    "max_overflow": settings.db_pool_max_overflow,
    "pool_pre_ping": True,
    # 使用前验证连接
    "pool_recycle": 3600,
    # 1小时后回收连接
}

# 处理不同数据库的特定设置
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # 为SQLite启用外键约束
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL特定配置
    if settings.environment == "test":
        # 测试环境使用NullPool
        engine = create_engine(DATABASE_URL, poolclass=NullPool, echo=True)
    else:
        # 生产环境配置
        engine_args.update({
            "echo": settings.environment == "development",
            # 开发环境打印SQL
            "echo_pool": settings.environment == "development",
            "connect_args": {
                "connect_timeout": 10,
                "options": "-c timezone=utc"
            }
        })
        engine = create_engine(DATABASE_URL, **engine_args)
    logger.info("使用PostgreSQL数据库")
else:
    # 其他数据库
    engine = create_engine(DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()
Base = declarative_base(metadata=metadata)

class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    # 软删除
    def to_dict(self):
        """将模型转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def soft_delete(self):
        """软删除记录"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()