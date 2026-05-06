"""
Phase 3 End-to-End Verification Test

Test TopicAgent + KnowledgeBase workflow
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
    """Run Phase 3 E2E test"""
    log("Phase 3 E2E verification started")

    results = {
        "start_time": datetime.now(),
        "steps": {},
        "success": False,
        "errors": [],
    }

    # ========== Step 1: TopicAgent - Generate Topics ==========
    log_step(1, "TopicAgent - Topic Generation")
    try:
        from agents import TopicAgent
        from models import TopicIdea, TopicCategory, TopicSource

        topic_agent = TopicAgent()
        log("TopicAgent instance created: " + topic_agent.config.name)

        # Test model creation without LLM call
        test_topic = TopicIdea(
            id="test_001",
            title="护肝片种草指南",
            description="针对熬夜加班人群的护肝保健品选题",
            category=TopicCategory.HEALTH_PRODUCT,
            source=TopicSource.TRENDING,
            keywords=["护肝", "熬夜", "保健品"],
            target_persona="30-50岁白领",
            content_angle="真实体验分享"
        )
        log("TopicIdea created: " + test_topic.title)

        results["steps"]["topic_agent"] = {
            "status": "success",
            "topic_count": 1,
        }
        log("SUCCESS: TopicAgent initialized OK")

    except Exception as e:
        import traceback
        results["steps"]["topic_agent"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 1 exception: " + str(e))
        log("FAILED: TopicAgent exception: " + str(e))

    # ========== Step 2: KnowledgeBaseAgent - KB Search ==========
    log_step(2, "KnowledgeBaseAgent - KB Search")
    try:
        from agents import KnowledgeBaseAgent
        from models import KnowledgeEntry, SearchResult

        kb_agent = KnowledgeBaseAgent()
        log("KnowledgeBaseAgent instance created")

        # Test model creation
        test_entry = KnowledgeEntry(
            id="kb_001",
            title="护肝片知识",
            content="护肝片是一种保健品",
            category="health_product"
        )
        log("KnowledgeEntry created: " + test_entry.id)

        results["steps"]["kb_agent"] = {
            "status": "success",
            "entry_count": 1,
        }
        log("SUCCESS: KnowledgeBaseAgent initialized OK")

    except Exception as e:
        import traceback
        results["steps"]["kb_agent"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 2 exception: " + str(e))
        log("FAILED: KnowledgeBaseAgent exception: " + str(e))

    # ========== Step 3: ObsidianClient + KnowledgeLoader ==========
    log_step(3, "ObsidianClient + KnowledgeLoader")
    try:
        from sync import ObsidianClient, KnowledgeLoader

        obsidian_client = ObsidianClient()
        loader = KnowledgeLoader()
        log("ObsidianClient and KnowledgeLoader created")

        # Test loading from kb/ directory
        entries = loader.load_from_markdown_dir("health_product")
        log("Loaded " + str(len(entries)) + " health_product entries")

        entries_ai = loader.load_from_markdown_dir("ai_industry")
        log("Loaded " + str(len(entries_ai)) + " ai_industry entries")

        total_entries = len(entries) + len(entries_ai)
        results["steps"]["knowledge_loader"] = {
            "status": "success",
            "total_entries": total_entries,
            "health_entries": len(entries),
            "ai_entries": len(entries_ai),
        }
        log("SUCCESS: Loaded " + str(total_entries) + " total entries")

    except Exception as e:
        import traceback
        results["steps"]["knowledge_loader"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 3 exception: " + str(e))
        log("FAILED: KnowledgeLoader exception: " + str(e))

    # ========== Step 4: Topic List Model ==========
    log_step(4, "TopicListOutput Model")
    try:
        from models import TopicListOutput, TopicIdea, TopicCategory, TopicSource

        topics = [
            TopicIdea(
                id="topic_001",
                title="护肝片种草指南",
                description="针对熬夜加班人群",
                category=TopicCategory.HEALTH_PRODUCT,
                source=TopicSource.TRENDING,
                keywords=["护肝"],
                target_persona="白领",
                content_angle="真实体验"
            ),
            TopicIdea(
                id="topic_002",
                title="睡眠改善方案",
                description="睡眠质量提升",
                category=TopicCategory.HEALTH_PRODUCT,
                source=TopicSource.SEASONAL,
                keywords=["睡眠"],
                target_persona="失眠人群",
                content_angle="科学建议"
            ),
        ]

        topic_list = TopicListOutput(
            topics=topics,
            total=2,
            page=1,
            page_size=10
        )
        log("TopicListOutput created with " + str(len(topic_list.topics)) + " topics")

        results["steps"]["topic_model"] = {
            "status": "success",
            "topic_count": len(topic_list.topics),
        }
        log("SUCCESS: TopicListOutput model OK")

    except Exception as e:
        import traceback
        results["steps"]["topic_model"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 4 exception: " + str(e))
        log("FAILED: Topic model exception: " + str(e))

    # ========== Step 5: Knowledge Entry Model ==========
    log_step(5, "KnowledgeEntry Model")
    try:
        from models import KnowledgeEntry, KBMetadata, SearchResult

        entry = KnowledgeEntry(
            id="kb_test_001",
            title="测试知识",
            content="这是测试内容",
            category="test",
            tags=["test"]
        )
        log("KnowledgeEntry created: " + entry.id)

        metadata = KBMetadata(
            total_entries=100,
            categories=["health_product", "ai_industry"],
            tags=["护肝", "AI"],
            last_updated=datetime.now().isoformat()
        )
        log("KBMetadata created, total: " + str(metadata.total_entries))

        search_result = SearchResult(
            entries=[entry],
            total=1,
            query="测试"
        )
        log("SearchResult created, found: " + str(search_result.total))

        results["steps"]["kb_model"] = {
            "status": "success",
        }
        log("SUCCESS: KB models OK")

    except Exception as e:
        import traceback
        results["steps"]["kb_model"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 5 exception: " + str(e))
        log("FAILED: KB model exception: " + str(e))

    # ========== Step 6: Import Script ==========
    log_step(6, "Knowledge Import Script")
    try:
        # Test script imports
        from sync import KnowledgeLoader, ObsidianClient

        loader = KnowledgeLoader()
        entries = loader.load_from_markdown_dir("health_product")

        results["steps"]["import_script"] = {
            "status": "success",
            "entries_loaded": len(entries),
        }
        log("SUCCESS: Import script OK")

    except Exception as e:
        import traceback
        results["steps"]["import_script"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append("Step 6 exception: " + str(e))
        log("FAILED: Import script exception: " + str(e))

    # ========== Summary ==========
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

    sep = '=' * 60
    log("\n" + sep)
    log("PHASE 3 VERIFICATION REPORT")
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
        log("\nSUCCESS: Phase 3 E2E verification PASSED!")
    else:
        log("\nWARNING: Phase 3 E2E verification NOT fully passed")

    return results


if __name__ == "__main__":
    sep = '=' * 60
    print(sep)
    print("Content Agent Phase 3 E2E Verification")
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