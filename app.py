"""
智创笔记 - 多平台AI内容创作系统
手动编排版本 - Phase 1 验证用
"""

import os
import sys
import json
import re
from dotenv import load_dotenv
load_dotenv()

# 解决 Windows 控制台编码问题
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from tools.llm_tools import LLMCallTool
from tools.compliance_tools import ComplianceCheckTool
from models.material_pack import MaterialPack, BrandInfo, ProductInfo, PersonaInfo, SceneInfo, ComplianceRules
from models.note_output import NoteOutput, TitleOutput, Paragraph
from validators.ai_flavor_scorer import AIFlavorScorer


def create_material_pack() -> MaterialPack:
    """创建素材包"""
    return MaterialPack(
        brand=BrandInfo(
            name="护肝宝",
            tone=["健康", "天然"],
            taboos=["最便宜", "第一"]
        ),
        product=ProductInfo(
            name="护肝片",
            selling_points=["保护肝脏", "天然成分", "加班必备"],
            ingredients=["水飞蓟", "B族维生素"]
        ),
        persona=PersonaInfo(
            profile="30-50岁白领,关注健康养生",
            pain_points=["熬夜伤肝", "肝功能下降"]
        ),
        scene=[
            SceneInfo(
                description="加班熬夜场景",
                usage_method="每日一粒,饭后服用"
            )
        ],
        compliance=ComplianceRules(
            rules=["不允许绝对化用语", "不允许医疗断言"],
            forbidden_groups=["孕妇", "儿童"]
        )
    )


def generate_titles(llm: LLMCallTool, topic: str, material: MaterialPack) -> TitleOutput:
    """生成标题"""
    prompt = f"""请根据以下信息生成小红书标题：

选题方向：{topic}

素材包信息：
- 品牌：{material.brand.name}
- 产品：{material.product.name}
- 卖点：{', '.join(material.product.selling_points)}
- 人群：{material.persona.profile}

要求：
1. 生成5个不同策略的标题
2. 每个标题15-20字
3. 输出JSON格式

输出格式：
{{"titles": [{{"title": "标题", "strategy": "策略", "score": 8, "reason": "理由"}}]}}
"""
    result = llm._run(prompt=prompt, max_tokens=3000)

    # 解析JSON
    try:
        data = json.loads(result)
        return TitleOutput(**data)
    except json.JSONDecodeError as e:
        # 尝试从输出中提取JSON
        start = result.find('{')
        end = result.rfind('}') + 1
        if start != -1 and end > start:
            try:
                data = json.loads(result[start:end])
                return TitleOutput(**data)
            except json.JSONDecodeError:
                pass
        return TitleOutput(titles=[], warnings=[f"标题解析失败: {str(e)[:50]}"])


def generate_article(llm: LLMCallTool, title: str, material: MaterialPack) -> str:
    """生成正文"""
    prompt = f"""请根据以下信息生成小红书正文：

选定标题：{title}

素材包信息：
- 品牌：{material.brand.name}
- 产品：{material.product.name}
- 卖点：{', '.join(material.product.selling_points)}
- 成分：{', '.join(material.product.ingredients)}
- 人群：{material.persona.profile}
- 使用场景：{material.scene[0].description if material.scene else ''}

要求：
1. 字数300-500字
2. 口语化,有人味,不要AI味
3. 结构：痛点引入→产品发现→卖点展示→真实体验→互动引导
4. 不要使用绝对化用语

请直接输出正文,不需要JSON格式。
"""
    return llm._run(prompt=prompt, max_tokens=1500)


