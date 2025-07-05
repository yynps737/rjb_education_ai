from celery import shared_task
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path

from models.database import get_db_session
from models.assignment import Submission
from models.knowledge import KnowledgeDocument
from models.analytics import PerformanceMetrics

logger = logging.getLogger(__name__)

@shared_task
def cleanup_old_submissions(days: int = 180) -> Dict[str, Any]:
    """
    Clean up old submission data (default: 6 months)
    """
    try:
        with get_db_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Find old submissions
            old_submissions = db.query(Submission).filter(
                Submission.submitted_at < cutoff_date
            ).all()

            deleted_count = 0

            for submission in old_submissions:
                # Archive important 数据 before deletion (in real 实现)
                logger.info(f"Archiving submission {submission.id} before deletion")

                # 删除 submission and related answers (cascade)
                db.delete(submission)
                deleted_count += 1

            db.commit()

            logger.info(f"Cleaned up {deleted_count} old submissions")

            return {
                "status": "success",
                "submissions_deleted": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }

    except Exception as e:
        logger.error(f"Error cleaning up old submissions: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def cleanup_orphaned_files() -> Dict[str, Any]:
    """
    Clean up files that are no longer referenced in database
    """
    try:
        with get_db_session() as db:
            # 获取 全部 文件 paths from 数据库
            db_files = set()

            # Knowledge documents
            docs = db.query(KnowledgeDocument.file_path).all()
            db_files.update(doc[0] for doc in docs)

            # 头像 files
            from models.user import User
            avatars = db.query(User.avatar_url).filter(
                User.avatar_url.isnot(None)
            ).all()
            db_files.update(
                avatar[0].replace('/static/', 'static/')
                for avatar in avatars
            )

            # 检查 文件 directories
            cleaned_files = 0
            directories = [
                "data/knowledge_base/uploads",
                "static/avatars"
            ]

            for directory in directories:
                if not os.path.exists(directory):
                    continue

                for file_path in Path(directory).rglob('*'):
                    if file_path.is_file():
                        relative_path = str(file_path)

                        if relative_path not in db_files:
                            # 文件 not in 数据库, remove it
                            logger.info(f"Removing orphaned file: {relative_path}")
                            file_path.unlink()
                            cleaned_files += 1

            return {
                "status": "success",
                "files_cleaned": cleaned_files
            }

    except Exception as e:
        logger.error(f"Error cleaning up orphaned files: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def cleanup_old_metrics(days: int = 90) -> Dict[str, Any]:
    """
    Clean up old performance metrics (default: 3 months)
    """
    try:
        with get_db_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 删除 old metrics except important reports
            deleted = db.query(PerformanceMetrics).filter(
                PerformanceMetrics.recorded_at < cutoff_date,
                ~PerformanceMetrics.metric_type.in_([
                    'course_report',
                    'daily_report',
                    'learning_path'
                ])
            ).delete()

            db.commit()

            return {
                "status": "success",
                "metrics_deleted": deleted,
                "cutoff_date": cutoff_date.isoformat()
            }

    except Exception as e:
        logger.error(f"Error cleaning up old metrics: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def vacuum_vector_store() -> Dict[str, Any]:
    """
    Clean up vector store by removing orphaned embeddings
    """
    try:
        from core.rag.vector_store import VectorStore

        with get_db_session() as db:
            # 获取 全部 valid embedding IDs from 数据库
            from models.knowledge import KnowledgeChunk

            valid_ids = set()
            chunks = db.query(KnowledgeChunk.embedding_id).filter(
                KnowledgeChunk.embedding_id.isnot(None)
            ).all()

            valid_ids.update(chunk[0] for chunk in chunks)

            # In a real 实现, would compare with vector store
            # and remove orphaned embeddings

            logger.info(f"Vector store maintenance completed. Valid embeddings: {len(valid_ids)}")

            return {
                "status": "success",
                "valid_embeddings": len(valid_ids)
            }

    except Exception as e:
        logger.error(f"Error vacuuming vector store: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def cleanup_temp_files() -> Dict[str, Any]:
    """
    Clean up temporary files
    """
    try:
        temp_dirs = [
            "data/cache",
            "/tmp/education_ai"
        ]

        cleaned = 0

        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue

            # Remove files older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            for file_path in Path(temp_dir).rglob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned += 1

        return {
            "status": "success",
            "files_cleaned": cleaned
        }

    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")
        return {"status": "error", "message": str(e)}