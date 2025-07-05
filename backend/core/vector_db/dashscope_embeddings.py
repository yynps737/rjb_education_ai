"""
阿里通义千问嵌入服务 - 最优质的中文嵌入方案
"""
import os
import dashscope
from dashscope import TextEmbedding
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class DashScopeEmbedding:
    """通义千问嵌入服务"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化DashScope嵌入服务

        Args:
            api_key: API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量或提供api_key参数")

        dashscope.api_key = self.api_key

        # 使用text-embedding-v1模型
        self.model = TextEmbedding.Models.text_embedding_v1
        self.dimension = 1536
        # 推荐维度

    async def generate_embedding(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        try:
            resp = TextEmbedding.call(
                model=self.model,
                input=text,
                dimension=self.dimension
            )

            if resp.status_code == 200:
                # 返回第一个嵌入结果
                return resp.output['embeddings'][0]['embedding']
            else:
                logger.error(f"DashScope API错误: {resp.message}")
                raise Exception(f"嵌入生成失败: {resp.message}")

        except Exception as e:
            logger.error(f"DashScope嵌入生成异常: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        try:
            # DashScope支持批量处理
            resp = TextEmbedding.call(
                model=self.model,
                input=texts,
                dimension=self.dimension
            )

            if resp.status_code == 200:
                # 提取所有嵌入结果
                embeddings = []
                for embedding_data in resp.output['embeddings']:
                    embeddings.append(embedding_data['embedding'])
                return embeddings
            else:
                logger.error(f"DashScope批量API错误: {resp.message}")
                raise Exception(f"批量嵌入生成失败: {resp.message}")

        except Exception as e:
            logger.error(f"DashScope批量嵌入生成异常: {e}")
            raise

    def get_embedding_info(self):
        """获取嵌入模型信息"""
        return {
            "provider": "DashScope (阿里通义千问)",
            "model": "text-embedding-v1",
            "dimension": self.dimension,
            "max_input_length": 2048,
            # 字符数
            "features": [
                "中文语义理解最优",
                "支持批量处理",
                "自定义维度",
                "OpenAI兼容"
            ]
        }