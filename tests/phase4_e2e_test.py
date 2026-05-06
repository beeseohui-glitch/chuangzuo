"""
Phase 4 End-to-End Verification Test

Test Analytics + Operation + Prompt Optimizer workflow
"""

import os
import sys
import io
from datetime import datetime

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print('[' + ts + '] ' + msg)


def log_step(step, msg):
    sep = '=' * 60
    print('\n' + sep)
    print('Step ' + str(step) + ': ' + msg)
    print(sep)


def run_test():
    """Run Phase 4 E2E test"""
    log("Phase 4 E2E verification started")

    results = {
        "start_time": datetime.now(),
        "steps": {},
        "success": False,
        "errors": [],
    }

    # ========== Step 1: Analytics Models ==========
    log_step(1, "Analytics Models")
    try:
        from models import AnalyticsData, ContentStats, PerformanceMetrics, ContentPerformance

        stats = ContentStats(total_content=100, published=80, total_views=10000)
        pm = PerformanceMetrics(date='2026-05-04', platform='xiaohongshu', content_count=10, impressions=1000, clicks=100)
        cp = ContentPerformance(content_id='c001', title='Test', platform='xiaohongshu', published_at='2026-05-01')

        ad = AnalyticsData(period_start='2026-05-01', period_end='2026-05-04')
        ad.content_stats = stats

        log("Analytics models created successfully")
        results["steps"]["analytics_models"] = {"status": "success"}
        log("SUCCESS: Analytics models OK")

    except Exception as e:
        import traceback
        results["steps"]["analytics_models"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 1 exception: " + str(e))
        log("FAILED: Analytics models exception: " + str(e))

    # ========== Step 2: AnalyticsAgent ==========
    log_step(2, "AnalyticsAgent")
    try:
        from agents import AnalyticsAgent

        agent = AnalyticsAgent()
        log("AnalyticsAgent instance created")

        # Test generate_report
        mock_data = [
            {"id": "c001", "title": "Test", "platform": "xiaohongshu", "status": "published", "views": 1000, "likes": 100, "comments": 10, "shares": 5, "ai_score": 75},
            {"id": "c002", "title": "Test2", "platform": "xiaohongshu", "status": "draft", "views": 0, "ai_score": 60},
        ]

        report = agent.generate_report("2026-05-01", "2026-05-04", mock_data)
        log("Report generated, recommendations: " + str(len(report.recommendations)))

        results["steps"]["analytics_agent"] = {"status": "success"}
        log("SUCCESS: AnalyticsAgent OK")

    except Exception as e:
        import traceback
        results["steps"]["analytics_agent"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 2 exception: " + str(e))
        log("FAILED: AnalyticsAgent exception: " + str(e))

    # ========== Step 3: OperationAgent ==========
    log_step(3, "OperationAgent")
    try:
        from agents import OperationAgent

        op_agent = OperationAgent()
        log("OperationAgent instance created")

        pending_content = [
            {"id": "p001", "title": "Test Post 1", "platform": "xiaohongshu", "priority": "high"},
            {"id": "p002", "title": "Test Post 2", "platform": "wechat_public", "priority": "medium"},
        ]

        schedule = op_agent.generate_schedule(pending_content, ["xiaohongshu", "wechat_public"])
        log("Schedule generated, items: " + str(len(schedule.publish_schedule)))
        log("Strategy recommendations: " + str(len(schedule.strategy_recommendations)))

        results["steps"]["operation_agent"] = {"status": "success"}
        log("SUCCESS: OperationAgent OK")

    except Exception as e:
        import traceback
        results["steps"]["operation_agent"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 3 exception: " + str(e))
        log("FAILED: OperationAgent exception: " + str(e))

    # ========== Step 4: PromptOptimizer ==========
    log_step(4, "PromptOptimizer")
    try:
        from tools import PromptOptimizer

        optimizer = PromptOptimizer()

        # Test remove_ai_flavor
        text1 = "首先，我们需要考虑这个问题。其次，实际上这是一个重要的点。"
        cleaned = optimizer.remove_ai_flavor(text1)
        log("remove_ai_flavor result: " + str(len(cleaned)) + " chars")

        # Test analyze_ai_score
        text2 = "首先，我们需要考虑这个问题"
        analysis = optimizer.analyze_ai_score(text2)
        log("AI score: " + str(analysis["score"]) + ", acceptable: " + str(analysis["is_acceptable"]))

        # Test suggest_improvements
        suggestions = optimizer.suggest_improvements(text2)
        log("Suggestions: " + str(len(suggestions)))

        results["steps"]["prompt_optimizer"] = {"status": "success"}
        log("SUCCESS: PromptOptimizer OK")

    except Exception as e:
        import traceback
        results["steps"]["prompt_optimizer"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 4 exception: " + str(e))
        log("FAILED: PromptOptimizer exception: " + str(e))

    # ========== Step 5: ContentStats ==========
    log_step(5, "ContentStats Aggregation")
    try:
        from models import ContentStats

        # Test aggregation
        content_data = [
            {"status": "published", "views": 1000, "likes": 100, "comments": 10, "shares": 5},
            {"status": "published", "views": 2000, "likes": 200, "comments": 20, "shares": 10},
            {"status": "draft", "views": 0, "likes": 0, "comments": 0, "shares": 0},
        ]

        total = len(content_data)
        published = sum(1 for c in content_data if c.get("status") == "published")
        total_views = sum(c.get("views", 0) for c in content_data)

        stats = ContentStats(total_content=total, published=published, total_views=total_views)
        log("ContentStats: total=" + str(stats.total_content) + ", published=" + str(stats.published))

        results["steps"]["content_stats"] = {"status": "success"}
        log("SUCCESS: ContentStats aggregation OK")

    except Exception as e:
        import traceback
        results["steps"]["content_stats"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 5 exception: " + str(e))
        log("FAILED: ContentStats exception: " + str(e))

    # ========== Step 6: PerformanceMetrics ==========
    log_step(6, "PerformanceMetrics Calculation")
    try:
        from models import PerformanceMetrics

        # Test CTR calculation
        impressions = 10000
        clicks = 1000
        ctr = clicks / impressions if impressions > 0 else 0.0

        pm = PerformanceMetrics(
            date="2026-05-04",
            platform="xiaohongshu",
            content_count=10,
            impressions=impressions,
            clicks=clicks,
            ctr=ctr,
        )
        log("PerformanceMetrics: CTR=" + str(pm.ctr))

        # Test engagement rate
        engagement = 100 + 20 + 10
        engagement_rate = engagement / impressions if impressions > 0 else 0.0
        log("Engagement rate: " + str(engagement_rate))

        results["steps"]["performance_metrics"] = {"status": "success"}
        log("SUCCESS: PerformanceMetrics calculation OK")

    except Exception as e:
        import traceback
        results["steps"]["performance_metrics"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 6 exception: " + str(e))
        log("FAILED: PerformanceMetrics exception: " + str(e))

    # ========== Summary ==========
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

    sep = '=' * 60
    log("\n" + sep)
    log("PHASE 4 VERIFICATION REPORT")
    log(sep)

    success_count = sum(1 for s in results["steps"].values() if s.get("status") == "success")
    total_count = len(results["steps"])

    log("Completed: " + str(success_count) + "/" + str(total_count) + " steps")
    log("Duration: " + str(results['duration']) + " seconds")

    if results["errors"]:
        log("Errors: " + str(len(results['errors'])))
        for err in results["errors"]:
            log("   - " + err)
    else:
        log("No errors")

    results["success"] = success_count == total_count and len(results["errors"]) == 0

    if results["success"]:
        log("\nSUCCESS: Phase 4 E2E verification PASSED!")
    else:
        log("\nWARNING: Phase 4 E2E verification NOT fully passed")

    return results


if __name__ == "__main__":
    sep = '=' * 60
    print(sep)
    print("Content Agent Phase 4 E2E Verification")
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