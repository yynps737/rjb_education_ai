"""
智能题目生成器，支持多种题型和认知层次
"""
import json
import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from datetime import datetime

from core.ai.llm_client import get_llm_client, GenerationConfig
from core.ai.config import get_ai_config
logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    # 单选题
    MULTIPLE_CHOICE = "multiple_choice"
    # 多选题
    TRUE_FALSE = "true_false"
    # 判断题
    FILL_BLANK = "fill_blank"
    # 填空题
    SHORT_ANSWER = "short_answer"
    # 简答题
    ESSAY = "essay"
    # 论述题
    CODING = "coding"
    # 编程题
    CALCULATION = "calculation"
    # 计算题
    MATCHING = "matching"
    # 配对题
    ORDERING = "ordering"
    # 排序题

class DifficultyLevel(Enum):
    """难度等级"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class BloomLevel(Enum):
    """布鲁姆认知层次"""
    REMEMBER = "remember"
    # 记忆
    UNDERSTAND = "understand"
    # 理解
    APPLY = "apply"
    # 应用
    ANALYZE = "analyze"
    # 分析
    EVALUATE = "evaluate"
    # 评价
    CREATE = "create"
    # 创造

@dataclass
class Question:
    """题目数据结构"""
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    bloom_level: BloomLevel = BloomLevel.UNDERSTAND
    points: float = 1.0
    time_limit: Optional[int] = None
    # 秒
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class GenerationRequest:
    """题目生成请求"""
    topic: str
    question_type: Optional[QuestionType] = None
    difficulty: Optional[DifficultyLevel] = None
    bloom_level: Optional[BloomLevel] = None
    count: int = 1
    context: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    language: str = "zh"

class QuestionGenerator:
    """题目生成器"""

    def __init__(self, llm_client=None, config=None):
        self.llm_client = llm_client or get_llm_client()
        self.config = config or get_ai_config()
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """加载题目生成模板"""
        return {
            QuestionType.SINGLE_CHOICE: """请基于以下主题生成一道单选题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 题目清晰明确，无歧义
2. 提供4个选项（A、B、C、D）
3. 只有一个正确答案
4. 错误选项要有迷惑性但不能太离谱
5. 提供详细的解析

输出格式：
题目：[题目内容]
A. [选项A]
B. [选项B]
C. [选项C]
D. [选项D]
答案：[正确选项]
解析：[详细解析]""",

            QuestionType.MULTIPLE_CHOICE: """请基于以下主题生成一道多选题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 题目清晰，明确说明是多选题
2. 提供4-5个选项
3. 有2-3个正确答案
4. 选项设计要合理
5. 提供详细解析

输出格式：
题目：[题目内容]（多选）
A. [选项A]
B. [选项B]
C. [选项C]
D. [选项D]
E. [选项E]（可选）
答案：[正确选项，如：ABC]
解析：[详细解析]""",

            QuestionType.TRUE_FALSE: """请基于以下主题生成一道判断题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 陈述要明确，避免模棱两可
2. 涉及重要概念或原理
3. 提供判断依据的解析

输出格式：
题目：[陈述内容]
答案：[正确/错误]
解析：[详细解析]""",

            QuestionType.FILL_BLANK: """请基于以下主题生成一道填空题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 空格位置要合理，考查关键概念
2. 每个空格用____表示
3. 可以有1-3个空格
4. 提供标准答案和解析

输出格式：
题目：[包含____的题目内容]
答案：[按顺序列出每个空的答案]
解析：[详细解析]""",

            QuestionType.SHORT_ANSWER: """请基于以下主题生成一道简答题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 问题明确具体
2. 答案在3-5句话内可以说清楚
3. 提供答题要点和评分标准

输出格式：
题目：[题目内容]
答案要点：
1. [要点1]
2. [要点2]
3. [要点3]
评分标准：[如何评分的说明]""",

            QuestionType.ESSAY: """请基于以下主题生成一道论述题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 题目有深度，需要综合分析
2. 要求学生论述观点并举例
3. 提供答题框架和评分要点

输出格式：
题目：[题目内容]
答题框架：
1. [论点1]
2. [论点2]
3. [论点3]
评分要点：
- [评分点1]
- [评分点2]
- [评分点3]""",

            QuestionType.CODING: """请基于以下主题生成一道编程题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 题目描述清晰，包含输入输出说明
2. 提供测试用例
3. 给出参考解法
4. 说明时间复杂度要求

输出格式：
题目：[题目描述]
输入格式：[输入说明]
输出格式：[输出说明]
示例：
输入：[示例输入]
输出：[示例输出]
参考解法：
```python
[代码]
```
时间复杂度：[要求]""",

            QuestionType.CALCULATION: """请基于以下主题生成一道计算题：
主题：{topic}
难度：{difficulty}
认知层次：{bloom_level}

要求：
1. 数据设置合理
2. 计算过程明确
3. 提供详细解答步骤

输出格式：
题目：[题目内容]
解答：
步骤1：[计算步骤]
步骤2：[计算步骤]
...
答案：[最终答案]""",

            QuestionType.MATCHING: """请基于以下主题生成一道配对题：
