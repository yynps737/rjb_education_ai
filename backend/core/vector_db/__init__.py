"""
Vector database module
"""
from core.vector_db.optimized_chroma_store import OptimizedChromaStore
from core.vector_db.dashscope_embeddings import DashScopeEmbedding
__all__ = ['OptimizedChromaStore', 'DashScopeEmbedding']