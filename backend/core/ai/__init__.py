"""
AI module exports - Simplified for API usage
"""
from core.ai.config import ai_config
from core.ai.llm_client import EnhancedLLMClient as LLMClient
from core.ai.auto_grader import AutoGrader
from core.ai.question_generator import QuestionGenerator
from core.ai.document_processor import DocumentProcessor
from core.ai.monitoring import AIMonitor
__all__ = [
    'ai_config',
    'LLMClient',
    'AutoGrader',
    'QuestionGenerator',
    'DocumentProcessor',
    'AIMonitor'
]