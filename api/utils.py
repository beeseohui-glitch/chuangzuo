"""
API 共享工具函数
"""

import json
from typing import Optional


def row_to_dict(row, extra_datetime_keys: Optional[tuple[str, ...]] = None) -> dict:
    """
    将 asyncpg/psycopg2 Record 转为前端兼容的 dict

    Args:
        row: 数据库行记录
        extra_datetime_keys: 额外需要转 isoformat 的时间字段（默认处理 created_at, updated_at）
    """
    d = dict(row)
    # JSONB 字段解析
    if "tags" in d and isinstance(d["tags"], str):
        d["tags"] = json.loads(d["tags"])
    if "metadata" in d and isinstance(d["metadata"], str):
        d["metadata"] = json.loads(d["metadata"])
    # datetime 转字符串
    datetime_keys = ("created_at", "updated_at")
    if extra_datetime_keys:
        datetime_keys = datetime_keys + extra_datetime_keys
    for key in datetime_keys:
        if key in d and d[key] is not None and not isinstance(d[key], str):
            d[key] = d[key].isoformat()
    # SERIAL id 是 int，前端期望 string
    if "id" in d:
        d["id"] = str(d["id"])
    return d
