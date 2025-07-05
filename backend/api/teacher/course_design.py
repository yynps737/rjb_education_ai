"""
教师端 - 智能备课API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from typing import List, Dict, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import logging
from models.database import get_db
from models.user import User, UserRole
from utils.auth import require_role
from core.llm.qwen_client import get_qwen_client
from core.rag.vector_store import VectorStore, RAGEngine
from core.evaluation.question_generator import QuestionGenerator, QuestionType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Teacher - Course Design"])

# 请求响应模型
class CourseOutlineRequest(BaseModel):
    """课程大纲生成请求"""
    course_name: str
    duration_minutes: int = 45
    grade_level: str  # 如：大一、高三等
    knowledge_points: List[str]  # 知识点列表
    teaching_objectives: Optional[List[str]] = None

class CourseOutlineResponse(BaseModel):
    """课程大纲响应"""
    course_name: str
    duration_minutes: int
    sections: List[Dict]  # 课程章节
    teaching_methods: List[str]  # 教学方法
    required_materials: List[str]  # 所需材料

class GenerateQuestionsRequest(BaseModel):
    """生成题目请求"""
    knowledge_content: str
    question_types: List[str]  # ["single_choice", "coding", etc.]
    num_questions: int = 5
    difficulty: int = 3  # 1-5

class LessonPlanRequest(BaseModel):
    """课程计划请求"""
    topic: str
    objectives: List[str]
    duration: int
    student_level: str

# 全局实例
llm_model = None
vector_store = None
rag_engine = None
question_generator = None

def get_llm_model():
    global llm_model
    if llm_model is None:
        llm_model = get_qwen_client()
    return llm_model

def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store

def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine(get_vector_store(), get_llm_model())
    return rag_engine

def get_question_generator():
    global question_generator
    if question_generator is None:
        question_generator = QuestionGenerator()
    return question_generator

@router.post("/generate-outline")
async def generate_course_outline(request: CourseOutlineRequest):
    """生成课程大纲"""
    try:
        llm = get_llm_model()

        # 构建提示
        knowledge_str = "、".join(request.knowledge_points)
        objectives_str = "、".join(request.teaching_objectives) if request.teaching_objectives else "培养学生对相关知识的理解和应用能力"

        prompt = f"""请为以下课程生成详细的教学大纲：

课程名称：{request.course_name}
课程时长：{request.duration_minutes}分钟
年级水平：{request.grade_level}
主要知识点：{knowledge_str}
教学目标：{objectives_str}

请生成包含以下内容的教学大纲：
1. 课程导入（5分钟）
2. 知识讲解（按知识点分配时间）
3. 实践练习
4. 课堂总结
5. 作业布置

每个部分请包含：
- 时间分配
- 具体内容
- 教学方法
- 学生活动

请以JSON格式输出。"""

        # 添加JSON格式要求
        prompt += """

