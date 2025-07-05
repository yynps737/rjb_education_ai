from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Float, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from models.base import BaseModel
class QuestionType(enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CODING = "coding"

class AssignmentStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"

class Assignment(BaseModel):
    __tablename__ = "assignments"

    title = Column(String, nullable=False)
    description = Column(Text)
    course_id = Column(Integer, ForeignKey("courses.id"))
    due_date = Column(DateTime)
    total_points = Column(Float, default=100)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.DRAFT)
    instructions = Column(Text)

    # 关系
    course = relationship("Course", back_populates="assignments")
    questions = relationship("Question", back_populates="assignment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assignment {self.title}>"

class Question(BaseModel):
    __tablename__ = "questions"

    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    question_type = Column(Enum(QuestionType), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(JSON)
    # 用于选择题
    correct_answer = Column(JSON)
    # 可以是字符串、列表或字典
    points = Column(Float, default=10)
    order = Column(Integer)
    explanation = Column(Text)
    grading_criteria = Column(JSON)
    # 用于主观题
    test_cases = Column(JSON)
    # 用于编程题

    # 关系
    assignment = relationship("Assignment", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Question {self.id} - {self.question_type.value}>"

class Submission(BaseModel):
    __tablename__ = "submissions"

    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    submitted_at = Column(DateTime)
    score = Column(Float)
    feedback = Column(Text)
    status = Column(String, default="submitted")
    # 提交、已评分、已退回

    # 关系
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Submission {self.id} by Student {self.student_id}>"

class Answer(BaseModel):
    __tablename__ = "answers"

    submission_id = Column(Integer, ForeignKey("submissions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    content = Column(JSON)  # Student's answer
    score = Column(Float)
    feedback = Column(Text)
    auto_graded = Column(Integer, default=0)

    # 关系
    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self):
        return f"<Answer for Question {self.question_id}>"