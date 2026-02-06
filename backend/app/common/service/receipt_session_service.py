import json
import time
from typing import Any, Dict, Optional

from backend.app.core.cache.redis import redis_client
from backend.app.common.utils.redis_lock import acquire_lock, release_lock


class ReceiptSessionService:
    """영수증 검증 결과(extracted)를 Redis에 임시 보관"""

    KEY_SESSION = "receipt:session:{rid}"
    KEY_LOCK = "receipt:lock:{rid}"

    TTL_SEC = 60 * 30  # 30분
    LOCK_TTL_SEC = 60  # 리뷰 생성 처리 중 락 TTL(보수적으로)

    @classmethod
    def put(cls, *, receipt_id: str, member_id: int, payload: Dict[str, Any], ttl_sec: int | None = None) -> None:
        ttl = int(ttl_sec or cls.TTL_SEC)
        data = {
            "receipt_id": receipt_id,
            "member_id": member_id,
            "payload": payload,
            "created_at": int(time.time()),
        }
        key = cls.KEY_SESSION.format(rid=receipt_id)
        redis_client.set(key, json.dumps(data, ensure_ascii=False))
        redis_client.expire(key, ttl)

    @classmethod
    def get(cls, *, receipt_id: str) -> Optional[Dict[str, Any]]:
        key = cls.KEY_SESSION.format(rid=receipt_id)
        raw = redis_client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @classmethod
    def delete(cls, *, receipt_id: str) -> None:
        key = cls.KEY_SESSION.format(rid=receipt_id)
        redis_client.delete(key)

    # ✅ 추가: receipt 단위 락(리뷰 생성 동시성 방지)
    @classmethod
    def acquire_create_lock(cls, *, receipt_id: str) -> Optional[str]:
        key = cls.KEY_LOCK.format(rid=receipt_id)
        return acquire_lock(redis_client, key, ttl_seconds=cls.LOCK_TTL_SEC)

    @classmethod
    def release_create_lock(cls, *, receipt_id: str, token: str) -> None:
        key = cls.KEY_LOCK.format(rid=receipt_id)
        release_lock(redis_client, key, token)
