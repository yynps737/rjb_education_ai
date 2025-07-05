from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models.assignment import Submission, Answer, Question, QuestionType
from core.ai.auto_grader import AutoGrader

class GradingService:
    def __init__(self):
        self.auto_grader = AutoGrader()

    async def grade_submission(
        self,
        db: Session,
        submission_id: int,
        manual_grades: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> Submission:
        """
        评分提交（自动 + 手动）
        manual_grades: {question_id: {"score": float, "feedback": str}}
        """
        # 获取包含答案和问题的提交
        submission = db.query(Submission).filter(
            Submission.id == submission_id
        ).first()

        if not submission:
            raise ValueError("提交未找到")

        total_score = 0
        total_points = 0

        # 评分每个答案
        for answer in submission.answers:
            question = answer.question
            total_points += question.points

            # 检查是否提供手动评分
            if manual_grades and answer.question_id in manual_grades:
                manual = manual_grades[answer.question_id]
                answer.score = manual["score"]
                answer.feedback = manual["feedback"]
                answer.auto_graded = 0
            else:
                # 如果可能的话自动评分
                if question.question_type in [
                    QuestionType.SINGLE_CHOICE,
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.TRUE_FALSE,
                    QuestionType.FILL_BLANK
                ]:
                    # 客观题
                    result = await self.auto_grader.grade_objective_question(
                        question_type=question.question_type.value,
                        student_answer=answer.content,
                        correct_answer=question.correct_answer
                    )

                    answer.score = result["score"] * question.points
                    answer.feedback = result.get("feedback", "")
                    answer.auto_graded = 1

                elif question.question_type in [
                    QuestionType.SHORT_ANSWER,
                    QuestionType.ESSAY
                ]:
                    # 主观题
                    result = await self.auto_grader.grade_subjective_question(
                        question=question.content,
                        student_answer=answer.content,
                        reference_answer=question.correct_answer,
                        grading_criteria=question.grading_criteria
                    )

                    answer.score = result["score"] * question.points / 10
                    # 转换为分数
                    answer.feedback = result.get("feedback", "")
                    answer.auto_graded = 1

                elif question.question_type == QuestionType.CODING:
                    # 编程题
                    result = await self.auto_grader.grade_code_question(
                        question=question.content,
                        student_code=answer.content,
                        test_cases=question.test_cases or [],
                        language="python"
                        # 默认为Python
                    )

                    answer.score = result["score"] * question.points / 100
                    # 转换百分比
                    answer.feedback = self._format_code_feedback(result)
                    answer.auto_graded = 1
                else:
                    # 未知类型，需要手动评分
                    answer.score = 0
                    answer.feedback = "需要手动评分"
                    answer.auto_graded = 0

            total_score += answer.score or 0

        # 更新提交
        submission.score = total_score
        submission.status = "graded"
        submission.feedback = f"总分: {total_score:.1f}/{total_points:.1f}"

        db.commit()
        db.refresh(submission)

        return submission

    def _format_code_feedback(self, result: Dict[str, Any]) -> str:
        """格式化代码评分反馈"""
        feedback_parts = []

        if result.get("test_results"):
            passed = sum(1 for t in result["test_results"] if t["passed"])
            total = len(result["test_results"])
            feedback_parts.append(f"测试: {passed}/{total} 通过")

        if result.get("error_analysis"):
            feedback_parts.append(f"错误: {result['error_analysis']}")

        if result.get("code_quality"):
            feedback_parts.append(f"代码质量: {result['code_quality']}")

        if result.get("suggestions"):
            feedback_parts.append(f"建议: {', '.join(result['suggestions'])}")

        return "\n".join(feedback_parts)

    def get_submission_details(
        self,
        db: Session,
        submission_id: int
    ) -> Dict[str, Any]:
        """获取包含答案和分数的详细提交信息"""
        submission = db.query(Submission).filter(
            Submission.id == submission_id
        ).first()

        if not submission:
            return None

        return {
            "id": submission.id,
            "student": {
                "id": submission.student.id,
                "name": submission.student.full_name,
                "username": submission.student.username
            },
            "assignment": {
                "id": submission.assignment.id,
                "title": submission.assignment.title
            },
            "submitted_at": submission.submitted_at,
            "score": submission.score,
            "status": submission.status,
            "answers": [
                {
                    "question_id": answer.question_id,
                    "question_content": answer.question.content,
                    "question_type": answer.question.question_type.value,
                    "student_answer": answer.content,
                    "correct_answer": answer.question.correct_answer,
                    "score": answer.score,
                    "max_score": answer.question.points,
                    "feedback": answer.feedback,
                    "auto_graded": bool(answer.auto_graded)
                }
                for answer in submission.answers
            ]
        }

grading_service = GradingService()