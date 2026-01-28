# menu_assistant/worker/worker_app/services/decision_rules.py
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


def _first_present(d: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _get_status(rec: Dict[str, Any]) -> str:
    # sample uses match_status: "EXACT" | "CLOSE" | "NOT_FOUND_BELOW_THRESHOLD" ...
    return _lower(rec.get("match_status") or rec.get("status") or "")


@dataclass
class ExactLLMItem:
    item_id: str
    status: str  # "exact"
    poly: Any
    menu_id: Optional[str]
    menu: str
    ingredients_ko: List[str]
    alg_tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "status": self.status,
            "poly": self.poly,
            "menu_id": self.menu_id,
            "menu": self.menu,
            "ingredients_ko": self.ingredients_ko,
            "alg_tags": self.alg_tags,
        }


@dataclass
class CloseLLMItem:
    item_id: str
    status: str  # "close"
    poly: Any
    decided_menu: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "status": self.status,
            "poly": self.poly,
            "decided_menu": self.decided_menu,
        }


class DecisionRules:
    """
    Output: LLM에 전달할 최소 필드만 추출 (exact/close만 유지)

    - exact:
        poly 필수
        confirmed.{menu_id,menu,ingredients_ko,alg_tags} 우선
        없으면 rag_match.best_match.{id,menu,ingredients_ko,alg_tags} fallback
    - close:
        poly 필수
        rag_match.decided_menu 우선
        없으면 menu_final/raw_menu fallback
    - else:
        discard
    """

    def __init__(
        self,
        *,
        require_poly: bool = True,
        keep_empty_ingredients: bool = True,
        keep_empty_alg_tags: bool = True,
    ) -> None:
        self.require_poly = require_poly
        self.keep_empty_ingredients = keep_empty_ingredients
        self.keep_empty_alg_tags = keep_empty_alg_tags

    def build_llm_items(self, rag_match: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        records = self._extract_records(rag_match)

        items: List[Dict[str, Any]] = []
        dropped = 0
        exact_out = 0
        close_out = 0
        errors: List[str] = []

        seq = 0
        for idx, rec in enumerate(records):
            if not isinstance(rec, dict):
                dropped += 1
                continue

            status = _get_status(rec)
            if status not in {"exact", "close"}:
                dropped += 1
                continue

            seq += 1
            item_id = f"itm_{seq:04d}"

            try:
                if status == "exact":
                    out = self._build_exact_item(item_id=item_id, rec=rec)
                    if out is None:
                        dropped += 1
                    else:
                        exact_out += 1
                        items.append(out)

                elif status == "close":
                    out = self._build_close_item(item_id=item_id, rec=rec)
                    if out is None:
                        dropped += 1
                    else:
                        close_out += 1
                        items.append(out)

            except Exception as e:
                dropped += 1
                errors.append(f"{status} idx={idx} error={type(e).__name__}: {e}")

        meta = {
            "total_in": len(records),
            "total_out": len(items),
            "exact_out": exact_out,
            "close_out": close_out,
            "dropped": dropped,
            "errors": errors[:50],
        }
        return items, meta

    def _extract_records(self, rag_match: Any) -> List[Any]:
        if isinstance(rag_match, list):
            return rag_match
        if isinstance(rag_match, dict):
            if isinstance(rag_match.get("items"), list):
                return rag_match["items"]
            for k in ("results", "outputs"):
                if isinstance(rag_match.get(k), list):
                    return rag_match[k]
            if ("match_status" in rag_match) or ("status" in rag_match):
                return [rag_match]
        return []

    def _extract_poly(self, rec: Dict[str, Any]) -> Any:
        poly = rec.get("poly")
        if self.require_poly and poly is None:
            return None
        return poly

    def _build_exact_item(self, *, item_id: str, rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        poly = self._extract_poly(rec)
        if self.require_poly and poly is None:
            return None

        confirmed = rec.get("confirmed") if isinstance(rec.get("confirmed"), dict) else None

        menu_id = None
        menu = None
        ingredients_ko: List[str] = []
        alg_tags: List[str] = []

        if confirmed:
            menu_id = _safe_str(confirmed.get("menu_id") or confirmed.get("id"))
            menu = _safe_str(confirmed.get("menu"))
            ingredients_ko = [str(x) for x in _as_list(confirmed.get("ingredients_ko")) if _safe_str(x)]
            alg_tags = [str(x) for x in _as_list(confirmed.get("alg_tags")) if _safe_str(x)]

        if not menu or (not ingredients_ko and not alg_tags):
            rag = rec.get("rag_match") if isinstance(rec.get("rag_match"), dict) else None
            best = rag.get("best_match") if rag and isinstance(rag.get("best_match"), dict) else None
            if best:
                menu_id = menu_id or _safe_str(best.get("id"))
                menu = menu or _safe_str(best.get("menu"))
                if not ingredients_ko:
                    ingredients_ko = [str(x) for x in _as_list(best.get("ingredients_ko")) if _safe_str(x)]
                if not alg_tags:
                    alg_tags = [str(x) for x in _as_list(best.get("alg_tags")) if _safe_str(x)]

        if not menu:
            return None
        if (not self.keep_empty_ingredients) and (not ingredients_ko):
            return None
        if (not self.keep_empty_alg_tags) and (not alg_tags):
            return None

        return ExactLLMItem(
            item_id=item_id,
            status="exact",
            poly=poly,
            menu_id=menu_id,
            menu=menu,
            ingredients_ko=ingredients_ko,
            alg_tags=alg_tags,
        ).to_dict()

    def _build_close_item(self, *, item_id: str, rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        poly = self._extract_poly(rec)
        if self.require_poly and poly is None:
            return None

        rag = rec.get("rag_match") if isinstance(rec.get("rag_match"), dict) else None
        decided = _safe_str(rag.get("decided_menu")) if rag else None

        decided = decided or _safe_str(rec.get("decided_menu")) or _safe_str(rec.get("menu_final")) or _safe_str(rec.get("raw_menu"))
        if not decided:
            return None

        return CloseLLMItem(
            item_id=item_id,
            status="close",
            poly=poly,
            decided_menu=decided,
        ).to_dict()
