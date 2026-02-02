import time
from pathlib import Path
from backend.app.core import config

def cleanup_local_tmp(ttl_seconds: int = None) -> int:
    """
    uploads/tmp 아래에서 오래된 폴더를 삭제한다.
    - 로컬에서만 의미 있음
    """
    if config.STORAGE_BACKEND != "local":
        return 0

    ttl = ttl_seconds or config.TMP_TTL_SECONDS
    now = time.time()
    root = config.LOCAL_TMP_ROOT
    if not root.exists():
        return 0

    deleted = 0
    for p in root.rglob("*"):
        if not p.is_dir():
            continue
        try:
            mtime = p.stat().st_mtime
            if now - mtime > ttl:
                # 폴더 통째 삭제
                for _ in [0]:
                    import shutil
                    shutil.rmtree(p, ignore_errors=True)
                deleted += 1
        except Exception:
            pass
    return deleted
