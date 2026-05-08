"""
Agent 链式执行器

支持按顺序执行多个 Agent，每步输出自动注入下一步的 context。
支持"反馈循环"：当某个 Agent 返回 urgent 级别消息时，可回退到上游重新处理。
"""

import uuid
import time
import logging
from typing import Any, Callable, Optional

from models.agent_message import AgentChainResult

logger = logging.getLogger(__name__)

# 全局 Agent 实例缓存
_agent_cache: dict[str, Any] = {}


def _get_agent_instance(agent_name: str) -> Any:
    """获取 Agent 实例（懒加载 + 缓存）"""
    if agent_name not in _agent_cache:
        from agents.base_agent import get_agent_registry
        registry = get_agent_registry()
        cls = registry.get(agent_name)
        if not cls:
            raise ValueError(f"Unknown agent: {agent_name}")
        _agent_cache[agent_name] = cls()
    return _agent_cache[agent_name]


class AgentChain:
    """
    Agent 链式执行器

    用法：
        chain = AgentChain()
        chain.add_step("material", "search", lambda ctx: {"product": ctx["product"]})
        chain.add_step("title", "generate", lambda ctx: {"topic": ctx["product"], "material_pack": ctx["step_0"].model_dump()})
        result = chain.execute({"product": "防晒霜"})
    """

    def __init__(self):
        self._steps: list[dict] = []
        self._chain_id = str(uuid.uuid4())[:8]
        self._correction_loops: dict[int, dict] = {}  # step_index -> correction config

    def add_step(
        self,
        agent_name: str,
        method: str,
        params_fn: Callable[[dict], dict],
        retry_on_failure: bool = False,
    ) -> "AgentChain":
        """
        添加执行步骤

        Args:
            agent_name: Agent 名称
            method: 调用方法名
            params_fn: 从 context 构建参数的函数
            retry_on_failure: 失败时是否继续（默认中断）

        Returns:
            self（支持链式调用）
        """
        self._steps.append({
            "agent_name": agent_name,
            "method": method,
            "params_fn": params_fn,
            "retry_on_failure": retry_on_failure,
        })
        return self

    def add_correction_loop(
        self,
        check_step: int,
        fix_step: int,
        max_retries: int = 2,
    ) -> "AgentChain":
        """
        添加修正循环：当 check_step 发现问题时，回退到 fix_step 重新处理

        Args:
            check_step: 检查步骤的索引（如合规检查）
            fix_step: 修正步骤的索引（如正文生成）
            max_retries: 最大重试次数

        Returns:
            self
        """
        self._correction_loops[check_step] = {
            "fix_step": fix_step,
            "max_retries": max_retries,
            "current_retries": 0,
        }
        return self

    def execute(self, initial_input: dict) -> AgentChainResult:
        """
        执行链式调用

        Args:
            initial_input: 初始输入数据

        Returns:
            AgentChainResult: 执行结果
        """
        start_time = time.time()
        context = {**initial_input}
        step_results = []
        warnings = []

        i = 0
        while i < len(self._steps):
            step = self._steps[i]
            step_start = time.time()

            try:
                agent = _get_agent_instance(step["agent_name"])
                method = getattr(agent, step["method"])

                # 从 context 构建参数
                params = step["params_fn"](context)

                # 执行
                result = method(**params)
                duration_ms = (time.time() - step_start) * 1000

                # 存储结果到 context
                context["step_result"] = result
                context[f"step_{i}"] = result

                step_results.append({
                    "step": i,
                    "agent": step["agent_name"],
                    "method": step["method"],
                    "success": True,
                    "duration_ms": duration_ms,
                })

                logger.info(
                    f"Chain {self._chain_id} step {i} "
                    f"({step['agent_name']}.{step['method']}): {duration_ms:.0f}ms"
                )

                # 检查是否需要修正循环
                if i in self._correction_loops:
                    loop_config = self._correction_loops[i]
                    if self._should_trigger_correction(result, loop_config):
                        if loop_config["current_retries"] < loop_config["max_retries"]:
                            loop_config["current_retries"] += 1
                            warnings.append(
                                f"Step {i} triggered correction, "
                                f"retry {loop_config['current_retries']}/{loop_config['max_retries']}"
                            )
                            # 回退到修正步骤
                            i = loop_config["fix_step"]
                            continue

                # 前进到下一步
                i += 1

            except Exception as e:
                duration_ms = (time.time() - step_start) * 1000
                step_results.append({
                    "step": i,
                    "agent": step["agent_name"],
                    "method": step["method"],
                    "success": False,
                    "error": str(e),
                    "duration_ms": duration_ms,
                })

                logger.error(
                    f"Chain {self._chain_id} step {i} "
                    f"({step['agent_name']}.{step['method']}) failed: {e}"
                )

                if step["retry_on_failure"]:
                    warnings.append(f"Step {i} failed, continuing: {e}")
                    i += 1
                    continue

                return AgentChainResult(
                    chain_id=self._chain_id,
                    steps=step_results,
                    final_result=None,
                    success=False,
                    total_duration_ms=(time.time() - start_time) * 1000,
                    warnings=warnings,
                )

        total_duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Chain {self._chain_id} completed: "
            f"{len(step_results)} steps, {total_duration_ms:.0f}ms"
        )

        return AgentChainResult(
            chain_id=self._chain_id,
            steps=step_results,
            final_result=context.get("step_result"),
            success=True,
            total_duration_ms=total_duration_ms,
            warnings=warnings,
        )

    def _should_trigger_correction(self, result: Any, loop_config: dict) -> bool:
        """
        判断是否触发修正循环

        默认逻辑：如果结果有 has_p0_issues 属性且为 True，则触发
        """
        if hasattr(result, 'has_p0_issues'):
            return result.has_p0_issues
        if isinstance(result, dict):
            return result.get("has_p0_issues", False)
        return False

    def clear_cache(self):
        """清除 Agent 实例缓存"""
        global _agent_cache
        _agent_cache.clear()
