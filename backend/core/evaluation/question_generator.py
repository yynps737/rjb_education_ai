"""
简化的题目生成器
"""
from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

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

    def generate_questions(
        self,
        knowledge_content: str,
        question_types: List[QuestionType],
        num_questions: int = 5,
        difficulty: int = 3
    ) -> List[Question]:
        """生成题目"""
        questions = []

        # 简单的示例实现
        for i in range(num_questions):
            q_type = question_types[i % len(question_types)]

            if q_type == QuestionType.SINGLE_CHOICE:
                question = Question(
                    type=q_type,
                    content=f"关于{knowledge_content}的选择题{i+1}",
                    options=["选项A", "选项B", "选项C", "选项D"],
                    answer="A",
                    explanation="这是解析",
                    difficulty=difficulty,
                    score=10.0,
                    knowledge_points=[knowledge_content]
                )
            elif q_type == QuestionType.TRUE_FALSE:
                question = Question(
                    type=q_type,
                    content=f"判断题：{knowledge_content}相关陈述{i+1}",
                    answer=True,
                    explanation="这是解析",
                    difficulty=difficulty,
                    score=5.0,
                    knowledge_points=[knowledge_content]
                )
            else:
                question = Question(
                    type=q_type,
                    content=f"关于{knowledge_content}的{q_type.value}题目{i+1}",
                    answer="示例答案",
                    explanation="这是解析",
                    difficulty=difficulty,
                    score=15.0,
                    knowledge_points=[knowledge_content]
                )

            questions.append(question)

        return questions