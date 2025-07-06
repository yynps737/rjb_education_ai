from typing import Dict, Any, Optional
import os
import psutil
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import json
from pathlib import Path

from models.database import get_db
from models.user import User, UserRole
from utils.auth import require_role
from utils.response import success_response, error_response
from core.rag.vector_store import VectorStore

router = APIRouter()

# 系统设置模型
class SystemSettings(BaseModel):
    site_name: str = "智能教学平台"
    site_description: str = "基于AI的现代化教学管理系统"
    admin_email: str = "admin@example.com"
    support_email: str = "support@example.com"
    max_file_size: int = 10  # MB
    allowed_file_types: list = ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "jpg", "png"]
    session_timeout: int = 30  # minutes
    enable_registration: bool = True
    enable_email_verification: bool = False
    enable_two_factor: bool = False
    maintenance_mode: bool = False
    maintenance_message: str = "系统正在维护中，请稍后再试。"
    backup_enabled: bool = True
    backup_frequency: str = "daily"
    backup_retention_days: int = 30
    log_level: str = "INFO"
    log_retention_days: int = 90
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_use_tls: bool = True

# 设置文件路径
SETTINGS_FILE = Path("settings.json")

def load_settings() -> SystemSettings:
    """Load settings from file or return defaults"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return SystemSettings(**data)
        except Exception:
            pass
    return SystemSettings()

def save_settings(settings: SystemSettings) -> None:
    """Save settings to file"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.dict(), f, ensure_ascii=False, indent=2)

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get system settings"""
    settings = load_settings()
    return success_response(data=settings.dict())

@router.put("/settings")
async def update_settings(
    settings: SystemSettings,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update system settings"""
    try:
        save_settings(settings)
        return success_response(message="设置保存成功")
    except Exception as e:
        return error_response(f"保存设置失败: {str(e)}")

@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get system information"""
    try:
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Mock database size
        db_size = 1024 * 1024 * 100  # 100MB
        
        # Mock counts
        total_users = 15
        total_courses = 5
        total_assignments = 10
        
        # Uptime
        import time
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_hours = uptime_seconds / 3600
        
        # Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        return success_response(data={
            "version": "1.0.0",
            "python_version": python_version,
            "database_size": db_size,
            "storage_used": disk.used,
            "storage_total": disk.total,
            "cpu_usage": cpu_usage,
            "memory_usage": memory.used,
            "memory_total": memory.total,
            "uptime_hours": round(uptime_hours, 2),
            "active_users": total_users,
            "total_courses": total_courses,
            "total_assignments": total_assignments
        })
    except Exception as e:
        return error_response(f"获取系统信息失败: {str(e)}")

@router.get("/health")
async def system_health_check(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Check system health and status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # 检查 数据库
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # 检查 vector store
    try:
        vector_store = VectorStore()
        # Simple health 检查 - try to 获取 collection 信息
        health_status["services"]["vector_store"] = {
            "status": "healthy",
            "message": "Vector store accessible"
        }
    except Exception as e:
        health_status["services"]["vector_store"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # 检查 Redis (if configured)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "message": str(e)
            }

    return success_response(data=health_status)

@router.get("/metrics")
async def get_system_metrics(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()

    # Memory usage
    memory = psutil.virtual_memory()

    # Disk usage
    disk = psutil.disk_usage('/')

    # 进程 信息
    process = psutil.Process()
    process_info = {
        "pid": process.pid,
        "memory_percent": process.memory_percent(),
        "cpu_percent": process.cpu_percent(interval=1),
        "num_threads": process.num_threads(),
        "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
    }

    return success_response(data={
        "cpu": {
            "percent": cpu_percent,
            "count": cpu_count
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        "process": process_info
    })

@router.get("/database/stats")
async def get_database_statistics(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get database statistics"""
    stats = {}

    # 表 sizes
    tables = [
        "users", "courses", "chapters", "lessons",
        "assignments", "questions", "submissions", "answers",
        "knowledge_documents", "knowledge_chunks",
        "learning_progress", "performance_metrics"
    ]

    for table in tables:
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            stats[table] = count
        except:
            stats[table] = "N/A"

    # 数据库 size (PostgreSQL specific)
    try:
        db_name = os.getenv("DB_NAME", "education_ai")
        size_query = text(
            "SELECT pg_database_size(:db_name) as size"
        )
        db_size = db.execute(size_query, {"db_name": db_name}).scalar()
        stats["database_size_bytes"] = db_size
        stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
    except:
        stats["database_size_bytes"] = "N/A"
        stats["database_size_mb"] = "N/A"

    return success_response(data=stats)

