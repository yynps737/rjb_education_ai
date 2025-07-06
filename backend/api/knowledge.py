"""
知识库API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from models.database import get_db
from models.knowledge import KnowledgeDocument
from models.user import UserRole
from services.knowledge_service import knowledge_service
from utils.auth import get_current_user
from utils.response import StandardResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["知识库"])

@router.get("")
async def get_knowledge_items(
    category_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库文档列表"""
    query = db.query(KnowledgeDocument)
    
    # 应用过滤条件
    if search:
        query = query.filter(KnowledgeDocument.title.contains(search))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    # 转换为响应格式
    result = []
    for item in items:
        meta_data = item.meta_data or {}
        
        # 优先使用提取的内容，如果没有则使用原始内容
        content = meta_data.get("content", meta_data.get("original_content", ""))
        if not content and item.file_path:
            content = f"文件: {os.path.basename(item.file_path)}"
        
        result.append({
            "id": item.id,
            "title": item.title,
            "content": content[:500] + "..." if len(content) > 500 else content,  # 限制内容长度
            "type": item.file_type or "document",
            "category_id": 1,  # 默认分类ID
            "category_name": meta_data.get("category", "通用"),
            "tags": meta_data.get("tags", []),
            "author_id": item.uploaded_by,
            "author_name": "用户",  # TODO: 从用户表获取真实姓名
            "view_count": 0,
            "is_starred": False,
            "is_public": meta_data.get("is_public", True),
            "file_url": f"/api/knowledge/download/{item.id}" if item.file_path else None,
            "file_path": item.file_path,
            "file_size": item.file_size,
            "meta_data": {
                "processed": meta_data.get("processed", False),
                "word_count": meta_data.get("word_count", 0),
                "page_count": meta_data.get("page_count", 0)
            },
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        })
    
    return StandardResponse.success({
        "items": result,
        "pagination": {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total + page_size - 1) // page_size
        }
    })

@router.get("/categories")
async def get_categories(
    current_user = Depends(get_current_user)
):
    """获取知识库分类"""
    # 暂时返回固定分类
    categories = [
        {"id": "general", "name": "通用", "count": 0},
        {"id": "course", "name": "课程资料", "count": 0},
        {"id": "reference", "name": "参考文档", "count": 0}
    ]
    
    return StandardResponse.success(categories)

@router.post("/index/course/{course_id}")
async def index_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """将课程内容索引到向量数据库"""
    # 检查权限（教师或管理员）
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="权限不足")

    result = await knowledge_service.index_course(db, course_id)

    if result["success"]:
        return StandardResponse.success(result, result["message"])
    else:
        return StandardResponse.error(result["message"])

@router.get("/search")
async def search_knowledge(
    query: str = Query(..., description="搜索查询"),
    course_id: Optional[int] = Query(None, description="限定课程ID"),
    limit: int = Query(5, ge=1, le=20, description="返回结果数量"),
    current_user = Depends(get_current_user)
):
    """搜索知识库"""
    results = await knowledge_service.search_knowledge(
        query=query,
        course_id=course_id,
        limit=limit
    )

    return StandardResponse.success({
        "query": query,
        "results": results,
        "count": len(results)
    })

@router.get("/related/{content_type}/{content_id}")
async def get_related_content(
    content_type: str,
    content_id: str,
    limit: int = Query(5, ge=1, le=10),
    current_user = Depends(get_current_user)
):
    """获取相关内容推荐"""
    if content_type not in ["course", "chapter", "lesson"]:
        raise HTTPException(status_code=400, detail="无效的内容类型")

    results = await knowledge_service.get_related_content(
        content_id=content_id,
        content_type=content_type,
        limit=limit
    )

    return StandardResponse.success({
        "content_id": content_id,
        "content_type": content_type,
        "related": results
    })

@router.get("/stats")
async def get_index_stats(
    current_user = Depends(get_current_user)
):
    """获取知识库统计信息"""
    stats = knowledge_service.get_index_stats()
    return StandardResponse.success(stats)

