"""
优化的Chroma向量存储 - 使用通义千问嵌入
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.vector_db.dashscope_embeddings import DashScopeEmbedding
logger = logging.getLogger(__name__)

class OptimizedChromaStore:
    """使用通义千问嵌入的优化向量存储"""

    def __init__(self,
                 collection_name: str = "education_knowledge",
                 api_key: Optional[str] = None):
        """初始化优化的向量存储"""
        # 数据目录
        persist_directory = Path("data/chroma")
        persist_directory.mkdir(parents=True, exist_ok=True)

        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 初始化通义千问嵌入服务
        self.embedding_service = DashScopeEmbedding(api_key=api_key)

        # 创建或获取集合
        self.collection_name = collection_name
        self._init_collection()

        # 线程池用于并发处理
        self.executor = ThreadPoolExecutor(max_workers=5)

    def _init_collection(self):
        """初始化集合"""
        try:
            # 删除旧集合（如果存在）
            try:
                self.client.delete_collection(name=self.collection_name)
            except:
                pass

            # 创建新集合，指定嵌入维度
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "教育平台知识库",
                    "embedding_model": "dashscope-text-embedding-v3",
                    "dimension": 1536
                }
            )
            logger.info(f"创建新集合: {self.collection_name}")
        except Exception as e:
            logger.error(f"集合初始化失败: {e}")
            raise

    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 10
    ):
        """批量添加文档到向量数据库"""
        if ids is None:
            import hashlib
            ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]

        # 分批处理，避免一次性处理过多
        total_docs = len(documents)
        for i in range(0, total_docs, batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            try:
                # 批量生成嵌入
                embeddings = await self.embedding_service.generate_embeddings_batch(batch_docs)

                # 添加到集合
                self.collection.add(
                    documents=batch_docs,
                    embeddings=embeddings,
                    metadatas=batch_metas,
                    ids=batch_ids
                )

                logger.info(f"成功添加批次 {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")

            except Exception as e:
                logger.error(f"添加文档批次失败: {e}")
                raise

        logger.info(f"总共添加了 {total_docs} 个文档到向量数据库")

    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """搜索相似文档"""
        try:
            # 生成查询嵌入
            query_embedding = await self.embedding_service.generate_embedding(query)

            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter
            )

            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0],
                "ids": results.get("ids", [[]])[0]
            }

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise

    async def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        keyword_boost: float = 0.3
    ) -> List[Dict[str, Any]]:
        """混合搜索：结合向量搜索和关键词匹配"""
        # 1. 向量搜索
        vector_results = await self.search(query, n_results * 2, filter)

        # 2. 简单的关键词匹配评分
        query_keywords = set(query.lower().split())

        # 3. 计算混合分数
        scored_results = []
        for i in range(len(vector_results["documents"])):
            doc = vector_results["documents"][i]
            doc_keywords = set(doc.lower().split())

            # 关键词匹配分数
            keyword_score = len(query_keywords & doc_keywords) / max(len(query_keywords), 1)

            # 向量相似度分数 (距离转换为相似度)
            vector_score = 1 - vector_results["distances"][i]

            # 混合分数
            final_score = (1 - keyword_boost) * vector_score + keyword_boost * keyword_score

            scored_results.append({
                "content": doc,
                "metadata": vector_results["metadatas"][i],
                "score": final_score,
                "vector_score": vector_score,
                "keyword_score": keyword_score,
                "id": vector_results["ids"][i]
            })

        # 按混合分数排序
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        return scored_results[:n_results]

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata,
            "embedding_info": self.embedding_service.get_embedding_info()
        }

    def reset_collection(self):
        """重置集合"""
        self.client.delete_collection(self.collection_name)
        self._init_collection()
        logger.warning(f"集合 {self.collection_name} 已重置")