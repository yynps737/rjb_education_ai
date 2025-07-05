
import httpx
from typing import Dict, List
from core.config import settings

class AIService:
    """AI服务 - 使用DeepSeek API"""

    def __init__(self):
        self.api_key = settings.deepseek_api_key.get_secret_value() if settings.deepseek_api_key else None
        self.base_url = settings.deepseek_base_url
        self.client = httpx.Client(timeout=30.0)

    async def generate_course_outline(self, subject: str, grade_level: str,
                                    duration_weeks: int) -> Dict:
        """生成课程大纲"""
        prompt = f"""
        请为{grade_level}年级的{subject}课程生成一个{duration_weeks}周的课程大纲。
        包括：
        1. 课程目标
        2. 每周主题
        3. 关键知识点
        4. 建议的作业

        请以JSON格式返回。
        """

        response = await self._call_api(prompt)
        return {"outline": response}

    async def grade_assignment(self, assignment_text: str, rubric: str) -> Dict:
        """AI自动评分"""
        prompt = f"""
        请根据以下评分标准对学生作业进行评分：

        评分标准：
        {rubric}

        学生作业：
        {assignment_text}

        请给出：
        1. 分数（0-100）
        2. 详细反馈
        3. 改进建议
        """

        response = await self._call_api(prompt)
        return {"grading": response}

    async def answer_question(self, question: str, context: str = "") -> str:
        """回答学生问题"""
        prompt = f"""
        学生问题：{question}

        相关背景：{context}

        请提供清晰、准确、适合学生理解的答案。
        """

        return await self._call_api(prompt)

    async def _call_api(self, prompt: str) -> str:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的教育AI助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI服务暂时不可用: {str(e)}"

ai_service = AIService()
