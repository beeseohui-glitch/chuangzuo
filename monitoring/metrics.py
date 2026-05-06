"""
Prometheus指标采集
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional

# 创建默认注册表
registry = CollectorRegistry()

# Agent指标
agent_calls_total = Counter(
    "agent_calls_total",
    "Total number of agent calls",
    ["agent_name", "status"],
    registry=registry,
)

agent_call_duration_seconds = Histogram(
    "agent_call_duration_seconds",
    "Agent call duration in seconds",
    ["agent_name"],
    registry=registry,
)

# LLM指标
llm_calls_total = Counter(
    "llm_calls_total",
    "Total number of LLM calls",
    ["provider", "status"],
    registry=registry,
)

llm_call_duration_seconds = Histogram(
    "llm_call_duration_seconds",
    "LLM call duration in seconds",
    ["provider"],
    registry=registry,
)

# 向量检索指标
vector_search_duration_seconds = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration in seconds",
    registry=registry,
)

# 系统指标
cpu_usage = Gauge(
    "cpu_usage_percent",
    "CPU usage percent",
    registry=registry,
)

memory_usage = Gauge(
    "memory_usage_percent",
    "Memory usage percent",
    registry=registry,
)


class MetricsCollector:
    """指标采集器"""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or registry

    def record_agent_call(self, agent_name: str, status: str, duration: float):
        """记录Agent调用"""
        agent_calls_total.labels(agent_name=agent_name, status=status).inc()
        agent_call_duration_seconds.labels(agent_name=agent_name).observe(duration)

    def record_llm_call(self, provider: str, status: str, duration: float):
        """记录LLM调用"""
        llm_calls_total.labels(provider=provider, status=status).inc()
        llm_call_duration_seconds.labels(provider=provider).observe(duration)

    def record_vector_search(self, duration: float):
        """记录向量检索"""
        vector_search_duration_seconds.observe(duration)

    def update_system_metrics(self, cpu: float, memory: float):
        """更新系统指标"""
        cpu_usage.set(cpu)
        memory_usage.set(memory)
