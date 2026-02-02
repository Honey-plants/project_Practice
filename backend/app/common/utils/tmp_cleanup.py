from __future__ import annotations

import shutil
import time
from pathlib import Path


def cleanup_old_dirs(base_dir: Path, ttl_seconds: int, marker_filename: str | None = None) -> int:
    """
    base_dir 하위의 디렉토리 중 TTL 지난 폴더 삭제
    - marker_filename이 있으면: 그 파일의 mtime 기준
    - 없으면: 폴더 mtime 기준
    """
    if not base_dir.exists():
        return 0

    now = time.time()
    deleted = 0

    for d in base_dir.iterdir():
        if not d.is_dir():
            continue

        # 기준 시간(mtime)
        try:
            if marker_filename:
                marker = d / marker_filename
                ts = marker.stat().st_mtime if marker.exists() else d.stat().st_mtime
            else:
                ts = d.stat().st_mtime
        except FileNotFoundError:
            continue

        if (now - ts) >= ttl_seconds:
            try:
                shutil.rmtree(d, ignore_errors=True)
                deleted += 1
            except Exception:
                # 로그가 필요하면 여기서 남기고 continue
                pass

    return deleted


def cleanup_receipt_tmp(local_tmp_root: Path, ttl_seconds: int) -> int:
    """
    uploads/tmp/receipt/* 폴더를 TTL 기준으로 삭제
    verify 단계에서 만들어둔 receipt_final.json mtime 기준으로 판단(있으면)
    """
    receipt_root = local_tmp_root / "receipt"
    return cleanup_old_dirs(receipt_root, ttl_seconds, marker_filename="receipt_final.json")
