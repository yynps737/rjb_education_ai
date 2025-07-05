"""
简化的向量存储实现
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class VectorStore:
    """简化的向量存储"""

    def __init__(self):
        """初始化向量存储"""
        self.documents = []
        logger.info("向量存储初始化完成")

    def add_documents(self, documents: List[Dict[str, Any]]):
        """添加文档"""
        self.documents.extend(documents)
        logger.info(f"添加了 {len(documents)} 个文档")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索文档"""
        # 简单的关键词匹配
        results = []
        query_lower = query.lower()

        for doc in self.documents:
            content = doc.get("content", "").lower()
            if query_lower in content:
                results.append(doc)

        return results[:top_k]

    def clear(self):
        """清空存储"""
        self.documents = []
        logger.info("向量存储已清空")


class RAGEngine:
    """简化的RAG引擎"""

    def __init__(self, vector_store: VectorStore, llm_model: Any):
        self.vector_store = vector_store
        self.llm_model = llm_model

    def retrieve_and_generate(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """检索并生成答案"""
        # 检索相关文档
        sources = self.vector_store.search(query, top_k)

        # 构建上下文
        context = "\n\n".join([doc.get("content", "") for doc in sources])

        # 生成答案
        if context:
            prompt = f"基于以下内容回答问题：\n\n{context}\n\n问题：{query}"
            answer = self.llm_model.generate(prompt)
        else:
            answer = "抱歉，我没有找到相关信息。"

        return {
            "answer": answer,
            "sources": sources,
            "query": query
        }