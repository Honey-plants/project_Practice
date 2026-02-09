from __future__ import annotations

import time
import uuid
from typing import Optional

# Lua: token이 일치할 때만 delete
_LUA_RELEASE = """
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
"""

def acquire_lock(redis_client, key: str, ttl_seconds: int) -> Optional[str]:
    """
    안전한 분산락 획득.
    - 성공 시 token(str) 반환
    - 실패 시 None
    """
    token = f"{uuid.uuid4().hex}:{int(time.time())}"
    ok = redis_client.set(key, token, nx=True, ex=int(ttl_seconds))
    return token if ok else None

def release_lock(redis_client, key: str, token: str) -> None:
    """
    안전한 분산락 해제.
    - token이 일치하는 경우에만 삭제
    """
    try:
        redis_client.eval(_LUA_RELEASE, 1, key, token)
    except Exception:
        # release 실패해도 TTL이 있으니 운영상 큰 문제는 없음
        pass
