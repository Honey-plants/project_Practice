from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------

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
    # 원본 상태 (rag_match.json에서 match_status가 우선)
    raw = rec.get("match_status") or rec.get("status")
    if raw is None:
        m = rec.get("match")
        if isinstance(m, dict):
            raw = m.get("status")
    s = _lower(raw)

    # ✅ 표준화 매핑
    # exact / close 계열
    if s in {"exact"} or "exact" in s:
        return "exact"
    if s in {"close"} or "close" in s:
        return "close"

    # not_found 계열 (너 케이스: NOT_FOUND_BELOW_THRESHOLD)
    if "not_found" in s:
        return "not_found"

    # ambiguous 계열(혹시 future)
    if "ambiguous" in s:
        return "ambiguous"

    # fallback: 모르면 not_found로 (LLM 보강 대상으로 넘겨서 comment라도 만들게)
    return "not_found"



def _pick_ocr_text(rec: Dict[str, Any]) -> str:
    for k in ("menu_final", "raw_menu_main", "raw_menu", "menu_norm", "used_query", "query"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""



def _extract_candidates(rec: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
    rag = rec.get("rag_match") or {}
    cands = rag.get("candidates")
    if not isinstance(cands, list):
        return []

    out: List[Dict[str, Any]] = []
    for c in cands[: max(1, top_n)]:
        if not isinstance(c, dict):
            continue
        menu = _safe_str(c.get("menu"))
        cid = _safe_str(c.get("id") or c.get("menu_id"))
        if not menu:
            continue
        out.append(
            {
                "id": cid,
                "menu": menu,
                "ingredients_ko": _as_list(c.get("ingredients_ko")),
                "alg_tags": _as_list(c.get("alg_tags")),
                "score": c.get("score"),
            }
        )
    return out


def _pick_ocr_text(rec: Dict[str, Any]) -> str:
    """
    rag_match record에서 원문 텍스트(ocr/normalize 결과)를 최대한 안전하게 꺼낸다.
    (키가 프로젝트마다 다를 수 있으니 여러 후보를 순서대로 시도)
    """
    for k in ("text", "menu_text", "raw_text", "ocr_text", "query", "used_query", "menu"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _extract_candidates(rec: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    rag_match.candidates에서 LLM에 넘길 최소 후보정보만 뽑는다.
    - menu/id/ingredients_ko/alg_tags/score 정도만 전달
    """
    rag = rec.get("rag_match") or {}
    cands = rag.get("candidates")
    if not isinstance(cands, list):
        return []

    out: List[Dict[str, Any]] = []
    for c in cands[: max(1, top_n)]:
        if not isinstance(c, dict):
            continue
        menu = _safe_str(c.get("menu"))
        cid = _safe_str(c.get("id") or c.get("menu_id"))
        if not menu:
            continue
        out.append(
            {
                "id": cid,
                "menu": menu,
                "ingredients_ko": _as_list(c.get("ingredients_ko")),
                "alg_tags": _as_list(c.get("alg_tags")),
                "score": c.get("score"),
            }
        )
    return out


# ------------------------------------------------------------
# DecisionRules
# ------------------------------------------------------------

class DecisionRules:
    """
    Step05용 LLM 입력 아이템 생성 규칙 클래스

    변경 포인트:
    - 기존: EXACT/CLOSE만 통과
    - 변경: EXACT/CLOSE + AMBIGUOUS/NOT_FOUND도 통과시켜 LLM 보강을 허용
      (단, 보강 항목은 evidence.candidates 기반으로만 선택하도록 프롬프트에서 강제)
    """

    def __init__(self, *, require_poly: bool = True) -> None:
        self.require_poly = require_poly

    def build_llm_items(
        self,
        rag_match: Any
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        records = self._extract_records(rag_match)

        items: List[Dict[str, Any]] = []
        dropped = 0
        exact_out = 0
        close_out = 0
        other_out = 0

        seq = 0
        for rec in records:
            if not isinstance(rec, dict):
                dropped += 1
                continue

            status = _get_status(rec)

            # ✅ 통과 대상 확장
            if status not in {"exact", "close", "ambiguous", "not_found"}:
                dropped += 1
                continue

            poly = rec.get("poly")
            if poly is None:
                m = rec.get("match")
                if isinstance(m, dict):
                    poly = m.get("poly")

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

            else:
                out = self._build_ambiguous_or_not_found(item_id, rec, status=status)
                if out:
                    items.append(out)
                    other_out += 1
                else:
                    dropped += 1

        meta = {
            "total_in": len(records),
            "total_out": len(items),
            "exact_out": exact_out,
            "close_out": close_out,
            "other_out": other_out,
            "dropped": dropped,
        }
        return items, meta

    # --------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------

    def _extract_records(self, rag_match: Any) -> List[Any]:
        if isinstance(rag_match, list):
            return rag_match
        if isinstance(rag_match, dict):
            if isinstance(rag_match.get("items"), list):
                return rag_match["items"]
            if "match_status" in rag_match:
                return [rag_match]
        return []

    def _build_exact(
        self,
        item_id: str,
        rec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

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

            # ⭐ LLM에서 사용하는 핵심 메뉴 이름
            "menu_name": menu,

            # evidence를 한 군데로 모아 전달 (프롬프트 안정성)
            "evidence": {
    "menu_id": confirmed.get("menu_id") or best.get("id"),
    "ingredients_ko": _as_list(confirmed.get("ingredients_ko") or best.get("ingredients_ko")),
    "alg_tags": _as_list(confirmed.get("alg_tags") or best.get("alg_tags")),
    "ocr_text": _pick_ocr_text(rec),
    "candidates": _extract_candidates(rec, top_n=5),
},


            # trace 용 원본 필드(기존 호환)
            "menu": menu,
            "menu_id": confirmed.get("menu_id") or best.get("id"),
            "ingredients_ko": _as_list(confirmed.get("ingredients_ko") or best.get("ingredients_ko")),
            "alg_tags": _as_list(confirmed.get("alg_tags") or best.get("alg_tags")),
        }

    def _build_close(
        self,
        item_id: str,
        rec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        poly = rec.get("poly")
        rag = rec.get("rag_match") or {}

        decided = _safe_str(rag.get("used_query")) or _safe_str(rec.get("used_query"))
        if not decided:
            # 그래도 텍스트가 있으면 그걸 메뉴명 후보로 둔다(보강용)
            decided = _pick_ocr_text(rec) or None
        if not decided:
            return None

        return {
            "item_id": item_id,
            "status": "close",
            "poly": poly,
            "menu_name": decided,

            "evidence": {
    "menu_id": None,
    "ingredients_ko": [],
    "alg_tags": [],
    "ocr_text": _pick_ocr_text(rec),
    "candidates": _extract_candidates(rec, top_n=5),
},


            "decided_menu": decided,
        }

    def _build_ambiguous_or_not_found(
        self,
        item_id: str,
        rec: Dict[str, Any],
        *,
        status: str
    ) -> Optional[Dict[str, Any]]:

        poly = rec.get("poly")

        # 기본 메뉴명은 OCR/normalize 텍스트(원문)로 둔다.
        base_name = _pick_ocr_text(rec)
        if not base_name:
            # 최소한 뭔가는 있어야 LLM이 판단 가능
            return None

        return {
            "item_id": item_id,
            "status": status,   # ambiguous | not_found
            "poly": poly,
            "menu_name": base_name,

            "evidence": {
                "menu_id": None,
                "ingredients_ko": [],
                "alg_tags": [],
                "ocr_text": base_name,
                "candidates": _extract_candidates(rec, top_n=5),
            },
        }
