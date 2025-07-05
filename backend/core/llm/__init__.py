"""
LLM模块 - 只使用千问API
"""
from .qwen_client import QwenClient, get_qwen_client

__all__ = ["QwenClient", "get_qwen_client"]