def generate_tags(llm: LLMCallTool, article: str, title: str) -> list[str]:
    """生成标签"""
    prompt = f"""请根据以下正文和标题,生成小红书标签：

标题：{title}

正文：{article[:200]}...

要求：
1. 生成8-12个标签
2. 每个标签2-5个字
3. 包含品类词、场景词、人群词、功效词
4. 输出JSON格式

输出格式：
{{"tags": ["标签1", "标签2", ...]}}
"""
    result = llm._run(prompt=prompt, max_tokens=2000, json_mode=False)

    # 解析JSON
    try:
        data = json.loads(result)
        return data.get("tags", [])
    except json.JSONDecodeError:
        # 尝试提取
        start = result.find('[')
        end = result.rfind(']') + 1
        if start != -1 and end > start:
            tags = json.loads(result[start:end])
            return tags
        return []


def check_compliance(compliance: ComplianceCheckTool, text: str) -> list:
    """合规检查"""
    return compliance._run(text=text, platform="xiaohongshu", check_type="all")


def run_content_creation(topic: str) -> NoteOutput:
    """运行完整内容创作流程"""
    print(f"\n{'='*50}")
    print(f"智创笔记 - 内容创作流程")
    print(f"{'='*50}")
    print(f"选题: {topic}")

    # 1. 创建素材包
    print(f"\n[1/6] 创建素材包...")
    material = create_material_pack()
    print(f"  品牌: {material.brand.name}")
    print(f"  产品: {material.product.name}")

    # 2. 初始化工具
    print(f"\n[2/6] 初始化工具...")
    llm = LLMCallTool()
    compliance = ComplianceCheckTool()
    scorer = AIFlavorScorer()
    print(f"  LLMCallTool: OK")
    print(f"  ComplianceCheckTool: OK")
    print(f"  AIFlavorScorer: OK")

    # 3. 生成标题
    print(f"\n[3/6] 生成标题...")
    title_output = generate_titles(llm, topic, material)
    if title_output.titles:
        print(f"  生成 {len(title_output.titles)} 个标题:")
        for i, t in enumerate(title_output.titles[:5], 1):
            print(f"    {i}. [{t.strategy}] {t.title}")
        selected_title = title_output.titles[0].title
    else:
        print(f"  标题生成失败: {title_output.warnings}")
        selected_title = "默认标题"

    # 4. 生成正文
    print(f"\n[4/6] 生成正文...")
    article = generate_article(llm, selected_title, material)
    print(f"  正文长度: {len(article)} 字")
    print(f"  预览: {article[:50]}...")

    # 5. AI味评分
    print(f"\n[5/6] AI味评分...")
    ai_score = scorer.score(article)
    print(f"  AI味评分: {ai_score}/100")

    # 6. 生成标签
    print(f"\n[6/6] 生成标签...")
    tags = generate_tags(llm, article, selected_title)
    print(f"  标签: {', '.join(tags[:5])}...")

    # 7. 合规检查
    print(f"\n[7/7] 合规检查...")
    compliance_issues = check_compliance(compliance, article)
    if compliance_issues:
        print(f"  发现 {len(compliance_issues)} 个合规问题:")
        for issue in compliance_issues:
            print(f"    - {issue}")
    else:
        print(f"  合规检查通过!")

    # 组装输出
    note = NoteOutput(
        title=selected_title,
        article=article,
        tags=tags,
        ai_flavor_score=ai_score,
        metadata={
            "topic": topic,
            "brand": material.brand.name,
            "product": material.product.name,
            "compliance_issues": len(compliance_issues)
        }
    )

    return note


if __name__ == "__main__":
    print("\n" + "="*50)
    print("智创笔记 Phase 1 端到端验证")
    print("="*50)

    result = run_content_creation("护肝片种草")

    print(f"\n{'='*50}")
    print("创作完成!")
    print(f"{'='*50}")
    print(f"标题: {result.title}")
    print(f"正文: {len(result.article)} 字")
    print(f"标签: {', '.join(result.tags)}")
    print(f"AI味评分: {result.ai_flavor_score}/100")

    # 保存结果
    with open("output_note.json", "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(ensure_ascii=False, indent=2))
    print(f"\n结果已保存到 output_note.json")
