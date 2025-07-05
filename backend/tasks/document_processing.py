from celery import shared_task
from typing import Dict, Any
import logging
from pathlib import Path

from models.database import get_db_session
from models.knowledge import KnowledgeDocument, KnowledgeChunk
from core.knowledge_base.document_processor import DocumentProcessor
from core.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_document_async(self, document_id: int) -> Dict[str, Any]:
    """
    Asynchronously process a document for the knowledge base
    """
    try:
        with get_db_session() as db:
            # 获取 文档
            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()

            if not document:
                return {"status": "error", "message": "Document not found"}

            # 初始化 processors
            doc_processor = DocumentProcessor()
            vector_store = VectorStore()

            # 进程 文档
            logger.info(f"Processing document {document_id}: {document.title}")
            chunks = doc_processor.process_file(document.file_path)

            # Store chunks
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                # Add to vector store
                embedding_ids = vector_store.add_texts(
                    texts=[chunk['content']],
                    metadatas=[{
                        'document_id': document.id,
                        'chunk_index': i,
                        'page_number': chunk.get('page_number'),
                        'title': document.title,
                        'course_id': document.course_id
                    }]
                )

                # 创建 chunk 记录
                kb_chunk = KnowledgeChunk(
                    document_id=document.id,
                    content=chunk['content'],
                    chunk_index=i,
                    page_number=chunk.get('page_number'),
                    embedding_id=embedding_ids[0] if embedding_ids else None,
                    metadata=chunk.get('metadata', {})
                )

                db.add(kb_chunk)
                chunk_ids.append(kb_chunk.id)

            db.commit()

            logger.info(f"Successfully processed document {document_id} with {len(chunks)} chunks")

            return {
                "status": "success",
                "document_id": document_id,
                "chunks_created": len(chunks),
                "chunk_ids": chunk_ids
            }

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")

        # 重试 with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@shared_task
def cleanup_failed_documents() -> Dict[str, Any]:
    """
    Clean up documents that failed processing
    """
    try:
        with get_db_session() as db:
            # Find documents without chunks (likely 失败 处理中)
            failed_docs = db.query(KnowledgeDocument).filter(
                ~KnowledgeDocument.chunks.any()
            ).all()

            cleaned = 0
            for doc in failed_docs:
                # 删除 文件 if exists
                if Path(doc.file_path).exists():
                    Path(doc.file_path).unlink()

                # 删除 文档 记录
                db.delete(doc)
                cleaned += 1

            db.commit()

            return {
                "status": "success",
                "documents_cleaned": cleaned
            }

    except Exception as e:
        logger.error(f"Error cleaning up failed documents: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@shared_task
def reindex_course_documents(course_id: int) -> Dict[str, Any]:
    """
    Reindex all documents for a course
    """
    try:
        with get_db_session() as db:
            documents = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.course_id == course_id
            ).all()

            reindexed = 0
            for doc in documents:
                # 删除 existing chunks from vector store
                for chunk in doc.chunks:
                    if chunk.embedding_id:
                        VectorStore().delete([chunk.embedding_id])

                # 删除 chunk records
                db.query(KnowledgeChunk).filter(
                    KnowledgeChunk.document_id == doc.id
                ).delete()

                db.commit()

                # Reprocess 文档
                process_document_async.delay(doc.id)
                reindexed += 1

            return {
                "status": "success",
                "documents_queued": reindexed
            }

    except Exception as e:
        logger.error(f"Error reindexing course {course_id} documents: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }