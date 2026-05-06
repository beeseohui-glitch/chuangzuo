"""
环境检查脚本 - 检查所有环境变量和依赖
"""

import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_env():
    """检查环境配置"""
    print("=" * 60)
    print("Environment Check")
    print("=" * 60)

    results = {
        "env_vars": {},
        "python_packages": {},
        "issues": [],
    }

    # 检查环境变量
    env_vars = [
        "MINIMAX_API_KEY",
        "MINIMAX_BASE_URL",
        "MINIMAX_MODEL",
        "DEEPSEEK_API_KEY",
        "OBSIDIAN_VAULT_PATH",
        "OBSIDIAN_API_KEY",
    ]

    print("\n[1] Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏API key部分
            if "KEY" in var and len(value) > 10:
                display = value[:8] + "..." + value[-4:]
            else:
                display = value
            print(f"  {var}: {display}")
            results["env_vars"][var] = "OK"
        else:
            print(f"  {var}: NOT SET")
            results["env_vars"][var] = "MISSING"

    # 检查Python包
    print("\n[2] Python Packages:")
    packages = [
        "crewai",
        "crewai_flows",
        "openai",
        "pydantic",
        "psycopg2",
        "redis",
        "streamlit",
        "sentence_transformers",
        "python-dotenv",
    ]

    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  {pkg}: OK")
            results["python_packages"][pkg] = "OK"
        except ImportError:
            print(f"  {pkg}: MISSING")
            results["python_packages"][pkg] = "MISSING"
            results["issues"].append(f"Missing package: {pkg}")

    # 检查项目结构
    print("\n[3] Project Structure:")
    dirs = [
        "agents",
        "models",
        "tools",
        "flows",
        "prompts",
        "config",
        "tests",
        "sync",
        "kb",
    ]

    for d in dirs:
        path = PROJECT_ROOT / d
        if path.exists():
            print(f"  {d}/: OK")
        else:
            print(f"  {d}/: MISSING")
            results["issues"].append(f"Missing directory: {d}")

    # 检查关键文件
    print("\n[4] Key Files:")
    files = [
        "agents/__init__.py",
        "models/__init__.py",
        "config/__init__.py",
        "flows/xiaohongshu_flow.py",
        "prompts/title_agent.md",
        ".env",
    ]

    for f in files:
        path = PROJECT_ROOT / f
        if path.exists():
            print(f"  {f}: OK")
        else:
            print(f"  {f}: MISSING")
            results["issues"].append(f"Missing file: {f}")

    # 总结
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    env_count = sum(1 for v in results["env_vars"].values() if v == "OK")
    pkg_count = sum(1 for v in results["python_packages"].values() if v == "OK")

    print(f"Environment Variables: {env_count}/{len(env_vars)} OK")
    print(f"Python Packages: {pkg_count}/{len(packages)} OK")

    if results["issues"]:
        print(f"\nIssues found: {len(results['issues'])}")
        for issue in results["issues"]:
            print(f"  - {issue}")
    else:
        print("\nNo critical issues found!")

    return results


if __name__ == "__main__":
    check_env()