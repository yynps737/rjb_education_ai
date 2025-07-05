"""
知识库服务 - 管理课程内容的向量化存储和检索
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from models.course import Course, Chapter, Lesson
from models.knowledge import KnowledgeDocument
from core.vector_db.optimized_chroma_store import OptimizedChromaStore
from core.config import settings

logger = logging.getLogger(__name__)

class KnowledgeService:
    """知识库管理服务"""

    def __init__(self):
        # 初始化优化的向量存储（使用DashScope嵌入）
        import os
        dashscope_key = None
        if hasattr(settings, 'dashscope_api_key') and settings.dashscope_api_key:
            if hasattr(settings.dashscope_api_key, 'get_secret_value'):
                dashscope_key = str(settings.dashscope_api_key.get_secret_value())
            else:
                dashscope_key = str(settings.dashscope_api_key)
        else:
            dashscope_key = os.getenv("DASHSCOPE_API_KEY")

        self.vector_store = OptimizedChromaStore(
            collection_name="course_knowledge",
            api_key=dashscope_key
        )

    async def index_course(self, db: Session, course_id: int) -> Dict[str, Any]:
        """将课程内容索引到向量数据库"""
        # 获取课程信息
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return {"success": False, "message": "课程不存在"}

        documents = []
        metadatas = []
        ids = []

        # 索引课程基本信息
        course_doc = f"课程：{course.title}\n描述：{course.description}"
        documents.append(course_doc)
        metadatas.append({
            "type": "course",
            "course_id": course_id,
            "title": course.title,
            "subject": course.subject,
            "grade_level": course.grade_level
        })
        ids.append(f"course_{course_id}")

        # 索引章节和课时
        chapters = db.query(Chapter).filter(Chapter.course_id == course_id).all()
        for chapter in chapters:
            # 索引章节
            chapter_doc = f"章节：{chapter.title}\n{chapter.description or ''}"
            documents.append(chapter_doc)
            metadatas.append({
                "type": "chapter",
                "course_id": course_id,
                "chapter_id": chapter.id,
                "title": chapter.title,
                "order": chapter.order_index
            })
            ids.append(f"chapter_{chapter.id}")

            # 索引课时
            lessons = db.query(Lesson).filter(Lesson.chapter_id == chapter.id).all()
            for lesson in lessons:
                lesson_doc = f"课时：{lesson.title}\n内容：{lesson.content}"
                documents.append(lesson_doc)
                metadatas.append({
                    "type": "lesson",
                    "course_id": course_id,
                    "chapter_id": chapter.id,
                    "lesson_id": lesson.id,
                    "title": lesson.title,
                    "duration": lesson.duration_minutes
                })
                ids.append(f"lesson_{lesson.id}")

        # 添加到向量数据库
        await self.vector_store.add_documents(documents, metadatas, ids)

        return {
            "success": True,
            "message": f"成功索引课程 {course.title}",
            "indexed_count": len(documents)
        }

    async def search_knowledge(
        self,
        query: str,
        course_id: Optional[int] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索知识库"""
        # 构建过滤条件
        filter_dict = {}
        if course_id:
            filter_dict["course_id"] = course_id

        # 执行向量搜索
        results = await self.vector_store.search(
            query=query,
            n_results=limit,
            filter=filter_dict if filter_dict else None
        )

        # 格式化结果
        formatted_results = []
        for i in range(len(results["documents"])):
            formatted_results.append({
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
                "relevance_score": 1 - results["distances"][i],
                # 转换为相似度分数
                "id": results["ids"][i]
            })

        return formatted_results

    async def get_related_content(
        self,
        content_id: str,
        content_type: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取相关内容"""
        # 根据ID获取原始内容
        search_text = ""

        if content_type == "lesson":
            # 从数据库获取课时内容作为查询
            # 这里简化处理，实际应该从数据库查询
            search_text = f"相关课时内容"
        elif content_type == "chapter":
            search_text = f"相关章节内容"
        else:
            search_text = f"相关课程内容"

        # 搜索相似内容
        results = await self.vector_store.search(
            query=search_text,
            n_results=limit + 1
            # 多查一个以排除自己
        )

        # 过滤掉自己
        filtered_results = []
        for i in range(len(results["documents"])):
            if results["ids"][i] != content_id:
                filtered_results.append({
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "relevance_score": 1 - results["distances"][i],
                    "id": results["ids"][i]
                })

        return filtered_results[:limit]

    async def update_knowledge_index(
        self,
        db: Session,
        content_id: str,
        content_type: str,
        new_content: str
    ) -> Dict[str, Any]:
        """更新知识索引"""
        # 构建元数据
        metadata = {
            "type": content_type,
            "updated_at": str(datetime.utcnow())
        }

        # 删除旧文档并添加新的
        # 注意：OptimizedChromaStore 没有 update_document 方法，使用删除后重新添加
        try:
            # 先删除旧文档
            self.vector_store.collection.delete(ids=[content_id])

            # 添加新文档
            await self.vector_store.add_documents(
                documents=[new_content],
                metadatas=[metadata],
                ids=[content_id]
            )

            return {
                "success": True,
                "message": f"成功更新 {content_type} 的索引"
            }
        except Exception as e:
            logger.error(f"更新知识索引失败: {e}")
            return {
                "success": False,
                "message": f"更新失败: {str(e)}"
            }

    def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return self.vector_store.get_collection_stats()

    async def ask_question(self, question: str, course_id: Optional[int] = None) -> Dict[str, Any]:
        """基于知识库回答问题"""
        try:
            # 搜索相关内容
            search_results = await self.search_knowledge(
                query=question,
                course_id=course_id,
                limit=3
            )
            
            if not search_results:
                return {
                    "answer": "抱歉，我无法在知识库中找到相关信息来回答您的问题。",
                    "sources": [],
                    "confidence": 0.0
                }
            
            # 构建上下文
            context = "\n\n".join([result["content"] for result in search_results[:3]])
            
            # 简单的回答生成（实际应用中应该使用LLM）
            answer = f"根据知识库中的信息：\n\n{context}\n\n这是关于您问题的相关内容。"
            
            return {
                "answer": answer,
                "sources": [
                    {
                        "content": result["content"][:200] + "...",
                        "metadata": result["metadata"],
                        "relevance_score": result["relevance_score"]
                    }
                    for result in search_results[:3]
                ],
                "confidence": max([r["relevance_score"] for r in search_results[:3]]) if search_results else 0.0
            }
        except Exception as e:
            logger.error(f"处理问题时出错: {str(e)}")
            return {
                "answer": f"处理您的问题时出现错误：{str(e)}",
                "sources": [],
                "confidence": 0.0
            }

# 创建单例实例
knowledge_service = KnowledgeService()