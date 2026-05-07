"""
TTL 缓存工具 - 泛型内存缓存，支持过期自动清理
"""

import time
from typing import Optional, Any


class TTLCache:
    """通用 TTL 缓存"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，过期自动删除"""
        if key in self._cache:
            value, ts = self._cache[key]
            if time.time() - ts < self._ttl:
                return value
            del self._cache[key]
        return None

    def put(self, key: str, value: Any):
        """写入缓存"""
        self._cache[key] = (value, time.time())

    def delete(self, key: str):
        """删除指定 key"""
        self._cache.pop(key, None)

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
