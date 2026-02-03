from __future__ import annotations
import time


def acquire_lock(redis_client, key: str, ttl_seconds: int) -> bool:
    # SET key value NX EX ttl
    return bool(redis_client.set(key, str(time.time()), nx=True, ex=ttl_seconds))


def release_lock(redis_client, key: str) -> None:
    try:
        redis_client.delete(key)
    except Exception:
        pass
