"""
LLM 服务封装测试

测试覆盖：
1. LLM 配置（config/llm_config.py）- 配置加载、运行时切换
2. LLM 降级模块（tools/llm_tools.py）- L1-L4 降级逻辑
3. Prompt 管理（tools/prompt_tools.py）- 加载、变量替换
4. CrewAI 集成（tools/crewai_llm.py）- LLM 创建
"""

import os
import time
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from config import (
    LLMConfig,
    LLMFallbackConfig,
    LLMFallbackLevel,
    LLMManagerConfig,
    LLMProvider,
    MiniMaxConfig,
    MimoConfig,
    DeepSeekConfig,
    QwenConfig,
    load_llm_config_from_env,
)


# ── LLM 配置测试 ──────────────────────────────────────────


class TestLLMConfig:
    """LLM 配置类测试"""

    def test_llm_provider_enum(self):
        """测试 LLM 提供商枚举"""
        assert LLMProvider.MINIMAX == "minimax"
        assert LLMProvider.MIMO == "mimo"
        assert LLMProvider.DEEPSEEK == "deepseek"
        assert LLMProvider.QWEN == "qwen"

    def test_llm_fallback_level_enum(self):
        """测试降级级别枚举"""
        assert LLMFallbackLevel.L1_NORMAL == "l1_normal"
        assert LLMFallbackLevel.L2_RETRY == "l2_retry"
        assert LLMFallbackLevel.L3_FALLBACK == "l3_fallback"
        assert LLMFallbackLevel.L4_CACHE == "l4_cache"

    def test_mini_max_config_defaults(self):
        """测试 MiniMax 默认配置"""
        config = MiniMaxConfig(api_key="test")
        assert config.provider == LLMProvider.MINIMAX
        assert config.model == "MiniMax-M2.7"
        assert config.base_url == "https://api.minimax.chat/v1"
        assert config.timeout == 120

    def test_mimo_config_defaults(self):
        """测试 Mimo 默认配置"""
        config = MimoConfig(api_key="test")
        assert config.provider == LLMProvider.MIMO
        assert config.model == "mimo-v2.5-pro"

    def test_deepseek_config_defaults(self):
        """测试 DeepSeek 默认配置"""
        config = DeepSeekConfig(api_key="test")
        assert config.provider == LLMProvider.DEEPSEEK
        assert config.model == "deepseek-chat"

    def test_qwen_config_defaults(self):
        """测试 Qwen 默认配置"""
        config = QwenConfig(api_key="test")
        assert config.provider == LLMProvider.QWEN
        assert config.model == "qwen-turbo"

    def test_manager_config_defaults(self):
        """测试管理器默认配置"""
        config = LLMManagerConfig()
        assert config.primary.provider == LLMProvider.MINIMAX
        assert len(config.fallbacks) == 3
        assert config.current_level == LLMFallbackLevel.L1_NORMAL

    def test_manager_get_current_provider_l1(self):
        """测试 L1 正常状态获取 provider"""
        config = LLMManagerConfig()
        provider = config.get_current_provider()
        assert provider.provider == LLMProvider.MINIMAX

    def test_manager_advance_fallback(self):
        """测试降级推进"""
        config = LLMManagerConfig()

        # 第一次 advance → MIMO
        config.advance_fallback()
        assert config.current_level == LLMFallbackLevel.L3_FALLBACK
        assert config.get_current_provider().provider == LLMProvider.MIMO

        # 第二次 advance → DEEPSEEK
        config.advance_fallback()
        assert config.get_current_provider().provider == LLMProvider.DEEPSEEK

        # 第三次 advance → QWEN
        config.advance_fallback()
        assert config.get_current_provider().provider == LLMProvider.QWEN

        # 第四次 advance → 保持 QWEN（已用尽）
        config.advance_fallback()
        assert config.get_current_provider().provider == LLMProvider.QWEN
        assert config.is_all_fallbacks_exhausted

    def test_manager_reset(self):
        """测试重置"""
        config = LLMManagerConfig()
        config.advance_fallback()
        config.advance_fallback()
        config.reset()
        assert config.current_level == LLMFallbackLevel.L1_NORMAL
        assert config.get_current_provider().provider == LLMProvider.MINIMAX
        assert not config.is_all_fallbacks_exhausted

    def test_manager_get_next_fallback(self):
        """测试获取下一个降级配置"""
        config = LLMManagerConfig()
        next_fb = config.get_next_fallback()
        assert next_fb is not None
        assert next_fb.provider == LLMProvider.MIMO

    def test_load_config_from_env(self):
        """测试从环境变量加载配置"""
        with patch.dict(os.environ, {
            "MINIMAX_API_KEY": "test-minimax-key",
            "MINIMAX_BASE_URL": "https://custom.minimax.com/v1",
            "MIMO_API_KEY": "test-mimo-key",
            "DEEPSEEK_API_KEY": "test-deepseek-key",
        }):
            config = load_llm_config_from_env()
            assert config.primary.api_key == "test-minimax-key"
            assert config.primary.base_url == "https://custom.minimax.com/v1"
            assert len(config.fallbacks) >= 2  # mimo + deepseek


# ── LLM 降级模块测试 ──────────────────────────────────────


class TestLLMCallLog:
    """调用日志测试"""

    def test_record_success(self):
        """测试记录成功调用"""
        from tools.llm_tools import LLMCallLog, LLMCallRecord

        log = LLMCallLog()
        log.record(LLMCallRecord(
            provider="minimax", model="MiniMax-M2.7",
            latency_ms=500, success=True
        ))
        assert log.consecutive_failures == 0
        assert log.get_stats()["total"] == 1
        assert log.get_stats()["success"] == 1

    def test_record_failure(self):
        """测试记录失败调用"""
        from tools.llm_tools import LLMCallLog, LLMCallRecord

        log = LLMCallLog()
        log.record(LLMCallRecord(
            provider="minimax", model="MiniMax-M2.7",
            latency_ms=0, success=False, error="timeout"
        ))
        assert log.consecutive_failures == 1
        assert log.get_stats()["failure"] == 1

    def test_consecutive_failures(self):
        """测试连续失败计数"""
        from tools.llm_tools import LLMCallLog, LLMCallRecord

        log = LLMCallLog()
        for _ in range(3):
            log.record(LLMCallRecord(
                provider="minimax", model="MiniMax-M2.7",
                latency_ms=0, success=False, error="error"
            ))
        assert log.consecutive_failures == 3

        # 成功后重置
        log.record(LLMCallRecord(
            provider="minimax", model="MiniMax-M2.7",
            latency_ms=500, success=True
        ))
        assert log.consecutive_failures == 0

    def test_reset_failures(self):
        """测试手动重置失败计数"""
        from tools.llm_tools import LLMCallLog, LLMCallRecord

        log = LLMCallLog()
        log.record(LLMCallRecord(
            provider="minimax", model="MiniMax-M2.7",
            latency_ms=0, success=False, error="error"
        ))
        log.reset_failures()
        assert log.consecutive_failures == 0


class TestLLMResponseCache:
    """响应缓存测试"""

    def test_cache_put_get(self):
        """测试缓存存取"""
        from tools.llm_tools import LLMResponseCache

        cache = LLMResponseCache(ttl_seconds=60)
        messages = [{"role": "user", "content": "hello"}]
        cache.put(messages, "test-model", "cached response")
        assert cache.get(messages, "test-model") == "cached response"

    def test_cache_miss(self):
        """测试缓存未命中"""
        from tools.llm_tools import LLMResponseCache

        cache = LLMResponseCache(ttl_seconds=60)
        messages = [{"role": "user", "content": "hello"}]
        assert cache.get(messages, "nonexistent") is None

    def test_cache_ttl_expiry(self):
        """测试缓存过期"""
        from tools.llm_tools import LLMResponseCache

        cache = LLMResponseCache(ttl_seconds=1)
        messages = [{"role": "user", "content": "hello"}]
        cache.put(messages, "test-model", "cached response")
        time.sleep(1.1)
        assert cache.get(messages, "test-model") is None

    def test_cache_different_messages(self):
        """测试不同消息不命中"""
        from tools.llm_tools import LLMResponseCache

        cache = LLMResponseCache(ttl_seconds=60)
        msgs1 = [{"role": "user", "content": "hello"}]
        msgs2 = [{"role": "user", "content": "world"}]
        cache.put(msgs1, "model", "response1")
        assert cache.get(msgs2, "model") is None

    def test_cache_clear(self):
        """测试清空缓存"""
        from tools.llm_tools import LLMResponseCache

        cache = LLMResponseCache(ttl_seconds=60)
        messages = [{"role": "user", "content": "hello"}]
        cache.put(messages, "model", "response")
        cache.clear()
        assert cache.get(messages, "model") is None


class TestLLMCallTool:
    """LLM 调用工具测试"""

    def test_tool_init(self):
        """测试工具初始化"""
        from tools.llm_tools import LLMCallTool

        tool = LLMCallTool()
        status = tool.get_status()
        assert status["current_level"] == LLMFallbackLevel.L1_NORMAL
        assert status["current_provider"] == LLMProvider.MINIMAX

    def test_tool_call_with_mock_success(self):
        """测试模拟成功调用"""
        from tools.llm_tools import LLMCallTool

        tool = LLMCallTool()

        # Mock the _do_call method
        with patch.object(tool, '_do_call', return_value="test response"):
            result = tool.call([{"role": "user", "content": "hello"}])
            assert result == "test response"
            assert tool.call_log.consecutive_failures == 0
            assert tool.current_level == LLMFallbackLevel.L1_NORMAL

    def test_tool_call_with_mock_failure_then_success(self):
        """测试失败后重试成功（L2重试）"""
        from tools.llm_tools import LLMCallTool

        tool = LLMCallTool()

        call_count = 0
        def mock_do_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first call fails")
            return "success on retry"

        with patch.object(tool, '_do_call', side_effect=mock_do_call):
            result = tool.call([{"role": "user", "content": "hello"}])
            assert result == "success on retry"
            assert call_count == 2

    def test_tool_cache_fallback(self):
        """测试 L4 缓存兜底"""
        from tools.llm_tools import LLMCallTool

        tool = LLMCallTool()
        messages = [{"role": "user", "content": "hello"}]

        # 先写入缓存
        tool._cache.put(messages, "MiniMax-M2.7", "cached result")

        # Mock 所有调用失败
        with patch.object(tool, '_do_call', side_effect= RuntimeError("all failed")):
            result = tool.call(messages)
            assert "cached result" in result
            assert "建议人工审核" in result

    def test_tool_reset(self):
        """测试重置"""
        from tools.llm_tools import LLMCallTool

        tool = LLMCallTool()
        tool._llm_config.advance_fallback()
        tool.call_log.record(tool.call_log.__class__.__annotations__.get(
            'LLMCallRecord', type('LLMCallRecord', (), {})
        ) if False else __import__('tools.llm_tools', fromlist=['LLMCallRecord']).LLMCallRecord(
            provider="test", model="test", latency_ms=0, success=False, error="test"
        ))

        tool.reset()
        status = tool.get_status()
        assert status["current_level"] == LLMFallbackLevel.L1_NORMAL
        assert status["call_stats"]["consecutive_failures"] == 0


# ── Prompt 管理测试 ──────────────────────────────────────


class TestPromptManager:
    """Prompt 管理器测试"""

    def test_list_prompts(self):
        """测试列出可用 Prompt"""
        from tools.prompt_tools import prompt_manager

        prompts = prompt_manager.list_prompts()
        assert "title_agent" in prompts
        assert "article_agent" in prompts
        assert "compliance_agent" in prompts

    def test_load_prompt(self):
        """测试加载 Prompt"""
        from tools.prompt_tools import prompt_manager

        prompt = prompt_manager.load_prompt("title_agent")
        assert len(prompt) > 0
        assert "标题" in prompt or "title" in prompt.lower()

    def test_variable_replacement(self):
        """测试变量替换"""
        from tools.prompt_tools import PromptManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text(
                "Material: {{material_pack}}\nTopic: {{topic}}\nUnset: {{missing}}",
                encoding="utf-8",
            )

            pm = PromptManager(prompts_dir=tmpdir)
            result = pm.load_prompt("test", material_pack="test_material", topic="test_topic")

            assert "test_material" in result
            assert "test_topic" in result
            assert "{{missing}}" in result  # 未提供的变量保留占位符

    def test_file_not_found(self):
        """测试文件不存在"""
        from tools.prompt_tools import prompt_manager

        with pytest.raises(FileNotFoundError):
            prompt_manager.load_prompt("nonexistent_agent_xyz")

    def test_cache(self):
        """测试缓存机制"""
        from tools.prompt_tools import PromptManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("content v1", encoding="utf-8")

            pm = PromptManager(prompts_dir=tmpdir)
            result1 = pm.load_prompt("test")
            assert result1 == "content v1"

            # 修改文件，但缓存仍是旧内容
            test_file.write_text("content v2", encoding="utf-8")
            result2 = pm.load_prompt("test")
            assert result2 == "content v1"  # 缓存命中

            # 强制重新加载
            result3 = pm.reload_prompt("test")
            assert result3 == "content v2"

    def test_clear_cache(self):
        """测试清除缓存"""
        from tools.prompt_tools import PromptManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("v1", encoding="utf-8")

            pm = PromptManager(prompts_dir=tmpdir)
            pm.load_prompt("test")

            test_file.write_text("v2", encoding="utf-8")
            pm.clear_cache()

            result = pm.load_prompt("test")
            assert result == "v2"


# ── LLM 响应解析测试 ──────────────────────────────────────


class TestLLMResponseParser:
    """LLM 响应解析器测试"""

    def test_parse_json(self):
        """测试 JSON 解析"""
        from tools.llm_tools import LLMResponseParser

        result = LLMResponseParser.parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_noise(self):
        """测试带噪音的 JSON 解析"""
        from tools.llm_tools import LLMResponseParser

        result = LLMResponseParser.parse_json('Here is the result: {"key": "value"} done')
        assert result == {"key": "value"}

    def test_parse_list(self):
        """测试列表解析"""
        from tools.llm_tools import LLMResponseParser

        result = LLMResponseParser.parse_list('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_list_with_noise(self):
        """测试带噪音的列表解析"""
        from tools.llm_tools import LLMResponseParser

        result = LLMResponseParser.parse_list('Result: [1, 2, 3] done')
        assert result == [1, 2, 3]

    def test_parse_json_invalid(self):
        """测试无效 JSON"""
        from tools.llm_tools import LLMResponseParser

        with pytest.raises(ValueError):
            LLMResponseParser.parse_json("not json at all")


# ── CrewAI 集成测试 ──────────────────────────────────────


class TestCrewAILLMIntegration:
    """CrewAI 集成测试"""

    def test_create_llm(self):
        """测试创建 CrewAI LLM"""
        from tools.crewai_llm import create_llm

        llm = create_llm()
        assert llm.model == "openai/MiniMax-M2.7"

    def test_create_llm_with_custom_config(self):
        """测试自定义配置创建 LLM"""
        from tools.crewai_llm import create_llm

        config = LLMManagerConfig(primary=MiniMaxConfig(api_key="test-key"))
        llm = create_llm(config)
        assert "MiniMax" in llm.model

    def test_create_default_llm_tool(self):
        """测试创建默认 LLM 工具"""
        from tools.crewai_llm import create_default_llm_tool

        tool = create_default_llm_tool()
        assert tool.current_level == LLMFallbackLevel.L1_NORMAL


# ── 集成测试（需要 API Key）────────────────────────────────


@pytest.mark.skipif(
    not os.getenv("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY not set"
)
class TestLLMIntegration:
    """LLM 集成测试（需要真实 API Key）"""

    def test_minimax_api_call(self):
        """测试 MiniMax API 调用"""
        from tools.llm_tools import LLMCallTool

        tool = LLMCallTool()
        result = tool.call(
            [{"role": "user", "content": "你好，请回复'OK'"}],
            max_tokens=10,
        )
        assert len(result) > 0
        assert tool.call_log.get_stats()["success"] >= 1

    def test_prompt_load_and_call(self):
        """测试 Prompt 加载 + LLM 调用"""
        from tools.prompt_tools import prompt_manager
        from tools.llm_tools import LLMCallTool

        prompt = prompt_manager.load_prompt("title_agent")
        tool = LLMCallTool()

        result = tool.call(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "请生成一个关于护肝片的标题"},
            ],
            max_tokens=200,
        )
        assert len(result) > 0
