import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.core.cache.redis import redis_client


class MenuJobStore:
    KEY_JOB = "menu:job:{jid}"
    TTL_SEC = 60 * 30

    @classmethod
    def put(cls, *, job_id: str, member_id: int, result: Dict[str, Any], ttl_sec: int | None = None) -> None:
        ttl = int(ttl_sec or cls.TTL_SEC)
        data = {
            "job_id": job_id,
            "member_id": member_id,
            "result": result,
            "created_at": int(time.time()),
        }
        key = cls.KEY_JOB.format(jid=job_id)
        redis_client.set(key, json.dumps(data, ensure_ascii=False))
        redis_client.expire(key, ttl)

    @classmethod
    def get(cls, *, job_id: str) -> Optional[Dict[str, Any]]:
        key = cls.KEY_JOB.format(jid=job_id)
        raw = redis_client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @classmethod
    def delete(cls, *, job_id: str) -> None:
        key = cls.KEY_JOB.format(jid=job_id)
        redis_client.delete(key)


def run_menu_ai(*, image_path: str, runs_root: Path, run_id: str) -> Dict[str, Any]:
    from AI.menu_assistant.worker.worker_app.pipeline.orchestrator import (
        PipelineOrchestrator,
        Step5Options,
    )

    runs_root = Path(runs_root).expanduser().resolve()
    orch = PipelineOrchestrator(runs_root)
    step5 = Step5Options(user_profile_json=None)

    run_dir = orch.run(
        image_path=Path(image_path).expanduser().resolve(),
        run_id=run_id,
        step5=step5,
        run_step4=True,
        run_step5=True,
        run_step6=True,
        do_check=False,
    )

    result_path = run_dir / "final" / "final_translated.json"
    if not result_path.exists():
        result_path = run_dir / "final" / "final.json"
    if not result_path.exists():
        raise FileNotFoundError(f"Menu result not found: {result_path}")

    return json.loads(result_path.read_text(encoding="utf-8"))
