"""
Auto grader using DeepSeek API
"""
from typing import Dict, List, Any
import json
from core.llm.qwen_client import QwenClient

class AutoGrader:
    """Automated grading system using DeepSeek API"""

    def __init__(self):
        self.llm_client = QwenClient()

    async def grade_assignment(
        self,
        submission: str,
        assignment_type: str,
        grading_criteria: Dict[str, Any],
        reference_answer: str = None
    ) -> Dict[str, Any]:
        """
        Grade a student submission using AI

        Args:
            submission: Student's submitted answer
            assignment_type: Type of assignment (essay, code, math, etc.)
            grading_criteria: Criteria for grading
            reference_answer: Optional reference answer

        Returns:
            Grading result with score and feedback
        """
        # 构建评分prompt
        prompt = self._build_grading_prompt(
            submission, assignment_type, grading_criteria, reference_answer
        )

        # 调用AI进行评分
        response = await self.llm_client.generate(
            prompt,
            temperature=0.3,
            # 低温度以保证评分一致性
            max_tokens=1000
        )

        # 解析评分结果
        return self._parse_grading_result(response)

    def _build_grading_prompt(
        self,
        submission: str,
        assignment_type: str,
        criteria: Dict[str, Any],
        reference: str = None
    ) -> str:
        """构建评分prompt"""
        prompt = f"""作为一位专业的教师，请对以下{assignment_type}作业进行评分。

学生提交的答案：
{submission}

评分标准：
"""

        for criterion, weight in criteria.items():
            prompt += f"- {criterion}（权重：{weight}%）\n"

        if reference:
            prompt += f"\n参考答案：\n{reference}\n"

        prompt += """
请按照以下格式返回评分结果：
{
    "total_score": <总分0-100>,
    "criteria_scores": {
        "<标准名>": {"score": <分数>, "feedback": "<反馈>"},
        ...
    },
    "overall_feedback": "<总体反馈>",
    "strengths": ["<优点1>", "<优点2>", ...],
    "improvements": ["<改进建议1>", "<改进建议2>", ...]
}
"""
        return prompt

    def _parse_grading_result(self, response: str) -> Dict[str, Any]:
        """解析AI返回的评分结果"""
        try:
            # 尝试解析JSON格式的响应
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结果
            return {
                "total_score": 0,
                "criteria_scores": {},
                "overall_feedback": response,
                "strengths": [],
                "improvements": [],
                "error": "Failed to parse grading result"
            }

    async def grade_batch(
        self,
        submissions: List[Dict[str, Any]],
        assignment_type: str,
        grading_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """批量评分"""
        results = []
        for submission in submissions:
            result = await self.grade_assignment(
                submission['content'],
                assignment_type,
                grading_criteria,
                submission.get('reference_answer')
            )
            result['submission_id'] = submission.get('id')
            results.append(result)
        return results