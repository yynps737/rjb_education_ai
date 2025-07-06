"""
简化版的Chroma向量存储 - 兼容ChromaDB 0.4.x
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import hashlib
import json

from core.vector_db.dashscope_embeddings import DashScopeEmbedding

logger = logging.getLogger(__name__)

class SimpleChromaStore:
    """简化版的向量存储，兼容ChromaDB 0.4.x"""

    def __init__(self,
                 collection_name: str = "education_knowledge",
                 api_key: Optional[str] = None):
        """初始化向量存储"""
        # 数据目录
        self.persist_directory = Path("data/chroma")
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 初始化通义千问嵌入服务
        self.embedding_service = DashScopeEmbedding(api_key=api_key)
        
        # 初始化Chroma客户端
        self.collection_name = collection_name
        self._init_client()

    def _init_client(self):
        """初始化ChromaDB客户端"""
        try:
            # ChromaDB 0.4.x API
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"获取现有集合: {self.collection_name}，当前文档数: {self.collection.count()}")
            except Exception as e:
                logger.info(f"集合不存在，创建新集合: {self.collection_name}")
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "教育平台知识库",
                        "embedding_model": "dashscope-text-embedding-v3"
                    }
                )
                
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {e}")
            raise

    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 10
    ):
        """批量添加文档到向量数据库"""
        if not documents:
            logger.warning("没有文档要添加")
            return
            
        if ids is None:
            ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]
        
        # 清理元数据，确保所有值都是基本类型
        cleaned_metadatas = []
        for meta in metadatas:
            cleaned_meta = {}
            for key, value in meta.items():
                if isinstance(value, (str, int, float, bool)):
                    cleaned_meta[key] = value
                elif isinstance(value, (list, dict)):
                    cleaned_meta[key] = json.dumps(value, ensure_ascii=False)
                else:
                    cleaned_meta[key] = str(value)
            cleaned_metadatas.append(cleaned_meta)
        
        # 分批处理
        total_docs = len(documents)
        added_count = 0
        
        for i in range(0, total_docs, batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = cleaned_metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            try:
                # 生成嵌入
                embeddings = await self.embedding_service.generate_embeddings_batch(batch_docs)
                
                # 添加到集合
                self.collection.add(
                    documents=batch_docs,
                    embeddings=embeddings,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                
                added_count += len(batch_docs)
                logger.info(f"成功添加批次 {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
                
            except Exception as e:
                logger.error(f"添加文档批次失败: {e}")
                # 继续处理下一批，而不是完全失败
                continue
        
        logger.info(f"总共成功添加了 {added_count}/{total_docs} 个文档到向量数据库")
        
        # 验证添加
        current_count = self.collection.count()
        logger.info(f"当前集合文档总数: {current_count}")

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
            
            # 确保返回格式正确
            if not results.get("documents"):
                return {
                    "documents": [],
                    "metadatas": [],
                    "distances": [],
                    "ids": []
                }
            
            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0],
                "ids": results.get("ids", [[]])[0]
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "metadata": self.collection.metadata if hasattr(self.collection, 'metadata') else {},
                "embedding_info": self.embedding_service.get_embedding_info(),
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "name": self.collection_name,
                "count": 0,
                "metadata": {},
                "embedding_info": self.embedding_service.get_embedding_info(),
                "status": "error",
                "error": str(e)
            }

    def delete_documents(self, ids: List[str]):
        """删除文档"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"成功删除 {len(ids)} 个文档")
        except Exception as e:
            logger.error(f"删除文档失败: {e}")

    def reset_collection(self):
        """重置集合"""
        try:
            self.client.delete_collection(self.collection_name)
            self._init_client()
            logger.warning(f"集合 {self.collection_name} 已重置")
        except Exception as e:
            logger.error(f"重置集合失败: {e}")