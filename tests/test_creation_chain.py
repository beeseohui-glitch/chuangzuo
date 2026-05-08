"""
测试 CreationChain — 创作链
"""

import pytest


class TestCreationChain:
    """CreationChain 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from agents.chains.creation_chain import CreationChain
        assert CreationChain is not None

    def test_chain_init_quick(self):
        """测试快速模式初始化"""
        from agents.chains.creation_chain import CreationChain
        chain = CreationChain(mode="quick")
        assert chain is not None

    def test_chain_init_full(self):
        """测试数据驱动模式初始化"""
        from agents.chains.creation_chain import CreationChain
        chain = CreationChain(mode="full")
        assert chain is not None

    def test_chain_init_with_enterprise(self):
        """测试带企业ID初始化"""
        from agents.chains.creation_chain import CreationChain
        chain = CreationChain(mode="full", enterprise_id="ent_001")
        assert chain is not None


class TestComplianceChain:
    """ComplianceChain 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from agents.chains.compliance_chain import ComplianceChain
        assert ComplianceChain is not None

    def test_chain_init(self):
        """测试初始化"""
        from agents.chains.compliance_chain import ComplianceChain
        chain = ComplianceChain()
        assert chain is not None

    def test_chain_init_custom_rounds(self):
        """测试自定义最大轮次"""
        from agents.chains.compliance_chain import ComplianceChain
        chain = ComplianceChain(max_rounds=3)
        assert chain is not None


class TestChainsInit:
    """chains/__init__.py 测试"""

    def test_import_chains(self):
        """测试从 chains 包导入"""
        from agents.chains import CreationChain, ComplianceChain
        assert CreationChain is not None
        assert ComplianceChain is not None
