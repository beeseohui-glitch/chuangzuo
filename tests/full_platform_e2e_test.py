"""
Full Platform E2E Verification Test

Tests complete workflow: 小红书 + 公众号 + 抖音
"""

import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print('[' + ts + '] ' + msg)


def log_section(name):
    sep = '=' * 60
    print('\n' + sep)
    print(name)
    print(sep)


def run_test():
    """Run full platform E2E test"""
    log("Full Platform E2E Verification Started")

    results = {
        "start_time": datetime.now(),
        "platforms": {},
        "success": False,
        "errors": [],
    }

    # ========== 小红书平台测试 ==========
    log_section("Platform 1: 小红书 (Xiaohongshu)")
    try:
        from agents import TitleAgent, ArticleAgent, TagAgent
        from models import MaterialPack, BrandInfo, ProductInfo, PersonaInfo

        # 创建测试素材包
        material = MaterialPack(
            brand=BrandInfo(name="护肝宝", taboos=["最便宜", "第一"]),
            product=ProductInfo(
                name="护肝片",
                selling_points=["护肝", "熬夜必备", "天然成分"],
                ingredients=["水飞蓟", "B族维生素"],
            ),
            persona=PersonaInfo(profile="30-50岁白领"),
        )

        # 标题生成
        title_agent = TitleAgent()
        title_output = title_agent.generate(
            topic="护肝片种草",
            material_pack=material.model_dump(),
        )

        if title_output.titles:
            selected_title = title_output.titles[0].title
            log("XHS Title generated: " + selected_title)

            # 正文生成
            article_agent = ArticleAgent()
            note_output = article_agent.generate(
                title=selected_title,
                material_pack=material.model_dump(),
            )
            log("XHS Article generated: " + str(len(note_output.article)) + " chars")

            # 标签生成
            tag_agent = TagAgent()
            tags = tag_agent.generate(
                article=note_output.article,
                title=selected_title,
                material_pack=material.model_dump(),
            )
            log("XHS Tags generated: " + str(len(tags)) + " tags")

            results["platforms"]["xiaohongshu"] = {
                "status": "success",
                "title": selected_title,
                "article_length": len(note_output.article),
                "tags_count": len(tags),
            }
            log("[OK] Xiaohongshu platform: SUCCESS")
        else:
            results["platforms"]["xiaohongshu"] = {"status": "failed"}
            results["errors"].append("XHS: No titles generated")
            log("[FAIL] Xiaohongshu: No titles")

    except Exception as e:
        import traceback
        results["platforms"]["xiaohongshu"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("XHS exception: " + str(e))
        log("[FAIL] Xiaohongshu exception: " + str(e)[:100])

    # ========== 公众号平台测试 ==========
    log_section("Platform 2: 公众号 (Wechat Public)")
    try:
        from agents import WechatArticleAgent
        from models import MaterialPack, BrandInfo, ProductInfo, PersonaInfo

        material = MaterialPack(
            brand=BrandInfo(name="护肝宝", taboos=["最便宜", "第一"]),
            product=ProductInfo(
                name="护肝片",
                selling_points=["护肝", "熬夜必备", "天然成分"],
                ingredients=["水飞蓟", "B族维生素"],
            ),
            persona=PersonaInfo(profile="30-50岁白领"),
        )

        wechat_agent = WechatArticleAgent()
        public_content = wechat_agent.generate_article(
            title="护肝片：职场人群的健康守护神",
            material_pack=material.model_dump(),
            target_length="medium",
        )

        log("Wechat Article generated: " + str(len(public_content.article.content)) + " chars")
        log("AI Flavor Score: " + str(public_content.ai_flavor_score))

        results["platforms"]["wechat_public"] = {
            "status": "success",
            "title": public_content.article.title,
            "article_length": len(public_content.article.content),
            "ai_score": public_content.ai_flavor_score,
        }
        log("[OK] Wechat Public platform: SUCCESS")

    except Exception as e:
        results["platforms"]["wechat_public"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Wechat exception: " + str(e))
        log("[FAIL] Wechat Public exception: " + str(e)[:100])

    # ========== 抖音平台测试 ==========
    log_section("Platform 3: 抖音 (Douyin)")
    try:
        from agents import DouyinScriptAgent
        from models import MaterialPack, BrandInfo, ProductInfo, PersonaInfo

        material = MaterialPack(
            brand=BrandInfo(name="护肝宝", taboos=["最便宜", "第一"]),
            product=ProductInfo(
                name="护肝片",
                selling_points=["护肝", "熬夜必备", "天然成分"],
                ingredients=["水飞蓟", "B族维生素"],
            ),
            persona=PersonaInfo(profile="30-50岁白领"),
        )

        douyin_agent = DouyinScriptAgent()
        douyin_content = douyin_agent.generate_script(
            topic="护肝片种草",
            material_pack=material.model_dump(),
            duration_seconds=60,
        )

        log("Douyin Script generated: " + str(len(douyin_content.video.script.script_content)) + " chars")
        log("Duration: " + str(douyin_content.video.script.duration_seconds) + "s")
        log("Hashtags: " + str(len(douyin_content.video.hashtags)))

        results["platforms"]["douyin"] = {
            "status": "success",
            "title": douyin_content.video.title,
            "script_length": len(douyin_content.video.script.script_content),
            "duration": douyin_content.video.script.duration_seconds,
        }
        log("[OK] Douyin platform: SUCCESS")

    except Exception as e:
        results["platforms"]["douyin"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Douyin exception: " + str(e))
        log("[FAIL] Douyin exception: " + str(e)[:100])

    # ========== 跨平台分发测试 ==========
    log_section("Platform 4: Cross-Platform Publishing")
    try:
        from tools import MultiPlatformPublisher

        publisher = MultiPlatformPublisher()

        # 发布到三个平台
        results_list = publisher.publish_multi_platform(
            xhs_content={"title": "Test XHS", "content": "Test content"},
            wechat_content={"title": "Test Wechat", "content": "Test content"},
            douyin_content={"title": "Test Douyin", "script": "Test script"},
        )

        success_count = sum(1 for r in results_list if r.status == "published")
        log("Published to " + str(success_count) + "/" + str(len(results_list)) + " platforms")

        results["platforms"]["cross_platform"] = {
            "status": "success" if success_count == len(results_list) else "partial",
            "published_count": success_count,
            "total": len(results_list),
        }
        log("[OK] Cross-platform publishing: SUCCESS")

    except Exception as e:
        results["platforms"]["cross_platform"] = {
            "status": "error",
            "exception": str(e),
        }
        results["errors"].append("Cross-platform exception: " + str(e))
        log("[FAIL] Cross-platform publishing exception: " + str(e)[:100])

    # ========== Summary ==========
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

    log_section("FULL PLATFORM VERIFICATION REPORT")

    success_count = sum(1 for p in results["platforms"].values() if p.get("status") == "success")
    total_count = len(results["platforms"])

    log("Completed: " + str(success_count) + "/" + str(total_count) + " platforms")
    log("Duration: " + str(results['duration']) + " seconds")

    if results["errors"]:
        log("Errors: " + str(len(results["errors"])))
        for err in results["errors"][:5]:
            log("   - " + err[:100])

    results["success"] = success_count == total_count and len(results["errors"]) == 0

    if results["success"]:
        log("\n[SUCCESS] Full Platform E2E verification PASSED!")
    else:
        log("\n[PARTIAL] Full Platform E2E verification PARTIALLY PASSED")

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Content Agent Full Platform E2E Verification")
    print("(Xiaohongshu + Wechat Public + Douyin)")
    print("=" * 60)

    results = run_test()

    print("\n" + "=" * 60)
    print("Results JSON:")
    print("=" * 60)
    import json
    print(json.dumps({
        "success": results["success"],
        "duration": results.get("duration"),
        "platforms": {k: v.get("status") for k, v in results["platforms"].items()},
        "errors": results["errors"][:3],
    }, ensure_ascii=False, indent=2))