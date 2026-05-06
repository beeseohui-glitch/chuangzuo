"""
知识库导入脚本
将 kb/ 目录下的知识文件导入到向量数据库
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sync import KnowledgeLoader, ObsidianClient


def import_knowledge_to_vector_db():
    """将知识导入向量数据库"""
    print("=" * 50)
    print("Knowledge Base Import Script")
    print("=" * 50)

    # 初始化组件
    loader = KnowledgeLoader()
    obsidian_client = ObsidianClient()

    # 知识库目录
    kb_dir = Path("kb")

    if not kb_dir.exists():
        print(f"错误: 知识库目录 {kb_dir} 不存在")
        return

    # 导入健康产品知识库
    print("\n[1] 导入健康产品知识库...")
    health_entries = loader.load_from_markdown_dir("health_product")
    print(f"    找到 {len(health_entries)} 条健康产品知识")

    # 导入AI行业知识库
    print("\n[2] 导入AI行业知识库...")
    ai_entries = loader.load_from_markdown_dir("ai_industry")
    print(f"    找到 {len(ai_entries)} 条AI行业知识")

    # 合并所有条目
    all_entries = health_entries + ai_entries
    print(f"\n总计: {len(all_entries)} 条知识条目")

    # 向量化并存储
    print("\n[3] 向量化处理...")
    print("    (Skipped - embedding requires running environment)")
    print(f"    待处理: {len(all_entries)} 条知识条目")

    # TODO: 存储到向量数据库（pgvector）
    # 这里先打印统计信息
    print("\n[4] 存储到向量数据库...")
    print("    (Skipped - pgvector storage pending)")

    # 打印知识库统计
    print("\n[5] 知识库统计:")
    print(f"    健康产品: {len(health_entries)} 条")
    print(f"    AI行业: {len(ai_entries)} 条")

    print("\n" + "=" * 50)
    print("导入完成!")
    print("=" * 50)


if __name__ == "__main__":
    import_knowledge_to_vector_db()