from celery import shared_task, group
from typing import Dict, Any, List
import logging
from datetime import datetime

from models.database import get_db_session
from models.assignment import Submission, Assignment, AssignmentStatus
from services.grading_service import grading_service

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def grade_submission_async(self, submission_id: int) -> Dict[str, Any]:
    """
    Asynchronously grade a submission
    """
    try:
        with get_db_session() as db:
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()

            if not submission:
                return {"status": "error", "message": "Submission not found"}

            logger.info(f"Grading submission {submission_id}")

            # Grade submission
            graded_submission = grading_service.grade_submission(
                db,
                submission_id
            )

            # 发送 通知
            from tasks.notifications import send_grade_notification
            send_grade_notification.delay(
                student_id=submission.student_id,
                assignment_id=submission.assignment_id,
                score=graded_submission.score
            )

            return {
                "status": "success",
                "submission_id": submission_id,
                "score": graded_submission.score,
                "status": graded_submission.status
            }

    except Exception as e:
        logger.error(f"Error grading submission {submission_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@shared_task
def batch_grade_assignments(assignment_id: int) -> Dict[str, Any]:
    """
    Grade all submissions for an assignment
    """
    try:
        with get_db_session() as db:
            # 获取 全部 ungraded submissions
            submissions = db.query(Submission).filter(
                Submission.assignment_id == assignment_id,
                Submission.status != "graded"
            ).all()

            if not submissions:
                return {
                    "status": "success",
                    "message": "No submissions to grade",
                    "graded_count": 0
                }

            # 创建 分组 of 评分 tasks
            job = group(
                grade_submission_async.s(submission.id)
                for submission in submissions
            )

            # Execute 全部 tasks
            result = job.apply_async()

            return {
                "status": "success",
                "submissions_queued": len(submissions),
                "group_id": result.id
            }

    except Exception as e:
        logger.error(f"Error batch grading assignment {assignment_id}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@shared_task
def auto_grade_on_deadline() -> Dict[str, Any]:
    """
    Automatically grade assignments when deadline passes
    """
    try:
        with get_db_session() as db:
            # Find assignments with passed deadlines
            now = datetime.utcnow()

            overdue_assignments = db.query(Assignment).filter(
                Assignment.status == AssignmentStatus.PUBLISHED,
                Assignment.due_date < now
            ).all()

            graded_assignments = []

            for assignment in overdue_assignments:
                # 检查 for ungraded submissions
                ungraded = db.query(Submission).filter(
                    Submission.assignment_id == assignment.id,
                    Submission.status != "graded"
                ).count()

                if ungraded > 0:
                    # 队列 batch 评分
                    batch_grade_assignments.delay(assignment.id)
                    graded_assignments.append(assignment.id)

                # Close 作业
                assignment.status = AssignmentStatus.CLOSED

            db.commit()

            return {
                "status": "success",
                "assignments_processed": len(overdue_assignments),
                "grading_queued_for": graded_assignments
            }

    except Exception as e:
        logger.error(f"Error in auto grade on deadline: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@shared_task
def calculate_class_statistics(assignment_id: int) -> Dict[str, Any]:
    """
    Calculate statistics for an assignment after grading
    """
    try:
        with get_db_session() as db:
            # 获取 全部 graded submissions
            submissions = db.query(Submission).filter(
                Submission.assignment_id == assignment_id,
                Submission.status == "graded",
                Submission.score.isnot(None)
            ).all()

            if not submissions:
                return {
                    "status": "success",
                    "statistics": {
                        "submissions": 0,
                        "average": 0,
                        "min": 0,
                        "max": 0
                    }
                }

            scores = [s.score for s in submissions]

            statistics = {
                "submissions": len(submissions),
                "average": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "median": sorted(scores)[len(scores) // 2],
                "std_dev": None  # Would calculate if needed
            }

            # Store in performance metrics
            from models.analytics import PerformanceMetrics
            from models.assignment import Assignment

            assignment = db.query(Assignment).filter(
                Assignment.id == assignment_id
            ).first()

            if assignment:
                metric = PerformanceMetrics(
                    user_id=assignment.course.teacher_id,
                    course_id=assignment.course_id,
                    metric_type="assignment_statistics",
                    value=statistics["average"],
                    metadata=statistics,
                    recorded_at=datetime.utcnow()
                )
                db.add(metric)
                db.commit()

            return {
                "status": "success",
                "assignment_id": assignment_id,
                "statistics": statistics
            }

    except Exception as e:
        logger.error(f"Error calculating statistics for assignment {assignment_id}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }