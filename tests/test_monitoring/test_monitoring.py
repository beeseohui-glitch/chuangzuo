"""
Monitoring测试

Step 15: 测试模块开发
"""

import pytest


class TestMetricsCollector:
    """指标采集器测试"""

    def test_record_agent_call(self):
        """测试记录Agent调用"""
        from monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        # 测试记录不报错
        collector.record_agent_call("title_agent", "success", 0.5)
        collector.record_agent_call("article_agent", "success", 1.0)

    def test_record_llm_call(self):
        """测试记录LLM调用"""
        from monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_llm_call("minimax", "success", 0.3)

    def test_update_system_metrics(self):
        """测试更新系统指标"""
        from monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.update_system_metrics(cpu=50.0, memory=60.0)


class TestAlertManager:
    """告警管理器测试"""

    def test_add_rule(self):
        """测试添加告警规则"""
        from monitoring.alerts import AlertManager, AlertRule

        manager = AlertManager()
        rule = AlertRule(
            name="Test Alert",
            metric="cpu_usage_percent",
            threshold=80.0,
            operator="gt",
            severity="warning",
            message="CPU使用率过高",
        )
        manager.add_rule(rule)
        assert len(manager.rules) == 1

    def test_check_triggered(self):
        """测试告警触发"""
        from monitoring.alerts import AlertManager, AlertRule

        manager = AlertManager()
        rule = AlertRule(
            name="High CPU",
            metric="cpu_usage_percent",
            threshold=80.0,
            operator="gt",
            severity="warning",
            message="CPU使用率超过80%",
        )
        manager.add_rule(rule)

        triggered = manager.check("cpu_usage_percent", 85.0)
        assert len(triggered) == 1
        assert triggered[0].name == "High CPU"

    def test_check_not_triggered(self):
        """测试告警未触发"""
        from monitoring.alerts import AlertManager, AlertRule

        manager = AlertManager()
        rule = AlertRule(
            name="High CPU",
            metric="cpu_usage_percent",
            threshold=80.0,
            operator="gt",
            severity="warning",
            message="CPU使用率超过80%",
        )
        manager.add_rule(rule)

        triggered = manager.check("cpu_usage_percent", 50.0)
        assert len(triggered) == 0
