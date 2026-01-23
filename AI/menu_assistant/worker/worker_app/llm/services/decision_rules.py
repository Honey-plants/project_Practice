from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _safe_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _lower(v: Any) -> str:
    return str(v).strip().lower() if v is not None else ""


def _as_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _get_status(rec: Dict[str, Any]) -> str:
    return _lower(rec.get("match_status") or rec.get("status") or "")


class DecisionRules:
    """
    Step05 LLM input builder:
    - EXACT / CLOSE만 통과
    - poly 필수
    - menu_name을 exact/close 공통 키로 제공 (LLM/prompt 안정화 핵심)
    """

    def __init__(self, *, require_poly: bool = True) -> None:
        self.require_poly = require_poly

    def build_llm_items(self, rag_match: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        records = self._extract_records(rag_match)

        items: List[Dict[str, Any]] = []
        dropped = 0
        exact_out = 0
        close_out = 0

        seq = 0
        for rec in records:
            if not isinstance(rec, dict):
                dropped += 1
                continue

            status = _get_status(rec)
            if status not in {"exact", "close"}:
                dropped += 1
                continue

            poly = rec.get("poly")
            if self.require_poly and poly is None:
                dropped += 1
                continue

            seq += 1
            item_id = f"itm_{seq:04d}"

            if status == "exact":
                out = self._build_exact(item_id, rec)
                if out:
                    items.append(out)
                    exact_out += 1
                else:
                    dropped += 1

            elif status == "close":
                out = self._build_close(item_id, rec)
                if out:
                    items.append(out)
                    close_out += 1
                else:
                    dropped += 1

        meta = {
            "total_in": len(records),
            "total_out": len(items),
            "exact_out": exact_out,
            "close_out": close_out,
            "dropped": dropped,
        }
        return items, meta

    def _extract_records(self, rag_match: Any) -> List[Any]:
        if isinstance(rag_match, list):
            return rag_match
        if isinstance(rag_match, dict):
            if isinstance(rag_match.get("items"), list):
                return rag_match["items"]
            if "match_status" in rag_match:
                return [rag_match]
        return []

    def _build_exact(self, item_id: str, rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        poly = rec.get("poly")
        confirmed = rec.get("confirmed") or {}
        rag = rec.get("rag_match") or {}
        best = rag.get("best_match") or {}

        menu = _safe_str(confirmed.get("menu")) or _safe_str(best.get("menu"))
        if not menu:
            return None

        return {
            "item_id": item_id,
            "status": "exact",
            "poly": poly,
            "menu_name": menu,                # ⭐ 핵심
            "menu": menu,                     # trace
            "menu_id": confirmed.get("menu_id") or best.get("id"),
            "ingredients_ko": _as_list(confirmed.get("ingredients_ko") or best.get("ingredients_ko")),
            "alg_tags": _as_list(confirmed.get("alg_tags") or best.get("alg_tags")),
        }

    def _build_close(self, item_id: str, rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        poly = rec.get("poly")
        rag = rec.get("rag_match") or {}
        decided = _safe_str(rag.get("decided_menu")) or _safe_str(rec.get("decided_menu"))
        if not decided:
            return None

        return {
            "item_id": item_id,
            "status": "close",
            "poly": poly,
            "menu_name": decided,             # ⭐ 핵심
            "decided_menu": decided,          # trace
        }