@router.post("/create")
async def create_knowledge_item(
    title: str = Form(...),
    content: str = Form(...),
    type: str = Form("document"),
    category_id: str = Form("general"),
    tags: str = Form(""),
    is_public: bool = Form(True),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建知识库文档"""
    try:
        # 创建上传目录
        upload_dir = "uploads/knowledge"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = None
        file_type = type
        file_size = 0
        
        # 处理文件上传
        if file:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(file.filename)[1]
            new_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(upload_dir, new_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            
            # 根据文件扩展名确定类型
            if file_extension.lower() in ['.pdf']:
                file_type = 'pdf'
            elif file_extension.lower() in ['.doc', '.docx']:
                file_type = 'document'
            elif file_extension.lower() in ['.ppt', '.pptx']:
                file_type = 'presentation'
            elif file_extension.lower() in ['.mp4', '.avi', '.mov']:
                file_type = 'video'
        
        # 如果有文件上传，使用文档处理器提取内容
        extracted_content = content
        processed_doc = None
        
        if file and file_path:
            try:
                # 使用文档处理器处理文档
                document_processor = get_document_processor()
                processed_doc = document_processor.process_document(file_path)
                
                # 如果成功提取内容，使用提取的内容
                if processed_doc and processed_doc.content:
                    extracted_content = processed_doc.content
                    logger.info(f"成功从文档中提取 {processed_doc.word_count} 个词")
                    
            except Exception as e:
                logger.warning(f"文档处理失败，使用用户输入的内容: {e}")
                # 继续使用用户输入的内容
        
        # 创建知识库文档记录
        knowledge_doc = KnowledgeDocument(
            title=title,
            file_path=file_path or "",
            file_type=file_type,
            uploaded_by=current_user.id,
            file_size=file_size,
            meta_data={
                "content": extracted_content,
                "original_content": content,
                "category": category_id,
                "tags": tags.split(",") if tags else [],
                "is_public": is_public,
                "processed": processed_doc is not None,
                "word_count": processed_doc.word_count if processed_doc else len(extracted_content.split()),
                "page_count": processed_doc.page_count if processed_doc else 0
            }
        )
        
        db.add(knowledge_doc)
        db.commit()
        db.refresh(knowledge_doc)
        
        # 索引到向量数据库
        try:
            # 如果有处理后的文档，使用分块索引
            if processed_doc and processed_doc.chunks:
                documents = []
                metadatas = []
                ids = []
                
                for i, chunk in enumerate(processed_doc.chunks):
                    doc_content = f"{title}\n{chunk.content}"
                    doc_metadata = {
                        "type": "knowledge_document",
                        "document_id": knowledge_doc.id,
                        "title": title,
                        "category": category_id,
                        "tags": tags if isinstance(tags, str) else "",
                        "author_id": current_user.id,
                        "is_public": is_public,
                        "chunk_index": i,
                        "total_chunks": len(processed_doc.chunks)
                    }
                    doc_id = f"knowledge_doc_{knowledge_doc.id}_chunk_{i}"
                    
                    documents.append(doc_content)
                    metadatas.append(doc_metadata)
                    ids.append(doc_id)
                
                # 批量添加到向量数据库
                await knowledge_service.vector_store.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"成功索引 {len(documents)} 个文档块")
            else:
                # 没有分块，使用整个内容
                doc_content = f"{title}\n{extracted_content}"
                doc_metadata = {
                    "type": "knowledge_document",
                    "document_id": knowledge_doc.id,
                    "title": title,
                    "category": category_id,
                    "tags": tags if isinstance(tags, str) else "",
                    "author_id": current_user.id,
                    "is_public": is_public
                }
                doc_id = f"knowledge_doc_{knowledge_doc.id}"
                
                await knowledge_service.vector_store.add_documents(
                    documents=[doc_content],
                    metadatas=[doc_metadata],
                    ids=[doc_id]
                )
        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            # 不影响文档创建
        
        return StandardResponse.success({
            "id": knowledge_doc.id,
            "title": knowledge_doc.title,
            "type": knowledge_doc.file_type,
            "message": "知识库文档创建成功"
        })
        
    except Exception as e:
        db.rollback()
        # 如果出错，删除已上传的文件
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return StandardResponse.error(f"创建失败: {str(e)}")

@router.post("/qa")
async def knowledge_qa(
    question: str,
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """基于知识库的问答"""
    # 1. 搜索相关内容
    search_results = await knowledge_service.search_knowledge(
        query=question,
        course_id=course_id,
        limit=5  # 增加搜索结果数量
    )

    if not search_results:
        return StandardResponse.success({
            "question": question,
            "answer": "抱歉，我在知识库中没有找到相关内容。",
            "sources": []
        })

    # 2. 构建上下文（限制每个结果的长度）
    context_parts = []
    for r in search_results:
        content = r['content']
        
        # 检测并处理表格格式的内容
        # 检查是否包含表格标记（制表符分隔的数据）
        if '\t' in content or ('高' in content and '中' in content and '低' in content):
            # 这可能是表格数据，进行处理
            lines = content.split('\n')
            processed_content = []
            
            for line in lines:
                # 跳过空行和标题行
                if not line.strip() or '分类' in line or '字段名称' in line:
                    continue
                
                # 尝试用制表符分割
                parts = line.split('\t') if '\t' in line else line.split()
                
                # 确保有足够的部分
                if len(parts) >= 3:
                    # 跳过重要性标记行
                    if parts[-1] in ['高', '中', '低', '官方', '官方统计', '教育部']:
                        # 这是数据行，提取有用信息
                        if len(parts) >= 4:
                            field = parts[1]
                            value = parts[2]
                            # 清理值
                            if value and value not in ['高', '中', '低'] and not value.endswith('%'):
                                if '：' not in value:  # 避免重复格式化
                                    processed_content.append(f"{field}：{value}")
            
            # 如果处理后有内容，使用处理后的；否则截取原内容
            if processed_content:
                content = '\n'.join(processed_content[:15])  # 取前15条重要信息
            else:
                # 如果不是表格，就简单截取
                content = content[:500] + "..." if len(content) > 500 else content
        
        # 如果内容太长，截取
        if len(content) > 500:
            content = content[:500] + "..."
        
        title = r['metadata'].get('title', '')
        doc_type = r['metadata'].get('type', '内容')
        
        if content.strip():  # 只添加非空内容
            context_parts.append(f"【{doc_type}】{title}\n{content}")
    
    context = "\n\n".join(context_parts)

    # 3. 调用AI生成答案
    try:
        logger.info(f"开始处理AI问答，问题: {question}")
        logger.info(f"搜索结果数量: {len(search_results)}")
        logger.info(f"上下文预览: {context[:200]}...")
        
        from core.llm.qwen_client import QwenClient
        llm_client = QwenClient()
        logger.info("QwenClient 初始化成功")

        prompt = f"""你是一个友好专业的AI助手。请基于知识库内容，用自然流畅的语言回答用户问题。

特别注意：
1. 如果看到类似"8% 高 就业统计"、"学生发展 工科就业率 部分专业达100%"这样的格式，这是表格数据
2. 不要直接复制这些内容！要理解并转化为正常的句子
3. 如果看到"hi nihao"这样的测试文本，请忽略
4. 回答要像真人对话，不要有任何表格痕迹

知识库参考：
{context}

用户问题：{question}

请用友好自然的语言回答，要求：
- 把数据整理成完整的句子，例如："学校的就业率很高，工科专业甚至达到了100%"
- 用段落组织内容，不要罗列数据
- 保持亲切的语气，就像在和朋友介绍
- 重点突出用户关心的信息

回答："""

        answer = llm_client.generate(prompt, temperature=0.5)  # 降低温度使回答更稳定
        logger.info(f"AI回答成功，回答长度: {len(answer)}")
        
    except Exception as e:
        logger.error(f"调用AI失败: {str(e)}")
        # 如果AI调用失败，返回上下文内容（这可能是问题所在）
        answer = context

    return StandardResponse.success({
        "question": question,
        "answer": answer,
        "sources": [
            {
                "id": r["id"],
                "title": r["metadata"].get("title", ""),
                "type": r["metadata"].get("type", ""),
                "relevance": r["relevance_score"]
            }
            for r in search_results
        ]
    })

from pydantic import BaseModel
import os
import shutil
from datetime import datetime
from core.ai.document_processor import get_document_processor

class AskRequest(BaseModel):
    query: str
    context_type: str = "general"
    course_id: Optional[int] = None

@router.post("/ask-stream")
async def ask_question_stream(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """基于知识库的问答 - 流式传输版本"""
    logger.info(f"收到流式问答请求 /ask-stream - 问题: {request.query}")
    
    # 1. 搜索相关内容
    search_results = await knowledge_service.search_knowledge(
        query=request.query,
        course_id=request.course_id,
        limit=5
    )

    # 处理搜索结果
    context = ""
    sources = []
    
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

    async def generate():
        """生成流式响应"""
        try:
            # 先发送元数据
            metadata = {
                "type": "metadata",
                "question": request.query,
                "sources": sources,
                "has_context": bool(context)
            }
            yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
            
            from core.llm.qwen_client import QwenClient
            llm_client = QwenClient()
            
            if context:
                prompt = f"""你是一个友好专业的AI助手。请基于知识库内容，用自然流畅的语言回答用户问题。

特别注意：
1. 如果看到类似"8% 高 就业统计"、"学生发展 工科就业率 部分专业达100%"这样的格式，这是表格数据
2. 不要直接复制这些内容！要理解并转化为正常的句子
3. 如果看到"hi nihao"这样的测试文本，请忽略
4. 回答要像真人对话，不要有任何表格痕迹
5. 如果使用了知识库中的信息，请在回答的最后另起一行，添加参考来源
6. 参考来源格式：先空一行，然后写"参考来源：《具体文档标题》"

知识库参考：
{context}

用户问题：{request.query}

请用友好自然的语言回答，要求：
- 把数据整理成完整的句子，例如："学校的就业率很高，工科专业甚至达到了100%"
- 用段落组织内容，不要罗列数据
- 保持亲切的语气，就像在和朋友介绍
- 重点突出用户关心的信息
- 如果使用了知识库内容，记得在最后空一行后标注来源

回答："""
            else:
                # 无知识库内容时的通用回答
                prompt = f"""你是一个友好专业的AI助手。用户提出了一个问题，但知识库中没有相关内容。
请基于你的通用知识来回答用户的问题。

用户问题：{request.query}

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
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    # 强制刷新输出
                    import sys
                    sys.stdout.flush()
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式生成失败: {str(e)}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )

