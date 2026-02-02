from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------

def _safe_str(v: Any) -> Optional[str]:
    """
    임의의 값을 문자열로 안전하게 변환한다.
    - None → None
    - 공백만 있는 문자열 → None
    - 그 외 → strip() 적용된 문자열
    """
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _lower(v: Any) -> str:
    """
    문자열을 소문자로 변환하여 반환한다.
    - None → 빈 문자열
    - 그 외 → strip() + lower()
    """
    return str(v).strip().lower() if v is not None else ""


def _as_list(v: Any) -> List[Any]:
    """
    값을 항상 list 형태로 보정한다.
    - None → []
    - list → 그대로 반환
    - 단일 값 → [v]
    """
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _get_status(rec: Dict[str, Any]) -> str:
    """
    record(dict)에서 상태값을 추출한다.
    우선순위:
      1) match_status
      2) status
    결과는 항상 소문자로 반환된다.
    """
    return _lower(rec.get("match_status") or rec.get("status") or "")


# ------------------------------------------------------------
# DecisionRules
# ------------------------------------------------------------

class DecisionRules:
    """
    Step05용 LLM 입력 아이템 생성 규칙 클래스

    핵심 정책:
    - EXACT / CLOSE 상태만 통과
    - poly 좌표는 기본적으로 필수(require_poly=True)
    - menu_name을 exact/close 공통 키로 제공
      → LLM 프롬프트 안정성 확보의 핵심 포인트
    """

    def __init__(self, *, require_poly: bool = True) -> None:
        """
        :param require_poly:
            True  → poly가 없는 항목은 모두 제거
            False → poly가 없어도 통과 허용
        """
        self.require_poly = require_poly

    def build_llm_items(
        self,
        rag_match: Any
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        rag_match 결과를 받아 LLM 입력용 items와 메타 정보를 생성한다.

        반환값:
          - items: LLM에 전달할 메뉴 아이템 리스트
          - meta : 처리 통계 정보
        """

        # rag_match 구조를 표준 record list로 변환
        records = self._extract_records(rag_match)

        items: List[Dict[str, Any]] = []
        dropped = 0       # 필터링으로 제거된 항목 수
        exact_out = 0     # exact로 출력된 항목 수
        close_out = 0     # close로 출력된 항목 수

        seq = 0  # item_id 시퀀스
        for rec in records:
            # record는 반드시 dict여야 한다
            if not isinstance(rec, dict):
                dropped += 1
                continue

            # match 상태 추출 (exact / close / ambiguous / not_found 등)
            status = _get_status(rec)

            # exact, close 이외의 상태는 모두 제거
            if status not in {"exact", "close"}:
                dropped += 1
                continue

            # poly 좌표 확인
            poly = rec.get("poly")
            if self.require_poly and poly is None:
                dropped += 1
                continue

            # item_id는 itm_0001 형태로 순차 생성
            seq += 1
            item_id = f"itm_{seq:04d}"

            # ------------------------------------------------
            # EXACT 처리
            # ------------------------------------------------
            if status == "exact":
                out = self._build_exact(item_id, rec)
                if out:
                    items.append(out)
                    exact_out += 1
                else:
                    dropped += 1

            # ------------------------------------------------
            # CLOSE 처리
            # ------------------------------------------------
            elif status == "close":
                out = self._build_close(item_id, rec)
                if out:
                    items.append(out)
                    close_out += 1
                else:
                    dropped += 1

        # 처리 결과 요약 메타 정보
        meta = {
            "total_in": len(records),
            "total_out": len(items),
            "exact_out": exact_out,
            "close_out": close_out,
            "dropped": dropped,
        }
        return items, meta

    # --------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------

    def _extract_records(self, rag_match: Any) -> List[Any]:
        """
        rag_match 입력을 record list 형태로 정규화한다.

        허용 구조:
        - list → 그대로 사용
        - dict + items(list) → items 반환
        - dict + match_status → 단일 record로 감싸서 반환
        """
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
        """
        EXACT 상태 record를 LLM 입력용 item으로 변환한다.

        데이터 소스 우선순위:
          1) confirmed
          2) rag_match.best_match
        """

        poly = rec.get("poly")
        confirmed = rec.get("confirmed") or {}
        rag = rec.get("rag_match") or {}
        best = rag.get("best_match") or {}

        # menu 이름 결정 (confirmed 우선)
        menu = _safe_str(confirmed.get("menu")) or _safe_str(best.get("menu"))
        if not menu:
            return None

        return {
            "item_id": item_id,
            "status": "exact",
            "poly": poly,

            # ⭐ LLM에서 사용하는 핵심 메뉴 이름
            "menu_name": menu,

            # trace 용 원본 필드
            "menu": menu,
            "menu_id": confirmed.get("menu_id") or best.get("id"),

            # 재료 / 알러지 태그 (항상 list 형태로 보정)
            "ingredients_ko": _as_list(
                confirmed.get("ingredients_ko") or best.get("ingredients_ko")
            ),
            "alg_tags": _as_list(
                confirmed.get("alg_tags") or best.get("alg_tags")
            ),
        }

    def _build_close(
        self,
        item_id: str,
        rec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        CLOSE 상태 record를 LLM 입력용 item으로 변환한다.

        - decided_menu만 제공
        - 재료/알러지 정보는 아직 확정되지 않은 상태
        """

        poly = rec.get("poly")
        rag = rec.get("rag_match") or {}

        # decided_menu는 rag_match 우선, 없으면 record 자체에서 탐색
        decided = _safe_str(rag.get("used_query")) or _safe_str(rec.get("used_query"))
        if not decided:
            return None

        return {
            "item_id": item_id,
            "status": "close",
            "poly": poly,

            # ⭐ LLM에서 사용하는 핵심 메뉴 이름
            "menu_name": decided,

            # trace 용 필드
            "decided_menu": decided,
        }
