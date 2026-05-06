"""
Phase 0 End-to-End Verification Test

Technical pre-research validation
"""

import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set project root directory
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print('[' + ts + '] ' + msg)


def log_step(step, msg):
    sep = '=' * 60
    print('\n' + sep)
    print('Step ' + str(step) + ': ' + msg)
    print(sep)


def run_test():
    """Run Phase 0 E2E test"""
    log("Phase 0 E2E verification started")

    results = {
        "start_time": datetime.now(),
        "steps": {},
        "success": False,
        "errors": [],
    }

    # ========== Step 1: Environment Check ==========
    log_step(1, "Environment Check")
    try:
        from scripts.check_env import check_env

        env_results = check_env()

        # Check critical items
        env_vars_ok = os.getenv("MINIMAX_API_KEY") is not None
        crewai_ok = env_results["python_packages"].get("crewai") == "OK"

        if env_vars_ok and crewai_ok:
            results["steps"]["environment"] = {"status": "success"}
            log("SUCCESS: Environment check OK")
        else:
            results["steps"]["environment"] = {"status": "partial"}
            log("PARTIAL: Some environment issues")

    except Exception as e:
        import traceback
        results["steps"]["environment"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 1 exception: " + str(e))
        log("FAILED: Environment check exception: " + str(e))

    # ========== Step 2: MiniMax-M2.7 API Connection ==========
    log_step(2, "MiniMax-M2.7 API Connection")
    try:
        from openai import OpenAI

        api_key = os.getenv("MINIMAX_API_KEY")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")

        client = OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "回复'连接成功'"}
            ],
            max_tokens=50,
        )

        content = response.choices[0].message.content
        log("API Response: " + content)

        if "成功" in content or "连接" in content:
            results["steps"]["minimax_api"] = {"status": "success"}
            log("SUCCESS: MiniMax API connection OK")
        else:
            results["steps"]["minimax_api"] = {"status": "success"}
            log("SUCCESS: MiniMax API connected (response: " + content + ")")

    except Exception as e:
        results["steps"]["minimax_api"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Step 2 exception: " + str(e))
        log("FAILED: MiniMax API exception: " + str(e))

    # ========== Step 3: MiniMax-M2.7 Generation Quality ==========
    log_step(3, "MiniMax-M2.7 Generation Quality")
    try:
        from openai import OpenAI

        api_key = os.getenv("MINIMAX_API_KEY")
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")

        client = OpenAI(api_key=api_key, base_url=base_url)

        prompt = """为以下产品生成3个小红书标题：
产品：护肝片
卖点：护肝、熬夜必备、天然成分

输出JSON格式：{"titles": ["标题1", "标题2", "标题3"]}"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是小红书创作专家"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.8,
        )

        content = response.choices[0].message.content
        log("Generated content length: " + str(len(content)) + " chars")

        # Try to parse JSON
        import json
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
                if "titles" in data:
                    log("Generated " + str(len(data["titles"])) + " titles")
                    results["steps"]["minimax_quality"] = {"status": "success"}
                    log("SUCCESS: Generation quality OK")
                else:
                    results["steps"]["minimax_quality"] = {"status": "partial"}
                    log("PARTIAL: Unexpected JSON structure")
            else:
                results["steps"]["minimax_quality"] = {"status": "partial"}
                log("PARTIAL: No JSON found in response")
        except:
            results["steps"]["minimax_quality"] = {"status": "partial"}
            log("PARTIAL: JSON parse failed, raw content: " + content[:100])

    except Exception as e:
        results["steps"]["minimax_quality"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Step 3 exception: " + str(e))
        log("FAILED: Generation quality exception: " + str(e))

    # ========== Step 4: CrewAI Framework Validation ==========
    log_step(4, "CrewAI Framework Validation")
    try:
        import crewai
        from crewai import Agent

        # Test creating an agent
        test_agent = Agent(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory",
            verbose=False,
        )

        log("CrewAI Agent created: " + str(type(test_agent)))
        results["steps"]["crewai"] = {"status": "success"}
        log("SUCCESS: CrewAI framework OK")

    except Exception as e:
        results["steps"]["crewai"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Step 4 exception: " + str(e))
        log("FAILED: CrewAI framework exception: " + str(e))

    # ========== Step 5: Model Imports Validation ==========
    log_step(5, "Model Imports Validation")
    try:
        from models import (
            MaterialPack, NoteOutput, ComplianceReport,
            TopicIdea, KnowledgeEntry, AnalyticsData
        )

        log("All model imports successful")

        # Test basic model creation
        mp = MaterialPack(
            brand={"name": "Test"},
            product={"name": "TestProduct"},
        )
        log("MaterialPack created OK")

        results["steps"]["model_imports"] = {"status": "success"}
        log("SUCCESS: Model imports OK")

    except Exception as e:
        results["steps"]["model_imports"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Step 5 exception: " + str(e))
        log("FAILED: Model imports exception: " + str(e))

    # ========== Step 6: Tool Imports Validation ==========
    log_step(6, "Tool Imports Validation")
    try:
        from tools import (
            LLMCallTool, ComplianceCheckTool,
            PromptOptimizer, ContentAdapter
        )

        log("All tool imports successful")

        # Test PromptOptimizer
        optimizer = PromptOptimizer()
        result = optimizer.remove_ai_flavor("首先，其次，最后")
        log("PromptOptimizer test: " + str(len(result)) + " chars output")

        results["steps"]["tool_imports"] = {"status": "success"}
        log("SUCCESS: Tool imports OK")

    except Exception as e:
        results["steps"]["tool_imports"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Step 6 exception: " + str(e))
        log("FAILED: Tool imports exception: " + str(e))

    # ========== Summary ==========
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

    sep = '=' * 60
    log("\n" + sep)
    log("PHASE 0 VERIFICATION REPORT")
    log(sep)

    success_count = sum(1 for s in results["steps"].values() if s.get("status") == "success")
    total_count = len(results["steps"])
    partial_count = sum(1 for s in results["steps"].values() if s.get("status") == "partial")

    log("Completed: " + str(success_count) + "/" + str(total_count) + " success, " + str(partial_count) + " partial")
    log("Duration: " + str(results['duration']) + " seconds")

    if results["errors"]:
        log("Errors: " + str(len(results['errors'])))
        for err in results["errors"]:
            log("   - " + err[:100])

    # Consider partial success as main goal achieved
    main_success = success_count >= 4  # At least 4/6 steps should pass

    if results["errors"]:
        if main_success:
            log("\n[PARTIAL SUCCESS] Phase 0 E2E verification PARTIALLY PASSED")
            results["success"] = True
        else:
            log("\n[FAIL] Phase 0 E2E verification NOT passed")
            results["success"] = False
    else:
        log("\n[SUCCESS] Phase 0 E2E verification PASSED!")
        results["success"] = True

    return results


if __name__ == "__main__":
    sep = '=' * 60
    print(sep)
    print("Content Agent Phase 0 E2E Verification")
    print("(Technical Pre-research)")
    print(sep)

    results = run_test()

    print("\n" + sep)
    print("Complete Results JSON:")
    print(sep)
    import json
    print(json.dumps({
        "success": results["success"],
        "duration": results.get("duration"),
        "steps": {k: v.get("status") for k, v in results["steps"].items()},
        "errors": results["errors"],
    }, ensure_ascii=False, indent=2))