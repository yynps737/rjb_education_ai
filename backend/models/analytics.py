from sqlalchemy import Column, String, Integer, ForeignKey, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from models.base import BaseModel
class LearningProgress(BaseModel):
    __tablename__ = "learning_progress"

    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    progress_percentage = Column(Float, default=0)
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="learning_progress")

    def __repr__(self):
        return f"<LearningProgress User {self.user_id} - Course {self.course_id}>"

class PerformanceMetrics(BaseModel):
    __tablename__ = "performance_metrics"

    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    metric_type = Column(String)  # quiz_score, assignment_score, participation, etc.
    value = Column(Float)
    meta_data = Column(JSON, default=dict)
    recorded_at = Column(DateTime)

    def __repr__(self):
        return f"<PerformanceMetrics {self.metric_type}: {self.value}>"