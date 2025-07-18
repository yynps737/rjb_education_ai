from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from models.database import get_db
from models.user import User, UserRole
from models.course import Chapter, Lesson
from utils.auth import require_role
from utils.response import success_response, error_response
from services.analytics_service import analytics_service
from services.knowledge_service import knowledge_service

router = APIRouter()

class LessonResponse(BaseModel):
    id: int
    title: str
    content: str
    order: int
    duration_minutes: Optional[int]
    knowledge_points: List[str]
    resources: List[dict]
    progress: float

class ChapterWithLessons(BaseModel):
    id: int
    title: str
    description: Optional[str]
    order: int
    progress: float
    lessons: List[LessonResponse]

class TrackProgressRequest(BaseModel):
    time_spent: int = 0  # minutes

class AskQuestionRequest(BaseModel):
    question: str
    course_id: Optional[int] = None

@router.get("/courses/{course_id}/chapters", response_model=List[ChapterWithLessons])
async def get_course_chapters_with_progress(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get all chapters with lessons and progress for a course"""
    # 验证enrollment
    from services.course_service import course_service
    course = course_service.get_course_with_chapters(db, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    chapters_data = []

    for chapter in course.chapters:
        # 获取chapter progress
        chapter_progress = db.query(analytics_service.LearningProgress).filter(
            analytics_service.LearningProgress.user_id == current_user.id,
            analytics_service.LearningProgress.chapter_id == chapter.id,
            analytics_service.LearningProgress.lesson_id.is_(None)
        ).first()

        # 获取lessons with progress
        lessons_data = []
        for lesson in chapter.lessons:
            lesson_progress = db.query(analytics_service.LearningProgress).filter(
                analytics_service.LearningProgress.user_id == current_user.id,
                analytics_service.LearningProgress.lesson_id == lesson.id
            ).first()

            lessons_data.append(LessonResponse(
                id=lesson.id,
                title=lesson.title,
                content=lesson.content,
                order=lesson.order,
                duration_minutes=lesson.duration_minutes,
                knowledge_points=lesson.knowledge_points or [],
                resources=lesson.resources or [],
                progress=lesson_progress.progress_percentage if lesson_progress else 0.0
            ))

        chapters_data.append(ChapterWithLessons(
            id=chapter.id,
            title=chapter.title,
            description=chapter.description,
            order=chapter.order,
            progress=chapter_progress.progress_percentage if chapter_progress else 0.0,
            lessons=lessons_data
        ))

    return chapters_data

@router.get("/lessons/{lesson_id}")
async def get_lesson_content(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get lesson content and mark as accessed"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # 验证enrollment
    course = lesson.chapter.course
    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    # Track access
    analytics_service.track_learning_progress(
        db,
        user_id=current_user.id,
        course_id=course.id,
        chapter_id=lesson.chapter_id,
        lesson_id=lesson_id,
        time_spent=1  # Initial access
    )

    # 获取related knowledge base内容
    related_content = []
    if lesson.knowledge_points:
        for point in lesson.knowledge_points[:3]:  # Top 3 knowledge points
            results = await knowledge_service.search_knowledge(
                query=point,
                course_id=course.id,
                top_k=2
            )
            related_content.extend(results)

    return success_response(data={
        "lesson": {
            "id": lesson.id,
            "title": lesson.title,
            "content": lesson.content,
            "duration_minutes": lesson.duration_minutes,
            "knowledge_points": lesson.knowledge_points or [],
            "resources": lesson.resources or []
        },
        "chapter": {
            "id": lesson.chapter.id,
            "title": lesson.chapter.title
        },
        "course": {
            "id": course.id,
            "title": course.title
        },
        "related_content": related_content
    })

@router.post("/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    lesson_id: int,
    progress_data: TrackProgressRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Update learning progress for a lesson"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # 验证enrollment
    course = lesson.chapter.course
    if current_user not in course.users:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    # 更新progress
    progress = analytics_service.track_learning_progress(
        db,
        user_id=current_user.id,
        course_id=course.id,
        chapter_id=lesson.chapter_id,
        lesson_id=lesson_id,
        time_spent=progress_data.time_spent
    )

    # 记录performance metric
    analytics_service.record_performance_metric(
        db,
        user_id=current_user.id,
        course_id=course.id,
        metric_type="lesson_completion",
        value=progress.progress_percentage,
        metadata={
            "lesson_id": lesson_id,
            "time_spent": progress_data.time_spent
        }
    )

    return success_response(
        message="Progress updated",
        data={
            "lesson_progress": progress.progress_percentage,
            "total_time_spent": progress.time_spent_minutes
        }
    )

@router.post("/ask-stream")
async def ask_question_stream(
    request: AskQuestionRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Ask a question and get AI-powered answer - Stream version"""
    # If course_id provided, 验证enrollment
    if request.course_id:
        from services.course_service import course_service
        course = course_service.get(db, request.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if current_user not in course.users:
            raise HTTPException(
                status_code=403,
                detail="You are not enrolled in this course"
            )

    async def generate():
        """生成流式响应"""
        import asyncio
        try:
            # 1. 搜索相关内容
            search_results = await knowledge_service.search_knowledge(
                query=request.question,
                course_id=request.course_id,
                limit=5
            )

            # 处理搜索结果
            context = ""
            sources = []
            used_sources = []  # 实际使用的来源
            
            if search_results:
                context_parts = []
                source_titles = []  # 收集实际使用的知识库标题
                
                for i, r in enumerate(search_results):
                    content = r['content']
                    title = r['metadata'].get('title', '未命名文档')
                    
                    # 只使用相关度高的内容（前3个）
                    if i < 3 and r['relevance_score'] > 0.5:
                        # 记录使用的知识库标题
                        if title not in source_titles:
                            source_titles.append(title)
                    
                    # 处理表格格式的内容
                    if '\t' in content or ('高' in content and '中' in content and '低' in content):
                        lines = content.split('\n')
                        processed_content = []
                        
                        for line in lines:
                            if not line.strip() or '分类' in line or '字段名称' in line:
                                continue
                            
                            parts = line.split('\t') if '\t' in line else line.split()
                            
                            if len(parts) >= 3:
                                if parts[-1] in ['高', '中', '低', '官方', '官方统计', '教育部']:
                                    if len(parts) >= 4:
                                        field = parts[1]
                                        value = parts[2]
                                        if value and value not in ['高', '中', '低'] and not value.endswith('%'):
                                            if '：' not in value:
                                                processed_content.append(f"{field}：{value}")
                        
                        if processed_content:
                            content = '\n'.join(processed_content[:15])
                        else:
                            content = content[:500] + "..." if len(content) > 500 else content
                    
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    doc_type = r['metadata'].get('type', '内容')
                    
                    if content.strip():
                        context_parts.append(f"【{doc_type}】{title}\n{content}")
                    
                    sources.append({
                        "id": r["id"],
                        "title": r["metadata"].get("title", ""),
                        "type": r["metadata"].get("type", ""),
                        "relevance": r["relevance_score"]
                    })
                
                context = "\n\n".join(context_parts)
                # 只有在有实际来源时才添加标题信息
                if source_titles:
                    context += f"\n\n[使用的知识库: {', '.join(source_titles[:3])}]"

            # 先发送元数据
            metadata = {
                "type": "metadata",
                "question": request.question,
                "sources": [],  # 先不发送来源，等AI回答后再决定
                "has_context": bool(context)
            }
            yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n".encode('utf-8')
            
            from core.llm.qwen_client import QwenClient
            llm_client = QwenClient()
            
            if context:
                prompt = f"""你是一个友好专业的AI学习助手。请基于知识库内容，用自然流畅的语言回答学生的问题。

特别注意：
1. 如果看到类似"8% 高 就业统计"这样的格式，这是表格数据，要转化为自然语言
2. 用亲切友好的语气，像朋友一样交流
3. 重点解答学生的疑问，提供有帮助的信息
4. 如果使用了知识库中的信息，请在回答的最后另起一行，添加参考来源
5. 参考来源格式：先空一行，然后写"参考来源：《具体文档标题》"

知识库参考：
{context}

学生问题：{request.question}

请用友好自然的语言回答。如果使用了知识库内容，记得在最后另起一行标注来源："""
            else:
                # 无知识库内容时的通用回答
                prompt = f"""你是一个友好专业的AI学习助手。用户提出了一个问题，但知识库中没有相关内容。
请基于你的通用知识来回答学生的问题。

学生问题：{request.question}

请用友好自然的语言回答："""
            
            # 获取流式响应
            stream = llm_client.generate_stream(prompt, temperature=0.5)
            
            # 逐块发送响应
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    data = {
                        "type": "content",
                        "content": chunk.choices[0].delta.content
                    }
                    # 确保每个SSE消息都立即发送
                    sse_message = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    yield sse_message.encode('utf-8')
                    
                    # 添加小延迟确保数据发送
                    await asyncio.sleep(0.001)
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n".encode('utf-8')
            
            # Log the question for analytics (only if course_id is provided)
            if request.course_id:
                analytics_service.record_performance_metric(
                    db,
                    user_id=current_user.id,
                    course_id=request.course_id,
                    metric_type="question_asked",
                    value=1,
                    metadata={
                        "question": request.question[:200]
                    }
                )
            
        except Exception as e:
            import logging
            logging.error(f"流式生成失败: {str(e)}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n".encode('utf-8')
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Content-Encoding": "none",  # 禁用压缩
            "Access-Control-Allow-Origin": "*",  # CORS支持
            "Transfer-Encoding": "chunked"  # 使用分块传输
        }
    )

@router.post("/ask")
async def ask_question(
    request: AskQuestionRequest,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Ask a question and get AI-powered answer"""
    # If course_id provided, 验证enrollment
    if request.course_id:
        from services.course_service import course_service
        course = course_service.get(db, request.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if current_user not in course.users:
            raise HTTPException(
                status_code=403,
                detail="You are not enrolled in this course"
            )

    try:
        # 1. 搜索相关内容
        search_results = await knowledge_service.search_knowledge(
            query=request.question,
            course_id=request.course_id,
            limit=5
        )

        if not search_results:
            return success_response(data={
                "question": request.question,
                "answer": "抱歉，我在知识库中没有找到相关内容。"
            })

        # 2. 构建上下文
        context_parts = []
        for r in search_results:
            content = r['content']
            
            # 处理表格格式的内容
            if '\t' in content or ('高' in content and '中' in content and '低' in content):
                lines = content.split('\n')
                processed_content = []
                
                for line in lines:
                    if not line.strip() or '分类' in line or '字段名称' in line:
                        continue
                    
                    parts = line.split('\t') if '\t' in line else line.split()
                    
                    if len(parts) >= 3:
                        if parts[-1] in ['高', '中', '低', '官方', '官方统计', '教育部']:
                            if len(parts) >= 4:
                                field = parts[1]
                                value = parts[2]
                                if value and value not in ['高', '中', '低'] and not value.endswith('%'):
                                    if '：' not in value:
                                        processed_content.append(f"{field}：{value}")
                
                if processed_content:
                    content = '\n'.join(processed_content[:15])
                else:
                    content = content[:500] + "..." if len(content) > 500 else content
            
            if len(content) > 500:
                content = content[:500] + "..."
            
            title = r['metadata'].get('title', '')
            doc_type = r['metadata'].get('type', '内容')
            
            if content.strip():
                context_parts.append(f"【{doc_type}】{title}\n{content}")
        
        context = "\n\n".join(context_parts)

        # 3. 调用AI生成答案
        from core.llm.qwen_client import QwenClient
        llm_client = QwenClient()

        prompt = f"""你是一个友好专业的AI学习助手。请基于知识库内容，用自然流畅的语言回答学生的问题。

特别注意：
1. 如果看到类似"8% 高 就业统计"这样的格式，这是表格数据，要转化为自然语言
2. 用亲切友好的语气，像朋友一样交流
3. 重点解答学生的疑问，提供有帮助的信息

知识库参考：
{context}

学生问题：{request.question}

请用友好自然的语言回答："""

        answer = llm_client.generate(prompt, temperature=0.5)

        # Log the question for analytics (only if course_id is provided)
        if request.course_id:
            analytics_service.record_performance_metric(
                db,
                user_id=current_user.id,
                course_id=request.course_id,
                metric_type="question_asked",
                value=1,
                metadata={
                    "question": request.question[:200]
                }
            )

        return success_response(data={
            "question": request.question,
            "answer": answer
        })
    except Exception as e:
        import logging
        logging.error(f"Failed to process question: {str(e)}")
        return error_response(f"Failed to process question: {str(e)}")

@router.get("/progress/summary")
async def get_learning_summary(
    course_id: Optional[int] = None,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get learning progress summary"""
    summary = analytics_service.get_student_analytics(
        db,
        student_id=current_user.id,
        course_id=course_id
    )

    return success_response(data=summary)

@router.get("/progress")
async def get_learning_progress(
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get overall learning progress"""
    summary = analytics_service.get_student_analytics(
        db,
        student_id=current_user.id
    )
    
    return success_response(data=summary)