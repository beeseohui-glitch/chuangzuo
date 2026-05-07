"""
Prompt 管理器 - 统一加载接口 + 变量替换

用法：
    from tools.prompt_tools import prompt_manager
    prompt = prompt_manager.load_prompt("title_agent", material_pack="...", topic="...")
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# prompts 目录路径
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptManager:
    """Prompt 统一管理器"""

    def __init__(self, prompts_dir: Optional[str] = None):
        self._prompts_dir = Path(prompts_dir) if prompts_dir else PROMPTS_DIR
        self._cache: dict[str, str] = {}  # 文件内容缓存

    def load_prompt(self, agent_name: str, **kwargs) -> str:
        """
        加载 Prompt 文件并替换变量

        Args:
            agent_name: Agent 名称（不含 .md 后缀），如 "title_agent"
            **kwargs: 要替换的变量，如 material_pack="...", title="..."
                      会替换 Prompt 中的 {{material_pack}}, {{title}} 等占位符

        Returns:
            str: 替换变量后的 Prompt 内容
        """
        content = self._load_file(agent_name)

        if kwargs:
            content = self._replace_variables(content, kwargs)

        return content

    def _load_file(self, agent_name: str) -> str:
        """加载 Prompt 文件（带缓存）"""
        if agent_name in self._cache:
            return self._cache[agent_name]

        file_path = self._prompts_dir / f"{agent_name}.md"
        if not file_path.exists():
            raise FileNotFoundError(
                f"Prompt 文件不存在: {file_path}\n"
                f"可用的 Prompt: {self.list_prompts()}"
            )

        content = file_path.read_text(encoding="utf-8")
        self._cache[agent_name] = content
        return content

    def _replace_variables(self, content: str, variables: dict) -> str:
        """
        替换 {{variable}} 占位符

        未提供的变量保留原始占位符（不报错，便于调试）
        """
        def replacer(match):
            var_name = match.group(1).strip()
            if var_name in variables:
                return str(variables[var_name])
            return match.group(0)  # 保留原始占位符

        return re.sub(r'\{\{(\w+)\}\}', replacer, content)

    def list_prompts(self) -> list[str]:
        """列出所有可用的 Prompt 文件名"""
        if not self._prompts_dir.exists():
            return []
        return [
            f.stem for f in sorted(self._prompts_dir.glob("*.md"))
            if f.is_file()
        ]

    def clear_cache(self):
        """清除缓存（用于热更新 Prompt）"""
        self._cache.clear()

    def reload_prompt(self, agent_name: str) -> str:
        """强制重新加载 Prompt（忽略缓存）"""
        self._cache.pop(agent_name, None)
        return self._load_file(agent_name)


# 全局单例
prompt_manager = PromptManager()
