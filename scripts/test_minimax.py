"""
MiniMax API 连接测试
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
load_dotenv(PROJECT_ROOT / ".env")


def test_minimax_connection():
    """测试MiniMax API连接"""
    print("=" * 60)
    print("MiniMax API Connection Test")
    print("=" * 60)

    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")

    print(f"\n[1] Configuration:")
    print(f"  API Key: {api_key[:10]}...{api_key[-4:] if api_key else 'NOT SET'}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")

    if not api_key:
        print("\nERROR: MINIMAX_API_KEY not set!")
        return False

    print("\n[2] Testing API Connection...")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        # 测试简单的chat completions
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个测试助手"},
                {"role": "user", "content": "你好，请回复'API连接成功'"}
            ],
            max_tokens=50,
            temperature=0.5,
        )

        print("\n[3] Response:")
        content = response.choices[0].message.content
        print(f"  {content}")

        if "成功" in content or "success" in content.lower():
            print("\n[OK] MiniMax API connection SUCCESS!")
            return True
        else:
            print("\n[?] API connected but unexpected response")
            return True

    except Exception as e:
        print(f"\n[FAIL] MiniMax API connection FAILED: {e}")
        return False


def test_generation_quality():
    """测试生成质量"""
    print("\n" + "=" * 60)
    print("Generation Quality Test")
    print("=" * 60)

    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        # 测试小红书标题生成
        test_prompt = """请为以下产品生成3个小红书标题：

产品：护肝片
卖点：护肝、熬夜必备、天然成分

要求：
- 15-20字
- 有吸引力
- 口语化

输出JSON格式：{"titles": [{"title": "标题", "reason": "理由"}]}"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是小红书内容创作专家"},
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=500,
            temperature=0.8,
        )

        print("\n[Test] Title Generation:")
        content = response.choices[0].message.content
        print(f"  Response length: {len(content)} chars")

        # 尝试解析JSON
        import json
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
                print(f"  JSON parsed OK")
                if "titles" in data:
                    print(f"  Generated {len(data['titles'])} titles")
                    for i, t in enumerate(data["titles"][:3], 1):
                        print(f"    {i}. {t.get('title', 'N/A')}")
        except:
            print(f"  Raw response: {content[:200]}...")

        print("\n[OK] Generation quality test completed")
        return True

    except Exception as e:
        print(f"\n[FAIL] Generation test FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_minimax_connection()
    if success:
        test_generation_quality()
    else:
        print("\nSkipping quality test due to connection failure")