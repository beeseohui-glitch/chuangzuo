"""
Phase 5 End-to-End Verification Test

Test Multi-Platform Content Creation and Publishing
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
    """Run Phase 5 E2E test"""
    log("Phase 5 E2E verification started")

    results = {
        "start_time": datetime.now(),
        "steps": {},
        "success": False,
        "errors": [],
    }

    # ========== Step 1: Platform Content Models ==========
    log_step(1, "Platform Content Models")
    try:
        from models import (
            WechatArticle, PublicAccountContent,
            DouyinScript, DouyinVideo, DouyinContent,
            MultiPlatformContent
        )

        # Test WechatArticle
        wa = WechatArticle(title="Test Article", content="<p>Test content</p>")
        log("WechatArticle created: " + wa.title)

        # Test DouyinScript
        ds = DouyinScript(
            title="Test Video",
            hooks="开场钩子",
            script_content="主体内容",
            cta="行动号召",
            duration_seconds=60
        )
        log("DouyinScript created: " + ds.title)

        # Test DouyinVideo
        dv = DouyinVideo(title="Test Video", script=ds)
        log("DouyinVideo created: " + dv.title)

        # Test MultiPlatformContent
        mpc = MultiPlatformContent(source_material_id="mat_001")
        log("MultiPlatformContent created")

        results["steps"]["platform_models"] = {"status": "success"}
        log("SUCCESS: Platform content models OK")

    except Exception as e:
        import traceback
        results["steps"]["platform_models"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 1 exception: " + str(e))
        log("FAILED: Platform models exception: " + str(e))

    # ========== Step 2: WechatArticleAgent ==========
    log_step(2, "WechatArticleAgent")
    try:
        from agents import WechatArticleAgent

        agent = WechatArticleAgent()
        log("WechatArticleAgent created")

        # Test article creation (without LLM call)
        article = agent.generate_article(
            title="Test Article",
            material_pack={
                "brand": {"name": "TestBrand"},
                "product": {"name": "TestProduct", "selling_points": ["point1"]},
                "persona": {"profile": "白领"}
            }
        )
        log("Article generated, status: " + article.compliance_status)

        results["steps"]["wechat_agent"] = {"status": "success"}
        log("SUCCESS: WechatArticleAgent OK")

    except Exception as e:
        import traceback
        results["steps"]["wechat_agent"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 2 exception: " + str(e))
        log("FAILED: WechatArticleAgent exception: " + str(e))

    # ========== Step 3: DouyinScriptAgent ==========
    log_step(3, "DouyinScriptAgent")
    try:
        from agents import DouyinScriptAgent

        agent = DouyinScriptAgent()
        log("DouyinScriptAgent created")

        # Test script generation (without LLM call)
        content = agent.generate_script(
            topic="Test Topic",
            material_pack={
                "brand": {"name": "TestBrand"},
                "product": {"name": "TestProduct", "selling_points": ["point1"]},
                "persona": {"profile": "白领"}
            }
        )
        log("Script generated, status: " + content.compliance_status)
        log("Duration: " + str(content.video.script.duration_seconds) + "s")

        results["steps"]["douyin_agent"] = {"status": "success"}
        log("SUCCESS: DouyinScriptAgent OK")

    except Exception as e:
        import traceback
        results["steps"]["douyin_agent"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 3 exception: " + str(e))
        log("FAILED: DouyinScriptAgent exception: " + str(e))

    # ========== Step 4: ContentAdapter ==========
    log_step(4, "ContentAdapter")
    try:
        from tools import ContentAdapter

        adapter = ContentAdapter()

        # Create mock NoteOutput
        class MockNoteOutput:
            title = "Test Title"
            article = "Test article content. More content here."
            tags = ["tag1", "tag2", "tag3"]
            ai_flavor_score = 80
            metadata = {"material_id": "mat_001"}

        source = MockNoteOutput()

        # Test adapt for wechat
        wechat = adapter.adapt_for_wechat_public(source)
        log("Wechat adapted, title: " + wechat.article.title)

        # Test adapt for douyin
        douyin = adapter.adapt_for_douyin(source, 60)
        log("Douyin adapted, hooks: " + douyin.hooks[:10])

        # Test create multi-platform
        mp_content = adapter.create_multi_platform_content(source)
        log("Multi-platform created")

        results["steps"]["content_adapter"] = {"status": "success"}
        log("SUCCESS: ContentAdapter OK")

    except Exception as e:
        import traceback
        results["steps"]["content_adapter"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 4 exception: " + str(e))
        log("FAILED: ContentAdapter exception: " + str(e))

    # ========== Step 5: MultiPlatformPublisher ==========
    log_step(5, "MultiPlatformPublisher")
    try:
        from tools import MultiPlatformPublisher, PublishStatus

        publisher = MultiPlatformPublisher()

        # Test publish to xiaohongshu
        xhs_result = publisher.publish_to_xiaohongshu({"title": "Test", "content": "Content"})
        log("Xiaohongshu publish: " + xhs_result.status)

        # Test publish to wechat
        wc_result = publisher.publish_to_wechat_public({"title": "Test", "content": "Content"})
        log("Wechat publish: " + wc_result.status)

        # Test publish to douyin
        dy_result = publisher.publish_to_douyin({"title": "Test", "script": "Script"})
        log("Douyin publish: " + dy_result.status)

        # Test multi-platform publish
        results_list = publisher.publish_multi_platform(
            xhs_content={"title": "Test"},
            wechat_content={"title": "Test"},
        )
        log("Multi-platform publish: " + str(len(results_list)) + " platforms")

        results["steps"]["publisher"] = {"status": "success"}
        log("SUCCESS: MultiPlatformPublisher OK")

    except Exception as e:
        import traceback
        results["steps"]["publisher"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 5 exception: " + str(e))
        log("FAILED: MultiPlatformPublisher exception: " + str(e))

    # ========== Step 6: Platform Config ==========
    log_step(6, "Platform Config Validation")
    try:
        from config import WechatPublicConfig, DouyinConfig

        wechat_config = WechatPublicConfig()
        log("WechatPublicConfig: max_article_length=" + str(wechat_config.max_article_length))

        douyin_config = DouyinConfig()
        log("DouyinConfig: max_script_length=" + str(douyin_config.max_script_length))

        results["steps"]["platform_config"] = {"status": "success"}
        log("SUCCESS: Platform config OK")

    except Exception as e:
        import traceback
        results["steps"]["platform_config"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 6 exception: " + str(e))
        log("FAILED: Platform config exception: " + str(e))

    # ========== Summary ==========
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

    sep = '=' * 60
    log("\n" + sep)
    log("PHASE 5 VERIFICATION REPORT")
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
        log("\nSUCCESS: Phase 5 E2E verification PASSED!")
    else:
        log("\nWARNING: Phase 5 E2E verification NOT fully passed")

    return results


if __name__ == "__main__":
    sep = '=' * 60
    print(sep)
    print("Content Agent Phase 5 E2E Verification")
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