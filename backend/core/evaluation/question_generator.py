"""
简化的题目生成器
"""
from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass
import logging
import json
import re

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    CODING = "coding"


@dataclass
class Question:
    """题目数据类"""
    type: QuestionType
    content: str
    options: List[str] = None
    answer: Any = None
    explanation: str = None
    difficulty: int = 3
    score: float = 10.0
    knowledge_points: List[str] = None


class QuestionGenerator:
    """题目生成器"""

    def __init__(self):
        """初始化题目生成器"""
        logger.info("题目生成器初始化")
        self.llm_client = None

    def _get_llm_client(self):
        """获取LLM客户端"""
        if self.llm_client is None:
            from core.llm.qwen_client import get_qwen_client
            self.llm_client = get_qwen_client()
        return self.llm_client

    def generate_questions(
        self,
        knowledge_content: str,
        question_types: List[QuestionType],
        num_questions: int = 5,
        difficulty: int = 3
    ) -> List[Question]:
        """生成题目"""
        questions = []
        
        # 如果使用LLM生成
        try:
            llm = self._get_llm_client()
            
            # 构建题型说明
            type_descriptions = {
                QuestionType.SINGLE_CHOICE: "单选题（4个选项，只有一个正确答案）",
                QuestionType.MULTIPLE_CHOICE: "多选题（4个选项，有多个正确答案）",
                QuestionType.TRUE_FALSE: "判断题（正确或错误）",
                QuestionType.SHORT_ANSWER: "简答题（需要简短文字回答）",
                QuestionType.CODING: "编程题（需要编写代码）"
            }
            
            types_str = ", ".join([type_descriptions.get(qt, qt.value) for qt in question_types])
            
            prompt = f"""基于以下知识内容生成{num_questions}道题目：

知识内容：{knowledge_content}

要求：
1. 题型包括：{types_str}
2. 难度等级：{difficulty}/5
3. 每道题都要有明确的答案和解析
4. 题目要有层次，考察不同的知识点

请以JSON格式输出，格式如下：
{{
    "questions": [
        {{
            "type": "题型",
            "content": "题目内容",
            "options": ["选项A", "选项B", "选项C", "选项D"],  // 仅选择题需要
            "answer": "答案",
            "explanation": "解析说明"
        }}
    ]
}}"""
            
            response = llm.generate(prompt)
            
            # 解析JSON响应
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for q_data in data.get("questions", []):
                    # 匹配题型
                    q_type = None
                    for qt in QuestionType:
                        if qt.value in q_data.get("type", "") or q_data.get("type", "") in qt.value:
                            q_type = qt
                            break
                    
                    if q_type:
                        question = Question(
                            type=q_type,
                            content=q_data.get("content", ""),
                            options=q_data.get("options"),
                            answer=q_data.get("answer", ""),
                            explanation=q_data.get("explanation", ""),
                            difficulty=difficulty,
                            score=self._get_score_by_type(q_type),
                            knowledge_points=[knowledge_content[:50]]
                        )
                        questions.append(question)
                
                # 如果生成的题目不够，补充默认题目
                if len(questions) < num_questions:
                    questions.extend(self._generate_default_questions(
                        knowledge_content, 
                        question_types, 
                        num_questions - len(questions), 
                        difficulty
                    ))
                
                return questions[:num_questions]
                
        except Exception as e:
            logger.error(f"LLM生成题目失败: {e}")
        
        # 如果LLM生成失败，使用默认生成
        return self._generate_default_questions(knowledge_content, question_types, num_questions, difficulty)
    
    def _generate_default_questions(
        self,
        knowledge_content: str,
        question_types: List[QuestionType],
        num_questions: int,
        difficulty: int
    ) -> List[Question]:
        """生成默认题目"""
        questions = []
        
        for i in range(num_questions):
            q_type = question_types[i % len(question_types)]

            if q_type == QuestionType.SINGLE_CHOICE:
                question = Question(
                    type=q_type,
                    content=f"关于{knowledge_content[:30]}...的问题：以下哪个说法是正确的？",
                    options=["选项A：正确说法", "选项B：错误说法1", "选项C：错误说法2", "选项D：错误说法3"],
                    answer="A",
                    explanation="选项A是正确的，因为它准确描述了相关概念。",
                    difficulty=difficulty,
                    score=10.0,
                    knowledge_points=[knowledge_content[:50]]
                )
            elif q_type == QuestionType.TRUE_FALSE:
                question = Question(
                    type=q_type,
                    content=f"判断题：{knowledge_content[:50]}...这个说法是否正确？",
                    answer=True,
                    explanation="这个说法是正确的，符合基本概念。",
                    difficulty=difficulty,
                    score=5.0,
                    knowledge_points=[knowledge_content[:50]]
                )
            elif q_type == QuestionType.SHORT_ANSWER:
                question = Question(
                    type=q_type,
                    content=f"请简述{knowledge_content[:30]}...的主要特点。",
                    answer="主要特点包括：1) 特点一 2) 特点二 3) 特点三",
                    explanation="答案应包含主要特点的准确描述。",
                    difficulty=difficulty,
                    score=15.0,
                    knowledge_points=[knowledge_content[:50]]
                )
            elif q_type == QuestionType.CODING:
                question = Question(
                    type=q_type,
                    content=f"编写代码实现与{knowledge_content[:30]}...相关的功能。",
                    answer="def example():\n    # 示例代码\n    pass",
                    explanation="代码应该正确实现所要求的功能。",
                    difficulty=difficulty,
                    score=20.0,
                    knowledge_points=[knowledge_content[:50]]
                )
            else:
                question = Question(
                    type=q_type,
                    content=f"关于{knowledge_content[:30]}...的{q_type.value}题目",
                    answer="示例答案",
                    explanation="这是解析说明",
                    difficulty=difficulty,
                    score=10.0,
                    knowledge_points=[knowledge_content[:50]]
                )

            questions.append(question)

        return questions
    
    def _get_score_by_type(self, q_type: QuestionType) -> float:
        """根据题型获取分值"""
        score_map = {
            QuestionType.SINGLE_CHOICE: 10.0,
            QuestionType.MULTIPLE_CHOICE: 15.0,
            QuestionType.TRUE_FALSE: 5.0,
            QuestionType.FILL_BLANK: 10.0,
            QuestionType.SHORT_ANSWER: 15.0,
            QuestionType.CODING: 20.0
        }
        return score_map.get(q_type, 10.0)