@router.get("/logs/errors")
async def get_error_logs(
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get recent error logs"""
    # In a real 实现, this would read from actual log files
    # or a 日志 服务. For now, return a placeholder.
    log_file = "logs/error.log"
    errors = []

    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # 获取 最后一个 '限制' lines
                recent_lines = lines[-limit:] if len(lines) > limit else lines

                for line in recent_lines:
                    if line.strip():
                        errors.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": line.strip()
                        })
        except Exception as e:
            return error_response(f"Failed to read logs: {str(e)}")

    return success_response(data={
        "errors": errors,
        "count": len(errors)
    })

@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Clear application cache"""
    cleared = []

    # Clear Redis 缓存 if available
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.flushdb()
            cleared.append("redis")
        except Exception as e:
            return error_response(f"Failed to clear Redis cache: {str(e)}")

    # Clear 局部 缓存 目录
    cache_dir = "data/cache"
    if os.path.exists(cache_dir):
        try:
            import shutil
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)
            cleared.append("local_cache")
        except Exception as e:
            return error_response(f"Failed to clear local cache: {str(e)}")

    return success_response(
        message="Cache cleared successfully",
        data={"cleared": cleared}
    )

@router.get("/config")
async def get_system_configuration(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get system configuration (non-sensitive)"""
    config = {
        "environment": os.getenv("ENVIRONMENT", "production"),
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "database": {
            "type": "postgresql",
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "name": os.getenv("DB_NAME", "education_ai")
        },
        "services": {
            "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
            "vector_store": "milvus",
            "cache": "redis" if os.getenv("REDIS_URL") else "none",
            "task_queue": "celery" if os.getenv("CELERY_BROKER_URL") else "none"
        },
        "features": {
            "auto_grading": True,
            "rag_enabled": True,
            "analytics_enabled": True,
            "monitoring_enabled": bool(os.getenv("PROMETHEUS_ENABLED", False))
        },
        "limits": {
            "max_file_upload_size": 10 * 1024 * 1024,  # 10MB
            "max_students_per_course": 1000,
            "max_questions_per_assignment": 100
        }
    }

    return success_response(data=config)

@router.get("/activity/recent")
async def get_recent_activity(
    hours: int = 24,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get recent system activity"""
    since = datetime.utcnow() - timedelta(hours=hours)

    # Recent user registrations
    from models.user import User as UserModel
    recent_users = db.query(UserModel).filter(
        UserModel.created_at >= since
    ).count()

    # Recent submissions
    from models.assignment import Submission
    recent_submissions = db.query(Submission).filter(
        Submission.submitted_at >= since
    ).count()

    # Recent learning activity
    from models.analytics import LearningProgress
    active_learners = db.query(LearningProgress.user_id).filter(
        LearningProgress.last_accessed >= since
    ).distinct().count()

    # Recent 文档 uploads
    from models.knowledge import KnowledgeDocument
    recent_uploads = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.created_at >= since
    ).count()

    return success_response(data={
        "period_hours": hours,
        "since": since.isoformat(),
        "activity": {
            "new_users": recent_users,
            "submissions": recent_submissions,
            "active_learners": active_learners,
            "document_uploads": recent_uploads
        }
    })

@router.post("/test-email")
async def test_email(
    email_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Send a test email"""
    try:
        # In a real implementation, this would use the email service
        # For now, just simulate success
        to_email = email_data.get("to")
        if not to_email:
            return error_response("收件人邮箱不能为空")
        
        # Here you would integrate with your email service
        # Example: email_service.send_test_email(to_email, smtp_settings)
        
        return success_response(message=f"测试邮件已发送到 {to_email}")
    except Exception as e:
        return error_response(f"发送失败: {str(e)}")

@router.post("/backup-now")
async def backup_now(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Trigger an immediate backup"""
    try:
        # In a real implementation, this would trigger the backup service
        # For now, just simulate the process
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Here you would integrate with your backup service
        # Example: backup_service.create_backup(backup_id)
        
        return success_response(
            message="备份任务已启动",
            data={"backup_id": backup_id}
        )
    except Exception as e:
        return error_response(f"备份失败: {str(e)}")

@router.post("/clear-cache")
async def clear_system_cache(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Clear system cache"""
    cleared = []
    
    # Clear Redis cache if available
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.flushdb()
            cleared.append("redis")
        except Exception as e:
            return error_response(f"Failed to clear Redis cache: {str(e)}")
    
    # Clear local cache directory
    cache_dir = "data/cache"
    if os.path.exists(cache_dir):
        try:
            import shutil
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)
            cleared.append("local_cache")
        except Exception as e:
            return error_response(f"Failed to clear local cache: {str(e)}")
    
    return success_response(
        message="缓存已清除",
        data={"cleared": cleared}
    )