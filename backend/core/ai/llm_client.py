"""
增强版LLM客户端，支持重试、缓存、流式输出等功能
"""
import os
import time
import json
import hashlib
from typing import List, Dict, Optional, Generator, Any, Callable
from dataclasses import dataclass, field
import logging
from pathlib import Path
import asyncio
from functools import wraps
from datetime import datetime, timedelta

from openai import OpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import diskcache

from core.ai.config import get_ai_config
logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """生成配置"""
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    n: int = 1
    logprobs: Optional[int] = None

@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    created_at: datetime = field(default_factory=datetime.now)
    cached: bool = False
    latency_ms: float = 0

class LLMCache:
    """LLM缓存管理器"""

    def __init__(self, cache_dir: str, ttl: int = 3600):
        self.cache = diskcache.Cache(cache_dir)
        self.ttl = ttl

    def get_cache_key(self, prompt: str, system_prompt: str, config: GenerationConfig) -> str:
        """生成缓存键"""
        cache_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "config": config.__dict__
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[LLMResponse]:
        """获取缓存"""
        try:
            cached_data = self.cache.get(key)
            if cached_data:
                response = LLMResponse(**cached_data)
                response.cached = True
                return response
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def set(self, key: str, response: LLMResponse):
        """设置缓存"""
        try:
            self.cache.set(
                key,
                {
                    "content": response.content,
                    "model": response.model,
                    "usage": response.usage,
                    "finish_reason": response.finish_reason,
                    "created_at": response.created_at,
                    "latency_ms": response.latency_ms
                },
                expire=self.ttl
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

class EnhancedLLMClient:
    """增强版LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[Any] = None
    ):
        self.config = config or get_ai_config()
        self.api_key = api_key or self.config.llm_api_key
        self.base_url = base_url or self.config.llm_base_url
        self.model_name = model_name or self.config.llm_model_name

        # 初始化客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.config.llm_timeout,
            max_retries=0
            # 我们使用tenacity来处理重试
        )

        # 异步客户端
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.config.llm_timeout,
            max_retries=0
        )

        # 缓存
        self.cache = None
        if self.config.cache_enabled:
            cache_dir = Path(self.config.cache_dir) / "llm"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache = LLMCache(str(cache_dir), ttl=self.config.cache_ttl)

        # 统计
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_tokens": 0,
            "errors": 0
        }

        logger.info(f"Initialized Enhanced LLM client with model: {self.model_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    def _call_api(
        self,
        messages: List[Dict[str, str]],
        config: GenerationConfig
    ) -> Any:
        """调用API（带重试）"""
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stop=config.stop,
            stream=config.stream,
            n=config.n,
            logprobs=config.logprobs
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """生成回复"""
        if config is None:
            config = GenerationConfig()

        self.stats["total_requests"] += 1

        # 检查缓存
        if use_cache and self.cache and not config.stream:
            cache_key = self.cache.get_cache_key(prompt, system_prompt or "", config)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.stats["cache_hits"] += 1
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return cached_response

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            start_time = time.time()

            # 调用API
            response = self._call_api(messages, config)

            # 处理响应
            choice = response.choices[0]
            content = choice.message.content

            # 创建响应对象
            llm_response = LLMResponse(
                content=content,
                model=response.model,
                usage=response.usage.model_dump(),
                finish_reason=choice.finish_reason,
                latency_ms=(time.time() - start_time) * 1000
            )

            # 更新统计
            self.stats["total_tokens"] += response.usage.total_tokens

            # 保存到缓存
            if use_cache and self.cache and not config.stream:
                self.cache.set(cache_key, llm_response)

            return llm_response

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error generating response: {e}")
            raise

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> Generator[str, None, None]:
        """流式生成回复"""
        if config is None:
            config = GenerationConfig(stream=True)
        else:
            config.stream = True

        self.stats["total_requests"] += 1

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # 调用API（流式）
            stream = self._call_api(messages, config)

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    if callback:
                        callback(content)
                    yield content

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error in stream generation: {e}")
            raise

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """异步生成回复"""
        if config is None:
            config = GenerationConfig()

        # 检查缓存
        if use_cache and self.cache and not config.stream:
            cache_key = self.cache.get_cache_key(prompt, system_prompt or "", config)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                return cached_response

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            start_time = time.time()

            # 异步调用API
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop,
                stream=False,
                n=config.n
            )

            # 处理响应
            choice = response.choices[0]
            content = choice.message.content

            # 创建响应对象
            llm_response = LLMResponse(
                content=content,
                model=response.model,
                usage=response.usage.model_dump(),
                finish_reason=choice.finish_reason,
                latency_ms=(time.time() - start_time) * 1000
            )

            # 保存到缓存
            if use_cache and self.cache:
                self.cache.set(cache_key, llm_response)

            return llm_response

        except Exception as e:
            logger.error(f"Error in async generation: {e}")
            raise

    def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        max_concurrent: int = 5
    ) -> List[LLMResponse]:
        """批量生成"""
        async def _batch_process():
            semaphore = asyncio.Semaphore(max_concurrent)

            async def _process_one(prompt: str) -> LLMResponse:
                async with semaphore:
                    return await self.agenerate(prompt, system_prompt, config)

            tasks = [_process_one(prompt) for prompt in prompts]
            return await asyncio.gather(*tasks)

        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_batch_process())
        finally:
            loop.close()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_hit_rate = 0
        if self.stats["total_requests"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_requests"]

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "avg_tokens_per_request": self.stats["total_tokens"] / max(1, self.stats["total_requests"])
        }

    def clear_cache(self):
        """清除缓存"""
        if self.cache:
            self.cache.cache.clear()
            logger.info("LLM cache cleared")

# 全局客户端实例
_client_instance: Optional[EnhancedLLMClient] = None

def get_llm_client() -> EnhancedLLMClient:
    """获取LLM客户端单例"""
    global _client_instance
    if _client_instance is None:
        _client_instance = EnhancedLLMClient()
    return _client_instance