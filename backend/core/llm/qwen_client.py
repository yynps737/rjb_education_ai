"""
阿里千问API客户端
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class QwenClient:
    """阿里千问API客户端"""

    def __init__(self):
        """初始化千问客户端"""
        # 千问和DashScope使用同一个API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen-plus"  # 使用千问Plus模型

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7, stream: bool = False):
        """生成文本"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                # 返回生成器用于流式传输
                return response
            else:
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"千问API调用失败: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 2000, temperature: float = 0.7, stream: bool = False):
        """对话生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                # 返回生成器用于流式传输
                return response
            else:
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"千问API调用失败: {e}")
            raise
    
    def generate_stream(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7):
        """流式生成文本 - 便捷方法"""
        return self.generate(prompt, max_tokens, temperature, stream=True)


# 全局实例
_qwen_client = None


def get_qwen_client() -> QwenClient:
    """获取千问客户端实例"""
    global _qwen_client
    if _qwen_client is None:
        _qwen_client = QwenClient()
    return _qwen_client