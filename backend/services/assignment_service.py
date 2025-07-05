from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from services.base import BaseService
from models.assignment import Assignment, Question, Submission, Answer, AssignmentStatus, QuestionType
from models.user import User, UserRole

class AssignmentService(BaseService[Assignment]):
    def __init__(self):
        super().__init__(Assignment)

    def create_assignment(
        self,
        db: Session,
        title: str,
        course_id: int,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        instructions: Optional[str] = None
    ) -> Assignment:
        """Create a new assignment"""
        return self.create(
            db,
            title=title,
            course_id=course_id,
            description=description,
            due_date=due_date,
            instructions=instructions
        )

    def add_question(
        self,
        db: Session,
        assignment_id: int,
        question_type: QuestionType,
        content: str,
        points: float = 10,
        options: Optional[List[str]] = None,
        correct_answer: Optional[Any] = None,
        explanation: Optional[str] = None,
        grading_criteria: Optional[Dict] = None,
        test_cases: Optional[List[Dict]] = None
    ) -> Question:
        """Add a question to an assignment"""
        assignment = self.get(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # 获取 the 下一个 order number
        max_order = db.query(Question).filter(
            Question.assignment_id == assignment_id
        ).count()

        question = Question(
            assignment_id=assignment_id,
            question_type=question_type,
            content=content,
            points=points,
            order=max_order + 1,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            grading_criteria=grading_criteria,
            test_cases=test_cases
        )

        db.add(question)
        db.commit()
        db.refresh(question)

        # 更新 作业 总计 points
        total_points = db.query(Question).filter(
            Question.assignment_id == assignment_id
        ).with_entities(db.func.sum(Question.points)).scalar() or 0

        assignment.total_points = total_points
        db.commit()

        return question

    def publish_assignment(self, db: Session, assignment_id: int) -> Assignment:
        """Publish an assignment"""
        assignment = self.get(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if not assignment.questions:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish assignment without questions"
            )

        assignment.status = AssignmentStatus.PUBLISHED
        db.commit()
        db.refresh(assignment)

        return assignment

    def get_assignment_with_questions(
        self,
        db: Session,
        assignment_id: int
    ) -> Optional[Assignment]:
        """Get assignment with all questions"""
        return db.query(Assignment).options(
            joinedload(Assignment.questions)
        ).filter(Assignment.id == assignment_id).first()

    def submit_assignment(
        self,
        db: Session,
        assignment_id: int,
        student_id: int,
        answers: List[Dict[str, Any]]
    ) -> Submission:
        """Submit an assignment"""
        # 检查 if 作业 exists and is published
        assignment = self.get(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if assignment.status != AssignmentStatus.PUBLISHED:
            raise HTTPException(
                status_code=400,
                detail="Assignment is not available for submission"
            )

        # 检查 if student already submitted
        existing = db.query(Submission).filter(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="You have already submitted this assignment"
            )

        # 创建 submission
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student_id,
            submitted_at=datetime.utcnow(),
            status="submitted"
        )

        db.add(submission)
        db.flush()
        # 获取 submission ID

        # 创建 answers
        for answer_data in answers:
            answer = Answer(
                submission_id=submission.id,
                question_id=answer_data["question_id"],
                content=answer_data["content"]
            )
            db.add(answer)

        db.commit()
        db.refresh(submission)

        return submission

    def get_student_submissions(
        self,
        db: Session,
        student_id: int,
        course_id: Optional[int] = None
    ) -> List[Submission]:
        """Get all submissions by a student"""
        query = db.query(Submission).filter(Submission.student_id == student_id)

        if course_id:
            query = query.join(Assignment).filter(Assignment.course_id == course_id)

        return query.all()

    def get_assignment_submissions(
        self,
        db: Session,
        assignment_id: int
    ) -> List[Submission]:
        """Get all submissions for an assignment"""
        return db.query(Submission).options(
            joinedload(Submission.student),
            joinedload(Submission.answers)
        ).filter(Submission.assignment_id == assignment_id).all()

assignment_service = AssignmentService()