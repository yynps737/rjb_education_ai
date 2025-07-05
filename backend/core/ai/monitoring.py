"""
AI功能监控和日志模块
"""
import time
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict, deque
import threading
import asyncio
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, Summary
import psutil

from core.ai.config import get_ai_config
logger = logging.getLogger(__name__)

# Prometheus指标
ai_request_count = Counter('ai_request_total', 'Total AI requests', ['component', 'operation', 'status'])
ai_request_duration = Histogram('ai_request_duration_seconds', 'AI request duration', ['component', 'operation'])
ai_token_usage = Counter('ai_token_usage_total', 'Total tokens used', ['model', 'type'])
ai_cache_hits = Counter('ai_cache_hits_total', 'Cache hits', ['component'])
ai_cache_misses = Counter('ai_cache_misses_total', 'Cache misses', ['component'])
ai_error_count = Counter('ai_error_total', 'Total errors', ['component', 'error_type'])
ai_active_requests = Gauge('ai_active_requests', 'Active AI requests', ['component'])
ai_model_memory = Gauge('ai_model_memory_bytes', 'Model memory usage', ['model'])

@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class AIMetrics:
    """AI指标汇总"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_rate: float = 0.0
    average_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    error_rate: float = 0.0
    active_requests: int = 0
    memory_usage_mb: float = 0.0

class AIMonitor:
    """AI监控器"""

    def __init__(self, config=None):
        self.config = config or get_ai_config()
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.latency_buckets = defaultdict(list)
        self.start_time = datetime.now()
        self._lock = threading.Lock()

        # 启动后台监控线程
        if self.config.monitoring_enabled:
            self._start_monitoring()

    def _start_monitoring(self):
        """启动监控线程"""
        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(self.config.metrics_export_interval)
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        logger.info("AI monitoring started")

    def _collect_system_metrics(self):
        """收集系统指标"""
        # 内存使用
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        ai_model_memory.labels(model="system").set(memory_mb)

        # 清理过期数据
        self._cleanup_old_metrics()

    def _cleanup_old_metrics(self):
        """清理过期指标数据"""
        cutoff_time = datetime.now() - timedelta(days=self.config.metrics_retention_days)

        with self._lock:
            for key, points in self.metrics_history.items():
                # deque会自动维护最大长度，这里可以添加额外的清理逻辑
                pass

    @staticmethod
    def track_request(component: str, operation: str):
        """装饰器：跟踪请求"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                ai_active_requests.labels(component=component).inc()

                try:
                    result = func(*args, **kwargs)
                    ai_request_count.labels(
                        component=component,
                        operation=operation,
                        status="success"
                    ).inc()
                    return result

                except Exception as e:
                    ai_request_count.labels(
                        component=component,
                        operation=operation,
                        status="error"
                    ).inc()
                    ai_error_count.labels(
                        component=component,
                        error_type=type(e).__name__
                    ).inc()
                    raise

                finally:
                    duration = time.time() - start_time
                    ai_request_duration.labels(
                        component=component,
                        operation=operation
                    ).observe(duration)
                    ai_active_requests.labels(component=component).dec()

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                ai_active_requests.labels(component=component).inc()

                try:
                    result = await func(*args, **kwargs)
                    ai_request_count.labels(
                        component=component,
                        operation=operation,
                        status="success"
                    ).inc()
                    return result

                except Exception as e:
                    ai_request_count.labels(
                        component=component,
                        operation=operation,
                        status="error"
                    ).inc()
                    ai_error_count.labels(
                        component=component,
                        error_type=type(e).__name__
                    ).inc()
                    raise

                finally:
                    duration = time.time() - start_time
                    ai_request_duration.labels(
                        component=component,
                        operation=operation
                    ).observe(duration)
                    ai_active_requests.labels(component=component).dec()

            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
        return decorator

    def track_token_usage(self, model: str, input_tokens: int, output_tokens: int):
        """跟踪token使用"""
        ai_token_usage.labels(model=model, type="input").inc(input_tokens)
        ai_token_usage.labels(model=model, type="output").inc(output_tokens)
        ai_token_usage.labels(model=model, type="total").inc(input_tokens + output_tokens)

    def track_cache(self, component: str, hit: bool):
        """跟踪缓存"""
        if hit:
            ai_cache_hits.labels(component=component).inc()
        else:
            ai_cache_misses.labels(component=component).inc()

    def record_latency(self, component: str, operation: str, latency_ms: float):
        """记录延迟"""
        key = f"{component}:{operation}"
        with self._lock:
            self.latency_buckets[key].append(latency_ms)

            # 保持最近1000个样本
            if len(self.latency_buckets[key]) > 1000:
                self.latency_buckets[key] = self.latency_buckets[key][-1000:]

    def get_metrics_summary(self) -> AIMetrics:
        """获取指标汇总"""
        metrics = AIMetrics()

        # 这里应该从Prometheus或其他监控系统获取实际数据
        # 以下是示例实现

        with self._lock:
            # 计算延迟百分位
            all_latencies = []
            for latencies in self.latency_buckets.values():
                all_latencies.extend(latencies)

            if all_latencies:
                all_latencies.sort()
                n = len(all_latencies)
                metrics.average_latency = sum(all_latencies) / n
                metrics.p95_latency = all_latencies[int(n * 0.95)]
                metrics.p99_latency = all_latencies[int(n * 0.99)]

        # 计算错误率
        if metrics.total_requests > 0:
            metrics.error_rate = metrics.failed_requests / metrics.total_requests

        # 获取内存使用
        process = psutil.Process()
        metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024

        return metrics

    def export_metrics(self, format: str = "json") -> str:
        """导出指标"""
        metrics = self.get_metrics_summary()

        if format == "json":
            return json.dumps(asdict(metrics), indent=2)
        elif format == "prometheus":
            # 返回Prometheus格式
            lines = []
            lines.append(f"ai_total_requests {metrics.total_requests}")
            lines.append(f"ai_success_rate {1 - metrics.error_rate}")
            lines.append(f"ai_average_latency_ms {metrics.average_latency}")
            lines.append(f"ai_p95_latency_ms {metrics.p95_latency}")
            lines.append(f"ai_p99_latency_ms {metrics.p99_latency}")
            lines.append(f"ai_memory_usage_mb {metrics.memory_usage_mb}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

class AILogger:
    """AI专用日志器"""

    def __init__(self, name: str = "ai_system", config=None):
        self.config = config or get_ai_config()
        self.logger = self._setup_logger(name)

    def _setup_logger(self, name: str) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.config.log_level))

        # 文件处理器
        log_file = Path(self.config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(
            logging.Formatter(self.config.log_format)
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(self.config.log_format)
        )

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def log_request(
        self,
        component: str,
        operation: str,
        request_data: Dict[str, Any],
        response_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status: str = "success"
    ):
        """记录API请求"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "operation": operation,
            "status": status,
            "duration_ms": duration_ms,
            "request": request_data
        }

        if response_data:
            log_entry["response"] = response_data

        if status == "success":
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.error(json.dumps(log_entry, ensure_ascii=False))

    def log_error(
        self,
        component: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录错误"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        self.logger.error(json.dumps(error_entry, ensure_ascii=False), exc_info=True)

    def log_performance(
        self,
        component: str,
        metrics: Dict[str, Any]
    ):
        """记录性能指标"""
        perf_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "type": "performance",
            "metrics": metrics
        }

        self.logger.info(json.dumps(perf_entry, ensure_ascii=False))

class RequestTracker:
    """请求跟踪器"""

    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id or self._generate_request_id()
        self.start_time = time.time()
        self.events = []

    @staticmethod
    def _generate_request_id() -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())

    def add_event(self, event_type: str, data: Dict[str, Any]):
        """添加事件"""
        self.events.append({
            "timestamp": time.time() - self.start_time,
            "type": event_type,
            "data": data
        })

    def get_trace(self) -> Dict[str, Any]:
        """获取跟踪信息"""
        return {
            "request_id": self.request_id,
            "duration": time.time() - self.start_time,
            "events": self.events
        }

# 全局实例
_monitor_instance: Optional[AIMonitor] = None
_logger_instance: Optional[AILogger] = None

def get_ai_monitor() -> AIMonitor:
    """获取AI监控器单例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AIMonitor()
    return _monitor_instance

def get_ai_logger() -> AILogger:
    """获取AI日志器单例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AILogger()
    return _logger_instance

# 便捷装饰器
def monitor_ai_call(component: str, operation: str):
    """监控AI调用的装饰器"""
    return AIMonitor.track_request(component, operation)