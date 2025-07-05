"""
知识库API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from models.database import get_db
from services.knowledge_service import knowledge_service
from utils.auth import get_current_user
from utils.response import StandardResponse

router = APIRouter(tags=["知识库"])

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
        limit=3
    )

    if not search_results:
        return StandardResponse.success({
            "question": question,
            "answer": "抱歉，我在知识库中没有找到相关内容。",
            "sources": []
        })

    # 2. 构建上下文
    context = "\n\n".join([
        f"【{r['metadata'].get('type', '内容')}】{r['metadata'].get('title', '')}\n{r['content']}"
        for r in search_results
    ])

    # 3. 调用AI生成答案
    from core.llm.qwen_client import QwenClient
    llm_client = QwenClient()

    prompt = f"""基于以下知识库内容回答问题：

{context}

问题：{question}

请根据提供的内容准确回答问题。如果内容中没有相关信息，请明确说明。"""

    answer = await llm_client.generate(prompt, temperature=0.7)

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

class AskRequest(BaseModel):
    query: str
    context_type: str = "general"
    course_id: Optional[int] = None

@router.post("/ask")
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """基于知识库的问答（/qa的别名）"""
    return await knowledge_qa(
        question=request.query,
        course_id=request.course_id,
        db=db,
        current_user=current_user
    )