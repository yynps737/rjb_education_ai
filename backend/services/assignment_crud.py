
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from models.assignment import Assignment, Submission

class AssignmentService:
    """作业管理服务"""

    def create_assignment(self, db: Session, course_id: int, title: str,
                         description: str, due_date: datetime, total_points: int) -> Assignment:
        """创建作业"""
        assignment = Assignment(
            course_id=course_id,
            title=title,
            description=description,
            due_date=due_date,
            total_points=total_points,
            created_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def submit_assignment(self, db: Session, assignment_id: int, student_id: int,
                         content: str, file_url: Optional[str] = None) -> Submission:
        """提交作业"""
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            file_url=file_url,
            submitted_at=datetime.utcnow(),
            status="submitted"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    def grade_submission(self, db: Session, submission_id: int,
                        grade: float, feedback: str) -> Optional[Submission]:
        """评分"""
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.grade = grade
            submission.feedback = feedback
            submission.graded_at = datetime.utcnow()
            submission.status = "graded"
            db.commit()
            db.refresh(submission)
        return submission

assignment_service = AssignmentService()
