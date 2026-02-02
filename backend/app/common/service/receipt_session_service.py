import json
import time
from typing import Any, Dict, Optional

from backend.app.core.cache.redis import redis_client


class ReceiptSessionService:
    """영수증 검증 결과(extracted)를 Redis에 임시 보관"""

    KEY_SESSION = "receipt:session:{rid}"
    TTL_SEC = 60 * 30  # 30분

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
