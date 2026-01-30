
import os
import json
import uuid
import redis
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "cicdex:jobs")
QUEUE_NAME_MENU_ASSISTANT = os.getenv("QUEUE_NAME_MENU_ASSISTANT", "cicdex:jobs:menu_assistant")
QUEUE_NAME_JOURNAL = os.getenv("QUEUE_NAME_JOURNAL", "cicdex:jobs:journal")
QUEUE_NAME_REVIEW = os.getenv("QUEUE_NAME_REVIEW", "cicdex:jobs:review")


def utc_now_iso() -> str:
    """현재 UTC 시간을 ISO 포맷 문자열로 반환합니다."""
    return datetime.now(timezone.utc).isoformat()


def connect_redis() -> redis.Redis:
    """Redis 서버에 연결을 생성하고 반환합니다."""
    r = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    r.ping()
    return r


def _job_key(job_id: str) -> str:
    return f"cicdex:job:{job_id}"


def set_job(r: redis.Redis, job_id: str, status: str, **fields: Any) -> None:
    """Job 상태 및 메타데이터를 Redis Hash에 저장합니다."""
    data: Dict[str, str] = {
        "job_id": job_id,
        "status": status,
        "updated_at": utc_now_iso(),
    }
    for k, v in fields.items():
        if v is None:
            continue
        data[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    
    r.hset(_job_key(job_id), mapping=data)


def get_job(r: redis.Redis, job_id: str) -> Dict[str, str]:
    """Redis에서 Job 정보를 조회합니다."""
    return r.hgetall(_job_key(job_id))


def _queue_for_task(task: str) -> str:
    if task.startswith("menu_assistant_"):
        return QUEUE_NAME_MENU_ASSISTANT
    if task.startswith("journal_"):
        return QUEUE_NAME_JOURNAL
    if task.startswith("review_"):
        return QUEUE_NAME_REVIEW
    return QUEUE_NAME


def enqueue_task(r: redis.Redis, task: str, payload: Dict[str, Any]) -> str:
    """
    작업을 Redis 큐에 추가합니다.
    
    Args:
        r: Redis 클라이언트 인스턴스
        task: 작업 이름 (예: 'review_receipt_ocr', 'menu_assistant_pipeline', 'journal_generate')
        payload: 작업 실행에 필요한 데이터
        
    Returns:
        job_id: 생성된 Job ID
    """
    job_id = str(uuid.uuid4())
    queued_at = utc_now_iso()

    # Job 상태 초기화
    set_job(r, job_id, "PENDING", task=task, queued_at=queued_at)

    # 큐 메시지 생성
    msg = {
        "job_id": job_id,
        "task": task,
        "payload": payload,
        "queued_at": queued_at,
    }

    # Worker 큐에 푸시 (Worker는 BRPOPLPUSH 등으로 처리)
    queue_name = _queue_for_task(task)
    r.lpush(queue_name, json.dumps(msg, ensure_ascii=False))
    
    return job_id
