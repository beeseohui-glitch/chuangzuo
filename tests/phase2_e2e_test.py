"""
Phase 2 End-to-End Verification Test

Run the complete flow to verify all components are working correctly
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def log_step(step, msg):
    print(f"\n{'='*60}")
    print(f"Step {step}: {msg}")
    print('='*60)

def run_test():
    """Run end-to-end test"""
    log("Phase 2 E2E verification started")

    results = {
        "start_time": datetime.now(),
        "steps": {},
        "success": False,
        "errors": [],
    }

    # ========== Step 1: Orchestrator Agent Routing ==========
    log_step(1, "Orchestrator Agent Routing Verification")
    try:
        from flows.main_flow import MainFlow

        flow = MainFlow()
        user_input = {
            "text": "帮我为XX品牌的小红书写一篇护肝保健品笔记",
            "enterprise_id": "test_ent_001",
        }

        route_result = flow.route(user_input)
        log(f"Route result: {route_result}")

        if route_result.get("needs_clarification"):
            results["steps"]["route"] = {
                "status": "clarification_needed",
                "question": route_result.get("question"),
            }
            log(f"WARNING: Needs clarification: {route_result.get('question')}")
            # Retry with clearer input
            user_input["text"] = "帮我写一篇护肝片的小红书笔记"
            route_result = flow.route(user_input)
            log(f"Retry route result: {route_result}")

        platform = route_result.get("platform")
        if platform:
            platform_str = platform.value if hasattr(platform, 'value') else str(platform)
            results["steps"]["route"] = {
                "status": "success",
                "platform": platform_str,
            }
            log(f"SUCCESS: Routing OK: {platform_str}")
        else:
            results["steps"]["route"] = {
                "status": "failed",
                "error": "Cannot identify platform",
            }
            results["errors"].append("Step 1: Platform routing failed")
            log("FAILED: Routing failed")
            return results

    except Exception as e:
        import traceback
        results["steps"]["route"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 1 exception: {str(e)}")
        log(f"FAILED: Routing exception: {e}")
        return results

    # ========== Step 2: Material Search ==========
    log_step(2, "Material Search Verification")
    try:
        from flows.xiaohongshu_flow import XiaohongshuFlow
        from models import MaterialPack

        xhs_flow = XiaohongshuFlow()

        material_pack = xhs_flow.material_search({
            "product": "护肝片",
            "scene": "熬夜",
            "persona": "职场人群",
            "enterprise_id": "test_ent_001",
        })

        log(f"Material pack type: {type(material_pack)}")
        if isinstance(material_pack, MaterialPack):
            results["steps"]["material_search"] = {
                "status": "success",
                "product": material_pack.product.name if material_pack.product else "Unknown",
            }
            log(f"SUCCESS: Material search OK: {material_pack.product.name if material_pack.product else 'Unknown'}")
        else:
            results["steps"]["material_search"] = {
                "status": "failed",
                "type": str(type(material_pack)),
            }
            results["errors"].append("Step 2: Material pack type error")
            log(f"FAILED: Material pack type error: {type(material_pack)}")

    except Exception as e:
        import traceback
        results["steps"]["material_search"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 2 exception: {str(e)}")
        log(f"FAILED: Material search exception: {e}")
        # Continue but use mock data

    # ========== Step 3: Title Generation ==========
    log_step(3, "Title Generation Verification")
    try:
        from models import MaterialPack as MP, BrandInfo, ProductInfo, PersonaInfo

        # Use the retrieved material pack or create mock data
        if results["steps"].get("material_search", {}).get("status") == "success":
            mp = material_pack
        else:
            mp = MP(
                brand=BrandInfo(name="XX品牌", taboos=["最便宜", "第一"]),
                product=ProductInfo(
                    name="护肝片",
                    selling_points=["护肝", "熬夜必备", "天然成分"],
                ),
                persona=PersonaInfo(profile="职场人群"),
            )

        title_output = xhs_flow.title_generation(mp)
        log(f"Title output type: {type(title_output)}")

        if hasattr(title_output, 'titles') and len(title_output.titles) > 0:
            results["steps"]["title_generation"] = {
                "status": "success",
                "count": len(title_output.titles),
                "titles": [t.title for t in title_output.titles[:3]],
            }
            log(f"SUCCESS: Generated {len(title_output.titles)} titles")
            for t in title_output.titles[:3]:
                log(f"   - {t.title} ({t.strategy})")
        else:
            results["steps"]["title_generation"] = {
                "status": "failed",
            }
            results["errors"].append("Step 3: Title generation failed")
            log("FAILED: Title generation failed")

    except Exception as e:
        import traceback
        results["steps"]["title_generation"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 3 exception: {str(e)}")
        log(f"FAILED: Title generation exception: {e}")

    # ========== Step 4: Article Generation + AI Flavor Score ==========
    log_step(4, "Article Generation + AI Flavor Score Verification")
    try:
        if 'title_output' in dir() and title_output and hasattr(title_output, 'titles') and title_output.titles:
            note_output = xhs_flow.article_generation(title_output)
            log(f"Note output type: {type(note_output)}")

            if hasattr(note_output, 'article') and note_output.article:
                ai_score = getattr(note_output, 'ai_flavor_score', 0)
                results["steps"]["article_generation"] = {
                    "status": "success",
                    "article_length": len(note_output.article),
                    "ai_flavor_score": ai_score,
                }
                log(f"SUCCESS: Article generated ({len(note_output.article)} chars)")
                log(f"   AI flavor score: {ai_score}/100")

                if ai_score < 70:
                    log(f"WARNING: AI flavor score < 70 (required >= 70)")
            else:
                results["steps"]["article_generation"] = {
                    "status": "failed",
                }
                results["errors"].append("Step 4: Article generation empty")
                log("FAILED: Article generation failed")
        else:
            results["steps"]["article_generation"] = {
                "status": "skipped",
                "reason": "No valid titles",
            }
            log("SKIPPED: Article generation (no valid titles)")

    except Exception as e:
        import traceback
        results["steps"]["article_generation"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 4 exception: {str(e)}")
        log(f"FAILED: Article generation exception: {e}")

    # ========== Step 5: Tag Generation ==========
    log_step(5, "Tag Generation Verification")
    try:
        if 'note_output' in dir() and note_output and hasattr(note_output, 'article') and note_output.article:
            tags = xhs_flow.tag_generation({
                "note_output": note_output,
            })
            log(f"Tags output type: {type(tags)}, content: {tags}")

            if isinstance(tags, list) and len(tags) >= 8:
                results["steps"]["tag_generation"] = {
                    "status": "success",
                    "count": len(tags),
                    "tags": tags[:10],
                }
                log(f"SUCCESS: Generated {len(tags)} tags")
                log(f"   {', '.join(tags[:5])}...")
            elif isinstance(tags, list) and len(tags) > 0:
                results["steps"]["tag_generation"] = {
                    "status": "partial",
                    "count": len(tags),
                    "tags": tags,
                }
                log(f"WARNING: Tag count insufficient: {len(tags)} (required 8-10)")
            else:
                results["steps"]["tag_generation"] = {
                    "status": "failed",
                }
                results["errors"].append("Step 5: Tag generation failed")
                log("FAILED: Tag generation failed")
        else:
            results["steps"]["tag_generation"] = {
                "status": "skipped",
                "reason": "No valid article",
            }
            log("SKIPPED: Tag generation (no valid article)")

    except Exception as e:
        import traceback
        results["steps"]["tag_generation"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 5 exception: {str(e)}")
        log(f"FAILED: Tag generation exception: {e}")

    # ========== Step 6: Compliance Check ==========
    log_step(6, "Compliance Check Verification")
    try:
        if 'note_output' in dir() and note_output and hasattr(note_output, 'article') and note_output.article:
            compliance_result = xhs_flow.validate_and_compliance(note_output)
            log(f"Compliance result type: {type(compliance_result)}")

            if isinstance(compliance_result, dict):
                compliance_report = compliance_result.get("compliance_report")
                article_validation = compliance_result.get("article_validation")

                passed = article_validation.passed if article_validation else False
                results["steps"]["compliance_check"] = {
                    "status": "success",
                    "passed": passed,
                }
                log(f"SUCCESS: Compliance check completed")
                log(f"   Validation passed: {passed}")
                if article_validation and article_validation.issues:
                    log(f"   Issues: {article_validation.issues}")
            else:
                results["steps"]["compliance_check"] = {
                    "status": "failed",
                }
                results["errors"].append("Step 6: Compliance check failed")
                log("FAILED: Compliance check failed")
        else:
            results["steps"]["compliance_check"] = {
                "status": "skipped",
                "reason": "No valid article",
            }
            log("SKIPPED: Compliance check (no valid article)")

    except Exception as e:
        import traceback
        results["steps"]["compliance_check"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 6 exception: {str(e)}")
        log(f"FAILED: Compliance check exception: {e}")

    # ========== Step 7: Final Output ==========
    log_step(7, "Final Output Verification")
    try:
        final_output = xhs_flow.final_output(tags if 'tags' in dir() else [])
        log(f"Final output type: {type(final_output)}")

        if isinstance(final_output, dict):
            results["steps"]["final_output"] = {
                "status": "success",
                "success": final_output.get("success", False),
                "has_note_output": "note_output" in final_output,
                "has_tags": "tags" in final_output and len(final_output.get("tags", [])) > 0,
                "has_compliance_report": "compliance_report" in final_output,
            }
            log(f"SUCCESS: Final output completed")
            log(f"   Success flag: {final_output.get('success', False)}")
            log(f"   Has note output: {'note_output' in final_output}")
            log(f"   Has tags: {'tags' in final_output and len(final_output.get('tags', [])) > 0}")
            log(f"   Has compliance report: {'compliance_report' in final_output}")
        else:
            results["steps"]["final_output"] = {
                "status": "failed",
            }
            results["errors"].append("Step 7: Final output failed")
            log("FAILED: Final output failed")

    except Exception as e:
        import traceback
        results["steps"]["final_output"] = {
            "status": "error",
            "exception": str(e),
            "traceback": traceback.format_exc(),
        }
        results["errors"].append(f"Step 7 exception: {str(e)}")
        log(f"FAILED: Final output exception: {e}")

    # ========== Summary ==========
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

    log("\n" + "="*60)
    log("VERIFICATION REPORT SUMMARY")
    log("="*60)

    success_count = sum(1 for s in results["steps"].values() if s.get("status") == "success")
    total_count = len(results["steps"])

    log(f"Completed: {success_count}/{total_count} steps")
    log(f"Duration: {results['duration']:.1f} seconds")

    if results["errors"]:
        log(f"Errors: {len(results['errors'])}")
        for err in results["errors"]:
            log(f"   - {err}")
    else:
        log("No errors")

    results["success"] = success_count == total_count and len(results["errors"]) == 0

    if results["success"]:
        log("\nSUCCESS: Phase 2 E2E verification PASSED!")
    else:
        log("\nWARNING: Phase 2 E2E verification NOT fully passed")

    return results


if __name__ == "__main__":
    print("="*60)
    print("Content Agent Phase 2 E2E Verification")
    print("="*60)

    results = run_test()

    print("\n" + "="*60)
    print("Complete Results JSON:")
    print("="*60)
    import json
    print(json.dumps({
        "success": results["success"],
        "duration": results.get("duration"),
        "steps": {k: v.get("status") for k, v in results["steps"].items()},
        "errors": results["errors"],
    }, ensure_ascii=False, indent=2))