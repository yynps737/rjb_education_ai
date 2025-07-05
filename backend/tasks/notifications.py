from celery import shared_task
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from models.database import get_db_session
from models.user import User
from models.assignment import Assignment, AssignmentStatus, Submission
from models.course import Course

logger = logging.getLogger(__name__)

# In a real 实现, these would 发送 actual emails/notifications
# For now, we'll just log and store in a notifications 表
@shared_task
def send_assignment_reminder(
    student_id: int,
    assignment_id: int,
    days_until_due: int
) -> Dict[str, Any]:
    """
    Send assignment deadline reminder to student
    """
    try:
        with get_db_session() as db:
            student = db.query(User).filter(User.id == student_id).first()
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

            if not student or not assignment:
                return {"status": "error", "message": "Student or assignment not found"}

            # 检查 if already submitted
            submission = db.query(Submission).filter(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id
            ).first()

            if submission:
                return {"status": "skipped", "message": "Assignment already submitted"}

            # 创建 通知 消息
            message = f"Reminder: Assignment '{assignment.title}' is due in {days_until_due} days"

            # In real 实现, 发送 邮箱/push 通知
            logger.info(f"Sending reminder to {student.email}: {message}")

            # Log 通知 (could store in a notifications 表)
            return {
                "status": "success",
                "recipient": student.email,
                "assignment": assignment.title,
                "days_until_due": days_until_due
            }

    except Exception as e:
        logger.error(f"Error sending assignment reminder: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def send_grade_notification(
    student_id: int,
    assignment_id: int,
    score: float
) -> Dict[str, Any]:
    """
    Notify student when assignment is graded
    """
    try:
        with get_db_session() as db:
            student = db.query(User).filter(User.id == student_id).first()
            assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

            if not student or not assignment:
                return {"status": "error", "message": "Student or assignment not found"}

            # 创建 通知 消息
            percentage = (score / assignment.total_points) * 100 if assignment.total_points > 0 else 0
            message = (f"Your assignment '{assignment.title}' has been graded. "
                       f"Score: {score:.1f}/{assignment.total_points} ({percentage:.1f}%)")

            # In real 实现, 发送 邮箱/push 通知
            logger.info(f"Sending grade notification to {student.email}: {message}")

            return {
                "status": "success",
                "recipient": student.email,
                "assignment": assignment.title,
                "score": score,
                "percentage": percentage
            }

    except Exception as e:
        logger.error(f"Error sending grade notification: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def check_assignment_deadlines() -> Dict[str, Any]:
    """
    Check for upcoming assignment deadlines and send reminders
    """
    try:
        with get_db_session() as db:
            # 检查 assignments due in 1, 3, and 7 days
            reminder_days = [1, 3, 7]
            reminders_sent = 0

            for days in reminder_days:
                deadline_date = datetime.utcnow().date() + timedelta(days=days)

                # Find assignments due on that date
                assignments = db.query(Assignment).filter(
                    Assignment.status == AssignmentStatus.PUBLISHED,
                    func.date(Assignment.due_date) == deadline_date
                ).all()

                for assignment in assignments:
                    # 获取 students who haven't submitted
                    enrolled_students = assignment.course.users

                    for student in enrolled_students:
                        if student.role.value != "student":
                            continue

                        # 检查 if already submitted
                        submission = db.query(Submission).filter(
                            Submission.assignment_id == assignment.id,
                            Submission.student_id == student.id
                        ).first()

                        if not submission:
                            # 发送 reminder
                            send_assignment_reminder.delay(
                                student_id=student.id,
                                assignment_id=assignment.id,
                                days_until_due=days
                            )
                            reminders_sent += 1

            return {
                "status": "success",
                "reminders_queued": reminders_sent
            }

    except Exception as e:
        logger.error(f"Error checking assignment deadlines: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def send_course_announcement(
    course_id: int,
    title: str,
    message: str
) -> Dict[str, Any]:
    """
    Send announcement to all students in a course
    """
    try:
        with get_db_session() as db:
            course = db.query(Course).filter(Course.id == course_id).first()

            if not course:
                return {"status": "error", "message": "Course not found"}

            # 获取 全部 enrolled students
            students = [u for u in course.users if u.role.value == "student"]

            notifications_sent = 0
            for student in students:
                # In real 实现, 发送 邮箱/push 通知
                logger.info(f"Sending announcement to {student.email}: {title}")
                notifications_sent += 1

            return {
                "status": "success",
                "course": course.title,
                "recipients": notifications_sent,
                "title": title
            }

    except Exception as e:
        logger.error(f"Error sending course announcement: {str(e)}")
        return {"status": "error", "message": str(e)}

@shared_task
def notify_low_performance(threshold: float = 60.0) -> Dict[str, Any]:
    """
    Notify students with low performance
    """
    try:
        with get_db_session() as db:
            # Find students with recent low scores
            week_ago = datetime.utcnow() - timedelta(days=7)

            low_performers = db.query(
                User.id,
                User.email,
                func.avg(Submission.score).label('avg_score')
            ).join(
                Submission
            ).filter(
                User.role.value == "student",
                Submission.submitted_at >= week_ago,
                Submission.score.isnot(None)
            ).group_by(
                User.id, User.email
            ).having(
                func.avg(Submission.score) < threshold
            ).all()

            notifications_sent = 0

            for student_id, email, avg_score in low_performers:
                message = (f"Your recent average score is {avg_score:.1f}%. "
                           f"Consider reviewing course materials or reaching out to your teacher for help.")

                # In real 实现, 发送 邮箱/push 通知
                logger.info(f"Sending performance alert to {email}: {message}")
                notifications_sent += 1

            return {
                "status": "success",
                "students_notified": notifications_sent,
                "threshold": threshold
            }

    except Exception as e:
        logger.error(f"Error notifying low performers: {str(e)}")
        return {"status": "error", "message": str(e)}