@router.post("/ask")
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """基于知识库的问答"""
    logger.info(f"收到问答请求 /ask - 问题: {request.query}")
    
    # 直接使用 knowledge_qa 的逻辑，而不是调用 knowledge_service.ask_question
    # 1. 搜索相关内容
    search_results = await knowledge_service.search_knowledge(
        query=request.query,
        course_id=request.course_id,
        limit=5
    )

    if not search_results:
        # 没有找到相关内容时，让AI基于通用知识回答
        try:
            from core.llm.qwen_client import QwenClient
            llm_client = QwenClient()
            
            prompt = f"""你是一个友好专业的AI助手。用户提出了一个问题，但知识库中没有相关内容。
请基于你的通用知识来回答用户的问题。

用户问题：{request.query}

请用友好自然的语言回答："""
            
            answer = llm_client.generate(prompt, temperature=0.7)
            
            return StandardResponse.success({
                "question": request.query,
                "answer": answer,
                "sources": [],
                "note": "此回答基于AI的通用知识，非知识库内容"
            })
        except:
            return StandardResponse.success({
                "question": request.query,
                "answer": "抱歉，我在知识库中没有找到相关内容。",
                "sources": []
            })

    # 2. 构建上下文（限制每个结果的长度）
    context_parts = []
    for r in search_results:
        content = r['content']
        
        # 检测并处理表格格式的内容
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
    try:
        logger.info(f"开始处理AI问答，问题: {request.query}")
        logger.info(f"搜索结果数量: {len(search_results)}")
        
        from core.llm.qwen_client import QwenClient
        llm_client = QwenClient()
        logger.info("QwenClient 初始化成功")

        prompt = f"""你是一个友好专业的AI助手。请基于知识库内容，用自然流畅的语言回答用户问题。

特别注意：
1. 如果看到类似"8% 高 就业统计"、"学生发展 工科就业率 部分专业达100%"这样的格式，这是表格数据
2. 不要直接复制这些内容！要理解并转化为正常的句子
3. 如果看到"hi nihao"这样的测试文本，请忽略
4. 回答要像真人对话，不要有任何表格痕迹

知识库参考：
{context}

用户问题：{request.query}

请用友好自然的语言回答，要求：
- 把数据整理成完整的句子，例如："学校的就业率很高，工科专业甚至达到了100%"
- 用段落组织内容，不要罗列数据
- 保持亲切的语气，就像在和朋友介绍
- 重点突出用户关心的信息

回答："""

        answer = llm_client.generate(prompt, temperature=0.5)
        logger.info(f"AI回答成功，回答长度: {len(answer)}")
        
    except Exception as e:
        logger.error(f"调用AI失败: {str(e)}")
        answer = "抱歉，AI服务暂时不可用，请稍后再试。"

    return StandardResponse.success({
        "question": request.query,
        "answer": answer,
        "sources": [
            {
                "id": r["id"],
                "title": r["metadata"].get("title", ""),
                "type": r["metadata"].get("type", ""),
                "relevance": r["relevance_score"]
            }
            for r in search_results
        ]
    })

