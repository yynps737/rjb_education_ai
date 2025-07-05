from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from models.base import BaseModel
class KnowledgeDocument(BaseModel):
    __tablename__ = "knowledge_documents"

    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)  # pdf, docx, txt, etc.
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    file_size = Column(Integer)  # in bytes
    meta_data = Column(JSON, default=dict)

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeDocument {self.title}>"

class KnowledgeChunk(BaseModel):
    __tablename__ = "knowledge_chunks"

    document_id = Column(Integer, ForeignKey("knowledge_documents.id"))
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    page_number = Column(Integer, nullable=True)
    embedding_id = Column(String)
    # ID in vector 数据库    meta_data = Column(JSON, default=dict)

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")

    def __repr__(self):
        return f"<KnowledgeChunk {self.id} from Doc {self.document_id}>"