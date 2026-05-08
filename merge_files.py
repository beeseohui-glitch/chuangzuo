# merge_files.py — 放在项目根目录 D:\chuangzuo\ 运行
# python merge_files.py

import os

# 需要读取的所有文件（相对于项目根目录）
FILES = [
    # agents/
    "agents/base_agent.py",
    "agents/agent_chain.py",
    "agents/orchestrator_agent.py",
    "agents/topic_agent.py",
    "agents/title_agent.py",
    "agents/article_agent.py",
    "agents/tag_agent.py",
    "agents/compliance_agent.py",
    "agents/material_agent.py",
    "agents/kb_agent.py",
    "agents/analytics_agent.py",
    "agents/operation_agent.py",
    "agents/wechat_article_agent.py",
    "agents/douyin_script_agent.py",
    # agents/chains/
    "agents/chains/creation_chain.py",
    "agents/chains/compliance_chain.py",
    # api/
    "api/main.py",
    "api/auth.py",
    "api/db.py",
    "api/deps.py",
    "api/embedding_service.py",
    "api/flow_runner.py",
    "api/utils.py",
    "api/routes/agents.py",
    "api/routes/create.py",
    "api/routes/analytics.py",
    "api/routes/platform_knowledge.py",
    "api/routes/platform_tenants.py",
    "api/routes/tenant_knowledge.py",
    # flows/
    "flows/main_flow.py",
    "flows/xiaohongshu_flow.py",
    # prompts/
    "prompts/orchestrator.md",
    "prompts/topic_agent.md",
    "prompts/title_agent.md",
    "prompts/article_agent.md",
    "prompts/tag_agent.md",
    "prompts/compliance_agent.md",
    "prompts/material_search.md",
    "prompts/kb_agent.md",
    "prompts/analytics_agent.md",
    "prompts/operation_agent.md",
    "prompts/wechat_article_agent.md",
    "prompts/douyin_script_agent.md",
    # tasks/
    "tasks/title_task.py",
    "tasks/article_task.py",
    "tasks/tag_task.py",
    "tasks/compliance_task.py",
    "tasks/material_task.py",
    # crews/
    "crews/shared_crew.py",
    "crews/xiaohongshu_crew.py",
    # config/
    "config/llm_config.py",
    "config/agent_config.py",
    "config/platform_config.py",
    "config/vector_config.py",
    # tools/
    "tools/llm_tools.py",
    "tools/crewai_llm.py",
    "tools/prompt_tools.py",
    "tools/material_tools.py",
    "tools/embedding_tools.py",
    "tools/vector_tools.py",
    "tools/compliance_tools.py",
    "tools/cos_tools.py",
    "tools/obsidian_tools.py",
    "tools/cache_tools.py",
    "tools/multi_platform_publisher.py",
    "tools/content_adapter.py",
    "tools/prompt_optimizer.py",
    # validators/
    "validators/ai_flavor_scorer.py",
    "validators/result_validator.py",
    # models/
    "models/note_output.py",
    "models/material_pack.py",
    "models/compliance_report.py",
    "models/agent_message.py",
    "models/topic.py",
    # frontend
    "frontend/src/app/create/page.tsx",
    "frontend/src/app/tools/page.tsx",
    "frontend/src/app/tools/tools-content.tsx",
    "frontend/src/components/create/step-input.tsx",
    "frontend/src/components/create/step-topic.tsx",
    "frontend/src/components/create/step-material.tsx",
    "frontend/src/components/create/step-title.tsx",
    "frontend/src/components/create/step-article.tsx",
    "frontend/src/components/create/step-tags.tsx",
    "frontend/src/components/create/step-output.tsx",
    "frontend/src/components/create/preview-panel.tsx",
    "frontend/src/stores/create-store.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/nav-items.ts",
    "frontend/src/components/shared/agent-status.tsx",
    "frontend/src/components/shared/compliance-badge.tsx",
]

OUTPUT = "all_code_for_review.txt"

def main():
    found, missing = 0, []
    with open(OUTPUT, "w", encoding="utf-8") as out:
        for fpath in FILES:
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                out.write(f"\n{'='*60}\n")
                out.write(f"FILE: {fpath}\n")
                out.write(f"{'='*60}\n\n")
                out.write(content)
                out.write("\n")
                found += 1
                print(f"  [OK] {fpath}")
            else:
                missing.append(fpath)
                print(f"  [MISSING] {fpath}")

    print(f"\nDone: {found} files merged → {OUTPUT}")
    if missing:
        print(f"Missing {len(missing)} files:")
        for m in missing:
            print(f"  - {m}")

if __name__ == "__main__":
    main()