请严格按照以下JSON格式输出：
{
    "sections": [
        {
            "name": "章节名称",
            "duration": 时间（分钟）,
            "content": "具体内容",
            "activities": "学生活动",
            "method": "教学方法"
        }
    ],
    "teaching_methods": ["方法1", "方法2"],
    "required_materials": ["材料1", "材料2"]
}"""

        try:
            response = llm.generate(prompt=prompt)
            
            # 解析响应
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                outline_data = json.loads(json_match.group())
                
                # 确保sections存在且格式正确
                sections = outline_data.get("sections", [])
                if not sections:
                    raise ValueError("No sections in response")
                
                return CourseOutlineResponse(
                    course_name=request.course_name,
                    duration_minutes=request.duration_minutes,
                    sections=sections,
                    teaching_methods=outline_data.get("teaching_methods", ["讲授法", "讨论法", "练习法"]),
                    required_materials=outline_data.get("required_materials", ["PPT", "练习题"])
                )
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}")
        
        # 如果解析失败，返回基础结构
        return CourseOutlineResponse(
            course_name=request.course_name,
            duration_minutes=request.duration_minutes,
            sections=[
                {"name": "课程导入", "duration": 5, "content": "介绍本节课主题", "activities": "学生聆听", "method": "讲授法"},
                {"name": "知识讲解", "duration": 25, "content": knowledge_str, "activities": "记笔记、提问", "method": "讲授法+讨论法"},
                {"name": "实践练习", "duration": 10, "content": "学生练习相关题目", "activities": "动手练习", "method": "练习法"},
                {"name": "课堂总结", "duration": 5, "content": "回顾要点", "activities": "总结反思", "method": "讲授法"}
            ],
            teaching_methods=["讲授法", "讨论法", "练习法"],
            required_materials=["PPT", "练习题", "教材"]
        )

    except Exception as e:
        logger.error(f"Error generating course outline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-material")
async def upload_teaching_material(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """上传教学材料到知识库"""
    try:
        # 导入 文件 安全 validator
        from utils.file_security import file_validator
        from utils.response import StandardResponse
        from models.knowledge import KnowledgeDocument
        from core.exceptions import ValidationException
        from pathlib import Path

        # 校验 and 保存 文件 securely
        allowed_categories = ["document", "presentation", "spreadsheet"]
        relative_path, file_info = await file_validator.save_upload_file(
            file,
            allowed_categories=allowed_categories,
            subfolder=f"teacher_{current_user.id}"
        )

        # 保存 文件 信息 to 数据库
        knowledge_doc = KnowledgeDocument(
            title=file.filename,
            file_path=relative_path,
            file_type=Path(file.filename).suffix.lower(),
            uploaded_by=current_user.id,
            file_size=file_info["file_size"],
            meta_data=file_info
        )
        db.add(knowledge_doc)
        db.commit()

        # 进程 文档 asynchronously
        from tasks.document_processing import process_document_async
        task = process_document_async.delay(knowledge_doc.id)

        return StandardResponse.success(
            data={
                "document_id": knowledge_doc.id,
                "file_name": file.filename,
                "file_size": file_info["file_size"],
                "task_id": task.id,
                "message": "Document uploaded successfully. Processing in background."
            },
            message="Upload successful",
            request=request
        )

    except ValidationException as e:
        return StandardResponse.validation_error(
            {"file": str(e)},
            request=request
        )
    except Exception as e:
        logger.error(f"Error uploading material: {e}")
        return StandardResponse.error(
            "Failed to upload material",
            status_code=500,
            request=request
        )

@router.post("/generate-questions")
async def generate_questions(request: GenerateQuestionsRequest):
    """基于知识内容生成题目"""
    try:
        generator = get_question_generator()

        # 转换题型
        question_types = []
        for qt in request.question_types:
            try:
                question_types.append(QuestionType(qt))
            except ValueError:
                logger.warning(f"Unknown question type: {qt}")

        if not question_types:
            raise HTTPException(status_code=400, detail="No valid question types provided")

        # 生成题目
        questions = generator.generate_questions(
            knowledge_content=request.knowledge_content,
            question_types=question_types,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )

        # 转换为可序列化格式
        questions_data = []
        for q in questions:
            questions_data.append({
                "type": q.type.value,
                "content": q.content,
                "options": q.options,
                "answer": q.answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "score": q.score,
                "knowledge_points": q.knowledge_points
            })

        return {
            "status": "success",
            "questions": questions_data,
            "total": len(questions_data)
        }

    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-knowledge")
async def search_knowledge(query: str, top_k: int = 5):
    """搜索知识库"""
    try:
        rag = get_rag_engine()
        result = rag.retrieve_and_generate(query, top_k=top_k)

        return {
            "status": "success",
            "answer": result["answer"],
            "sources": result["sources"],
            "query": query
        }

    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-lesson")
async def optimize_lesson_plan(request: LessonPlanRequest):
    """优化课程计划"""
    try:
        llm = get_llm_model()

        objectives_str = "\n".join([f"- {obj}" for obj in request.objectives])

        prompt = f"""请帮我优化以下课程计划：

主题：{request.topic}
学生水平：{request.student_level}
课程时长：{request.duration}分钟

原定教学目标：
{objectives_str}

请提供：
1. 优化后的教学目标（更具体、可测量）
2. 建议的教学流程（包含时间分配）
3. 推荐的教学活动
4. 评估方法
5. 可能的教学难点及应对策略

请以JSON格式输出。"""

        response = llm.generate(prompt=prompt)

        # 解析响应
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            optimization_data = json.loads(json_match.group())
            return {
                "status": "success",
                "optimization": optimization_data
            }
        else:
            return {
                "status": "success",
                "optimization": {
                    "message": "优化建议生成完成",
                    "content": response
                }
            }

    except Exception as e:
        logger.error(f"Error optimizing lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teaching-suggestions/{topic}")
async def get_teaching_suggestions(topic: str):
    """获取教学建议"""
    try:
        llm = get_llm_model()

        prompt = f"""针对主题"{topic}"，请提供以下教学建议：

1. 常见的学生误区
2. 推荐的教学方法
3. 实用的课堂活动
4. 相关的实例或案例
5. 扩展学习资源

请用简洁明了的语言，每点2-3句话。"""

        response = llm.generate(prompt=prompt)

        return {
            "status": "success",
            "topic": topic,
            "suggestions": response
        }

    except Exception as e:
        logger.error(f"Error getting teaching suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def get_teacher_courses(
    current_user: User = Depends(require_role([UserRole.TEACHER])),
    db: Session = Depends(get_db)
):
    """获取教师的课程列表"""
    from models.course import Course
    from utils.response import StandardResponse
    
    courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    
    course_list = []
    for course in courses:
        course_list.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "subject": course.subject,
            "grade_level": course.grade_level,
            "student_count": len(course.users),
            "created_at": course.created_at,
            "updated_at": course.updated_at
        })
    
    return StandardResponse.success(
        data=course_list,
        message="课程列表获取成功"
    )