@router.delete("/{item_id}")
async def delete_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除知识库文档"""
    # 查询文档
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == item_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限（只有上传者或管理员可以删除）
    if document.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="您没有权限删除此文档")
    
    try:
        # 1. 从向量数据库中删除（包括所有分块）
        try:
            # 删除主文档
            doc_id = f"knowledge_doc_{document.id}"
            knowledge_service.vector_store.collection.delete(ids=[doc_id])
            
            # 删除所有分块（使用模糊匹配）
            # 获取文档的元数据
            meta_data = document.meta_data or {}
            if meta_data.get("processed") and meta_data.get("total_chunks", 0) > 0:
                # 删除所有分块
                chunk_ids = [f"knowledge_doc_{document.id}_chunk_{i}" 
                           for i in range(meta_data.get("total_chunks", 0))]
                knowledge_service.vector_store.collection.delete(ids=chunk_ids)
                logger.info(f"删除了 {len(chunk_ids)} 个文档分块")
        except Exception as e:
            logger.warning(f"从向量数据库删除文档失败: {e}")
            # 继续删除数据库记录
        
        # 2. 删除文件（如果存在）
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                logger.warning(f"删除文件失败: {e}")
        
        # 3. 从数据库中删除记录
        db.delete(document)
        db.commit()
        
        return StandardResponse.success({
            "message": "文档删除成功",
            "id": item_id
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除文档失败: {e}")
        return StandardResponse.error(f"删除失败: {str(e)}")

@router.post("/batch-delete")
async def batch_delete_knowledge_items(
    ids: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量删除知识库文档"""
    try:
        item_ids = ids.get("ids", [])
        if not item_ids:
            raise HTTPException(status_code=400, detail="请提供要删除的文档ID列表")
        
        # 查询所有要删除的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id.in_(item_ids)
        ).all()
        
        if not documents:
            raise HTTPException(status_code=404, detail="未找到任何文档")
        
        # 检查权限
        deleted_count = 0
        failed_items = []
        
        for document in documents:
            # 只有上传者或管理员可以删除
            if document.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN:
                failed_items.append({
                    "id": document.id,
                    "reason": "无权限删除"
                })
                continue
            
            try:
                # 1. 从向量数据库中删除（包括所有分块）
                try:
                    # 删除主文档
                    doc_id = f"knowledge_doc_{document.id}"
                    knowledge_service.vector_store.collection.delete(ids=[doc_id])
                    
                    # 删除所有分块
                    meta_data = document.meta_data or {}
                    if meta_data.get("processed") and meta_data.get("total_chunks", 0) > 0:
                        chunk_ids = [f"knowledge_doc_{document.id}_chunk_{i}" 
                                   for i in range(meta_data.get("total_chunks", 0))]
                        knowledge_service.vector_store.collection.delete(ids=chunk_ids)
                except Exception as e:
                    logger.warning(f"从向量数据库删除文档失败: {e}")
                
                # 2. 删除文件（如果存在）
                if document.file_path and os.path.exists(document.file_path):
                    try:
                        os.remove(document.file_path)
                    except Exception as e:
                        logger.warning(f"删除文件失败: {e}")
                
                # 3. 从数据库中删除记录
                db.delete(document)
                deleted_count += 1
                
            except Exception as e:
                failed_items.append({
                    "id": document.id,
                    "reason": str(e)
                })
        
        db.commit()
        
        return StandardResponse.success({
            "message": f"成功删除 {deleted_count} 个文档",
            "deleted_count": deleted_count,
            "failed_items": failed_items
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除文档失败: {e}")
        return StandardResponse.error(f"批量删除失败: {str(e)}")

@router.get("/download/{item_id}")
async def download_knowledge_file(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """下载知识库文档的文件"""
    from fastapi.responses import FileResponse
    
    # 查询文档
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == item_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    meta_data = document.meta_data or {}
    if not meta_data.get("is_public", True):
        # 非公开文档，只有上传者或管理员可以下载
        if document.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="您没有权限下载此文档")
    
    # 检查文件是否存在
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回文件
    return FileResponse(
        path=document.file_path,
        filename=os.path.basename(document.file_path),
        media_type='application/octet-stream'
    )

@router.post("/index-all")
async def index_all_documents(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """索引所有知识文档到向量数据库"""
    # 检查权限（管理员）
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取所有知识文档
    documents = db.query(KnowledgeDocument).all()
    
    indexed_count = 0
    errors = []
    
    for doc in documents:
        try:
            # 提取内容
            meta_data = doc.meta_data or {}
            content = meta_data.get("content", "")
            if not content:
                continue
                
            doc_content = f"{doc.title}\n{content}"
            doc_metadata = {
                "type": "knowledge_document",
                "document_id": doc.id,
                "title": doc.title,
                "category": meta_data.get("category", "general"),
                "tags": ",".join(meta_data.get("tags", [])) if isinstance(meta_data.get("tags", []), list) else str(meta_data.get("tags", "")),
                "author_id": doc.uploaded_by,
                "is_public": meta_data.get("is_public", True)
            }
            doc_id = f"knowledge_doc_{doc.id}"
            
            # 添加到向量数据库
            await knowledge_service.vector_store.add_documents(
                documents=[doc_content],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            indexed_count += 1
        except Exception as e:
            errors.append({
                "doc_id": doc.id,
                "title": doc.title,
                "error": str(e)
            })
    
    return StandardResponse.success({
        "indexed_count": indexed_count,
        "total_documents": len(documents),
        "errors": errors,
        "message": f"成功索引 {indexed_count}/{len(documents)} 个文档"
    })