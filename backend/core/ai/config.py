"""
AI配置 - 简化版，只使用千问API
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('../.env')

class AIConfig:
    """AI配置，只使用千问API"""

    def __init__(self):
        # 千问API配置
        self.provider = "qwen"
        # 千问和DashScope使用同一个API密钥
        self.api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not self.api_key:
            raise ValueError("未设置DASHSCOPE_API_KEY环境变量")

        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = "qwen-plus"

        # 简化的配置
        self.max_tokens = 4096
        self.temperature = 0.7
        self.enable_monitoring = True

    def get_llm_config(self):
        """获取LLM配置"""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }


# 全局配置实例
ai_config = AIConfig()


# 兼容性函数
def get_ai_config():
    """获取AI配置实例"""
    return ai_config