主题：{topic}
难度：{difficulty}

要求：
1. 左右两列各4-6项
2. 一一对应关系明确
3. 提供正确配对答案

输出格式：
题目：请将左右两列内容正确配对
左列：
1. [项目1]
2. [项目2]
3. [项目3]
4. [项目4]

右列：
A. [匹配项A]
B. [匹配项B]
C. [匹配项C]
D. [匹配项D]

答案：1-C, 2-A, 3-D, 4-B""",

            QuestionType.ORDERING: """请基于以下主题生成一道排序题：
主题：{topic}
难度：{difficulty}

要求：
1. 提供4-6个需要排序的项目
2. 排序依据明确
3. 给出正确顺序和理由

输出格式：
题目：[排序要求说明]
待排序项：
A. [项目A]
B. [项目B]
C. [项目C]
D. [项目D]

正确顺序：[如：B→D→A→C]
排序理由：[说明排序依据]"""
        }

    def generate_question(self, request: GenerationRequest) -> Question:
        """生成单个题目"""
        # 确定题型
        question_type = request.question_type or random.choice(list(QuestionType))

        # 获取模板
        template = self.templates.get(question_type)
        if not template:
            raise ValueError(f"Unsupported question type: {question_type}")

        # 准备提示词
        prompt = template.format(
            topic=request.topic,
            difficulty=request.difficulty.value if request.difficulty else "medium",
            bloom_level=request.bloom_level.value if request.bloom_level else "understand"
        )

        # 添加上下文
        if request.context:
            prompt = f"参考资料：\n{request.context}\n\n{prompt}"

        # 添加约束
        if request.constraints:
            constraints_str = "\n".join([f"- {k}: {v}" for k, v in request.constraints.items()])
            prompt += f"\n\n额外要求：\n{constraints_str}"

        # 生成题目
        config = GenerationConfig(
            temperature=0.8,
            max_tokens=1000
        )

        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt="你是一位经验丰富的教育专家，擅长设计高质量的考试题目。请严格按照给定的格式生成题目。",
            config=config
        )

        # 解析生成的题目
        return self._parse_question(response.content, question_type, request)

    def _parse_question(self, content: str, question_type: QuestionType, request: GenerationRequest) -> Question:
        """解析生成的题目内容"""
        lines = content.strip().split('\n')
        question_text = ""
        options = []
        correct_answer = None
        explanation = ""

        # 根据题型解析
        if question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
            # 解析选择题
            for line in lines:
                if line.startswith('题目：'):
                    question_text = line.replace('题目：', '').strip()
                elif re.match(r'^[A-E]\.\s', line):
                    options.append(line[3:].strip())
                elif line.startswith('答案：'):
                    correct_answer = line.replace('答案：', '').strip()
                elif line.startswith('解析：'):
                    explanation = line.replace('解析：', '').strip()

        elif question_type == QuestionType.TRUE_FALSE:
            # 解析判断题
            for line in lines:
                if line.startswith('题目：'):
                    question_text = line.replace('题目：', '').strip()
                elif line.startswith('答案：'):
                    answer_text = line.replace('答案：', '').strip()
                    correct_answer = answer_text == "正确"
                elif line.startswith('解析：'):
                    explanation = line.replace('解析：', '').strip()

        elif question_type == QuestionType.FILL_BLANK:
            # 解析填空题
            for line in lines:
                if line.startswith('题目：'):
                    question_text = line.replace('题目：', '').strip()
                elif line.startswith('答案：'):
                    correct_answer = line.replace('答案：', '').strip().split('，')
                elif line.startswith('解析：'):
                    explanation = line.replace('解析：', '').strip()

        else:
            # 其他题型的通用解析
            question_text = content.split('\n')[0].replace('题目：', '').strip()
            correct_answer = content
            # 保存完整内容作为答案

        # 创建题目对象
        return Question(
            question_text=question_text,
            question_type=question_type,
            options=options if options else None,
            correct_answer=correct_answer,
            explanation=explanation,
            difficulty=request.difficulty or DifficultyLevel.MEDIUM,
            bloom_level=request.bloom_level or BloomLevel.UNDERSTAND,
            tags=[request.topic],
            metadata={
                "generated_at": datetime.now().isoformat(),
                "language": request.language
            }
        )

    def generate_batch(self, request: GenerationRequest) -> List[Question]:
        """批量生成题目"""
        questions = []

        for i in range(request.count):
            try:
                # 为每个题目随机选择不同的类型（如果未指定）
                if not request.question_type:
                    request.question_type = random.choice(list(QuestionType))

                question = self.generate_question(request)
                questions.append(question)

                logger.info(f"Generated question {i+1}/{request.count}")

            except Exception as e:
                logger.error(f"Failed to generate question {i+1}: {e}")

        return questions

    def generate_quiz(
        self,
        topic: str,
        total_points: int = 100,
        time_limit: int = 3600,
        # 秒
        distribution: Optional[Dict[QuestionType, int]] = None
    ) -> Dict[str, Any]:
        """生成完整的测验"""
        if not distribution:
            # 默认题型分布
            distribution = {
                QuestionType.SINGLE_CHOICE: 10,
                QuestionType.MULTIPLE_CHOICE: 5,
                QuestionType.TRUE_FALSE: 5,
                QuestionType.FILL_BLANK: 5,
                QuestionType.SHORT_ANSWER: 3,
                QuestionType.ESSAY: 2
            }

        questions = []
        total_questions = sum(distribution.values())
        points_per_question = total_points / total_questions

        # 按题型生成题目
        for question_type, count in distribution.items():
            request = GenerationRequest(
                topic=topic,
                question_type=question_type,
                count=count
            )

            batch = self.generate_batch(request)

            # 分配分值
            for q in batch:
                if question_type in [QuestionType.ESSAY, QuestionType.SHORT_ANSWER]:
                    q.points = points_per_question * 2
                    # 主观题分值更高
                else:
                    q.points = points_per_question

            questions.extend(batch)

        # 调整总分
        actual_total = sum(q.points for q in questions)
        if actual_total != total_points:
            factor = total_points / actual_total
            for q in questions:
                q.points *= factor

        return {
            "title": f"{topic} 测验",
            "topic": topic,
            "total_points": total_points,
            "time_limit": time_limit,
            "questions": questions,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "question_count": len(questions),
                "distribution": {k.value: v for k, v in distribution.items()}
            }
        }

    def generate_adaptive_question(
        self,
        topic: str,
        student_performance: Dict[str, Any],
        previous_questions: List[Question]
    ) -> Question:
        """基于学生表现生成自适应题目"""
        # 分析学生表现
        avg_score = student_performance.get("avg_score", 0.5)
        weak_areas = student_performance.get("weak_areas", [])
        strong_areas = student_performance.get("strong_areas", [])

        # 确定难度
        if avg_score > 0.8:
            difficulty = DifficultyLevel.HARD
            bloom_level = BloomLevel.ANALYZE
        elif avg_score > 0.6:
            difficulty = DifficultyLevel.MEDIUM
            bloom_level = BloomLevel.APPLY
        else:
            difficulty = DifficultyLevel.EASY
            bloom_level = BloomLevel.UNDERSTAND

        # 确定题型
        # 避免重复最近的题型
        recent_types = [q.question_type for q in previous_questions[-3:]]
        available_types = [t for t in QuestionType if t not in recent_types]
        question_type = random.choice(available_types) if available_types else random.choice(list(QuestionType))

        # 生成题目
        request = GenerationRequest(
            topic=topic,
            question_type=question_type,
            difficulty=difficulty,
            bloom_level=bloom_level,
            constraints={
                "focus_on_weak_areas": weak_areas,
                "avoid_topics": strong_areas
            }
        )

        return self.generate_question(request)

    def export_questions(self, questions: List[Question], format: str = "json") -> str:
        """导出题目"""
        if format == "json":
            data = []
            for q in questions:
                data.append({
                    "question_text": q.question_text,
                    "question_type": q.question_type.value,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty.value,
                    "bloom_level": q.bloom_level.value,
                    "points": q.points,
                    "tags": q.tags,
                    "metadata": q.metadata
                })
            return json.dumps(data, ensure_ascii=False, indent=2)

        elif format == "markdown":
            md_content = []
            for i, q in enumerate(questions, 1):
                md_content.append(f"## {i}. {q.question_text}")
                md_content.append(f"**类型**: {q.question_type.value}")
                md_content.append(f"**难度**: {q.difficulty.value}")
                md_content.append(f"**分值**: {q.points}")

                if q.options:
                    md_content.append("\n**选项**:")
                    for j, opt in enumerate(q.options):
                        md_content.append(f"{chr(65+j)}. {opt}")

                md_content.append(f"\n**答案**: {q.correct_answer}")

                if q.explanation:
                    md_content.append(f"\n**解析**: {q.explanation}")

                md_content.append("\n---\n")

            return "\n".join(md_content)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def validate_question(self, question: Question) -> Tuple[bool, List[str]]:
        """验证题目质量"""
        errors = []

        # 基本验证
        if not question.question_text:
            errors.append("题目文本不能为空")

        if len(question.question_text) < 10:
            errors.append("题目文本过短")

        # 根据题型验证
        if question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
            if not question.options or len(question.options) < 2:
                errors.append("选择题至少需要2个选项")

            if not question.correct_answer:
                errors.append("选择题必须有正确答案")

        elif question.question_type == QuestionType.TRUE_FALSE:
            if question.correct_answer not in [True, False]:
                errors.append("判断题答案必须是True或False")

        elif question.question_type == QuestionType.FILL_BLANK:
            if "____" not in question.question_text:
                errors.append("填空题必须包含空格标记(____)")

        # 验证分值
        if question.points <= 0:
            errors.append("题目分值必须大于0")

        return len(errors) == 0, errors

# 创建全局实例
_generator_instance: Optional[QuestionGenerator] = None

def get_question_generator() -> QuestionGenerator:
    """获取题目生成器单例"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = QuestionGenerator()
    return _generator_instance