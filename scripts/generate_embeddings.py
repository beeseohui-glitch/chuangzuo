"""
生成种子数据 embedding 脚本

对 knowledge_base 表中 embedding 为 NULL 的记录生成 1024 维向量。
使用 bge-large-zh-v1.5 模型（sentence-transformers）。

用法：
  python scripts/generate_embeddings.py            # 执行
  python scripts/generate_embeddings.py --dry-run   # 预览
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2
from tools.embedding_tools import LocalEmbeddingTool
from config.vector_config import VectorStoreConfig


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for knowledge_base records")
    parser.add_argument("--dry-run", action="store_true", help="Preview without updating")
    args = parser.parse_args()

    # 连接数据库
    config = VectorStoreConfig.from_env()
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
    )

    # 绕过 RLS：设置 agent 会话上下文
    with conn.cursor() as cur:
        cur.execute("SET app.is_agent = true")
    conn.commit()

    # 查询 embedding 为 NULL 的记录
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, content FROM knowledge_base WHERE embedding IS NULL"
        )
        rows = cur.fetchall()

    if not rows:
        print("No records with NULL embedding found.")
        conn.close()
        return

    print(f"Found {len(rows)} records with NULL embedding.")

    if args.dry_run:
        print("\n[DRY RUN] Records to update:")
        for row_id, title, content in rows:
            preview = (content or "")[:60].replace("\n", " ")
            print(f"  [{row_id}] {title}: {preview}...")
        conn.close()
        return

    # 加载 embedding 模型
    print("Loading embedding model...")
    embedding_tool = LocalEmbeddingTool()
    print("Model loaded.")

    # 批量生成 embedding 并更新
    updated = 0
    for row_id, title, content in rows:
        text = f"{title or ''} {content or ''}".strip()
        if not text:
            print(f"  [{row_id}] Empty content, skipping.")
            continue

        embedding = embedding_tool.encode(text)[0].tolist()

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE knowledge_base SET embedding = %s WHERE id = %s",
                (str(embedding), row_id),
            )
        conn.commit()
        updated += 1
        print(f"  [{row_id}] Updated: {title}")

    print(f"\nDone. Updated {updated}/{len(rows)} records.")
    embedding_tool.destroy()
    conn.close()


if __name__ == "__main__":
    main()
