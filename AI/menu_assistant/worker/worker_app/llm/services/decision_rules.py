# C:\Users\201\Desktop\PGHfolder\haenet\AI\menu_assistant\worker\worker_app\llm\services\decision_rules.py
from __future__ import annotations

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


def _pick_text(rec: Dict[str, Any]) -> str:
    """
    Step4 결과 기준으로 메뉴 텍스트 후보를 안전하게 선택.
    - raw_menu / menu_norm 우선
    - (레거시 호환) menu_final/raw_menu_main 등도 fallback으로 유지
    """
    for k in ("raw_menu", "menu_norm", "menu_final", "raw_menu_main", "menu_name", "menu", "used_query", "query", "text"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _get_status(rec: Dict[str, Any]) -> str:
    """
    Step4: match_status = exact | unknown (우선)
    레거시: status / match.status 도 fallback으로 지원
    """
    raw = rec.get("match_status")
    if raw is None:
        raw = rec.get("status")
    if raw is None:
        m = rec.get("match")
        if isinstance(m, dict):
            raw = m.get("status")

    s = _lower(raw)

    if s == "exact" or "exact" in s:
        return "exact"
    if s == "unknown":
        return "unknown"

    # 레거시/확장 여지
    if s == "close" or "close" in s:
        return "close"
    if "ambiguous" in s:
        return "ambiguous"
    if "not_found" in s:
        return "not_found"

    # Step4 기준: 모르는 건 unknown 취급(LLM 판단 대상으로)
    return "unknown"


def _extract_confirmed(rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Step4 exact일 때 confirmed를 정규화해서 반환.
    confirmed가 없으면 None.
    """
    c = rec.get("confirmed")
    if not isinstance(c, dict):
        return None

    menu_id = _safe_str(c.get("menu_id") or c.get("id"))
    menu = _safe_str(c.get("menu"))
    ingredients_ko = _as_list(c.get("ingredients_ko"))
    alg_tags = _as_list(c.get("alg_tags"))

    # 최소 menu는 있어야 confirmed로 의미가 있음
    if not menu:
        return None

    return {
        "menu_id": menu_id,
        "menu": menu,
        "ingredients_ko": ingredients_ko,
        "alg_tags": alg_tags,
    }


# ------------------------------------------------------------
# Risk-match + comment helpers (MVP)
# ------------------------------------------------------------

def _compute_user_risk_match(
    *,
    user_profile: Optional[Dict[str, Any]],
    confirmed: Dict[str, Any],
) -> Dict[str, Any]:
    """
    exact 메뉴에 대해 user_profile과 confirmed(alg_tags/ingredients_ko/menu)를 비교해서
    프론트에서 표시할 user_risk_match를 만든다.

    user_profile minimal schema:
      {
        "allergy_tags": [...],
        "avoid_foods": [...],
        "religion": "islam_halal" | None
      }
    """
    allergy_hits: List[str] = []
    avoid_hits: List[str] = []
    religion_hits: List[str] = []

    if not isinstance(user_profile, dict):
        return {
            "allergy_tag_hits": [],
            "avoid_food_hits": [],
            "religion_hits": [],
            "has_any_risk": False,
        }

    user_allergy = set([str(x).strip() for x in _as_list(user_profile.get("allergy_tags")) if str(x).strip()])
    user_avoid = [str(x).strip() for x in _as_list(user_profile.get("avoid_foods")) if str(x).strip()]
    religion = _safe_str(user_profile.get("religion"))

    conf_alg = set([str(x).strip() for x in _as_list(confirmed.get("alg_tags")) if str(x).strip()])
    conf_ing = [str(x).strip() for x in _as_list(confirmed.get("ingredients_ko")) if str(x).strip()]
    conf_menu = _safe_str(confirmed.get("menu")) or ""

    # A) allergy tag exact intersection
    allergy_hits = sorted(list(user_allergy.intersection(conf_alg)))

    # B) avoid foods heuristic (보수적으로: ingredients_ko / menu 문자열 포함 여부)
    #    - ingredients_ko가 영문일 수도 있으니 일단 "부분문자열" 수준으로만 확인
    ing_blob = " ".join(conf_ing).lower()
    menu_blob = conf_menu.lower()

    for w in user_avoid:
        lw = w.lower()
        if lw and (lw in ing_blob or lw in menu_blob):
            avoid_hits.append(w)

    # C) religion heuristic (MVP: islam_halal만)
    if religion == "islam_halal":
        # 알코올/돼지고기/라드 등 키워드 탐지(메뉴명+ingredients 기반)
        blob = (conf_menu + " " + " ".join(conf_ing)).lower()
        alcohol_keys = ["술", "소주", "맥주", "와인", "럼", "브랜디", "청하", "막걸리", "alcohol", "wine", "beer", "soju"]
        pork_keys = ["돼지", "삼겹", "족발", "보쌈", "pork"]
        lard_keys = ["라드", "lard"]

        if any(k in blob for k in alcohol_keys):
            religion_hits.append("ALCOHOL_SUSPECT")
        if any(k in blob for k in pork_keys):
            religion_hits.append("PORK_SUSPECT")
        if any(k in blob for k in lard_keys):
            religion_hits.append("LARD_SUSPECT")

    has_any = bool(allergy_hits or avoid_hits or religion_hits)

    return {
        "allergy_tag_hits": allergy_hits,
        "avoid_food_hits": avoid_hits,
        "religion_hits": religion_hits,
        "has_any_risk": has_any,
    }




def _compute_risk_difficulty_exact(*, risk_match: Dict[str, Any]) -> int:
    """Exact-only risk_difficulty (0/1/2)

    Rule (user request):
      - 2: allergy_tag_hits OR religion_hits has at least one element
      - 1: only avoid_food_hits has at least one element
      - 0: no hits
    """
    if not isinstance(risk_match, dict):
        return 0
    allergy_hits = risk_match.get("allergy_tag_hits") or []
    religion_hits = risk_match.get("religion_hits") or []
    avoid_hits = risk_match.get("avoid_food_hits") or []

    if allergy_hits or religion_hits:
        return 2
    if avoid_hits:
        return 1
    return 0

def _build_comment_exact(
    *,
    confirmed: Dict[str, Any],
    risk_match: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]],
) -> List[str]:
    """
    직원에게 보여줄 Yes/No 질문(comment_ko) 생성 (exact용).
    - hit가 있으면 hit 기반으로 1~3개 질문
    - hit가 없으면 "알러지 유발 재료 포함 여부" 같은 보수적 질문 1개
    """
    out: List[str] = []

    allergy_hits = _as_list(risk_match.get("allergy_tag_hits"))
    avoid_hits = _as_list(risk_match.get("avoid_food_hits"))
    religion_hits = _as_list(risk_match.get("religion_hits"))

    # 1) allergy tag 기반 질문
    #    (태그->자연어 매핑은 추후 확장 가능. 지금은 태그 그대로 노출하되, 예시를 괄호로 붙이는 정도)
    for t in allergy_hits[:2]:
        out.append(f"이 메뉴에 알러지 유발 성분({t})이 포함되나요? (Yes/No)")

    # 2) avoid food 기반 질문
    for w in avoid_hits[:2]:
        out.append(f"이 메뉴에 '{w}'가 들어가나요? (Yes/No)")

    # 3) religion 기반 질문 (MVP: halal)
    if religion_hits:
        # 너무 길어지지 않게 1개로 묶어서 질문
        if "ALCOHOL_SUSPECT" in religion_hits:
            out.append("이 메뉴(또는 소스/육수)에 알코올이 들어가나요? (Yes/No)")
        if "PORK_SUSPECT" in religion_hits or "LARD_SUSPECT" in religion_hits:
            out.append("이 메뉴(또는 소스/육수)에 돼지고기/라드가 들어가나요? (Yes/No)")

    # 4) 아무것도 없으면 보수적 확인 질문 1개
    if not out:
        # user_profile이 있으면 그 중 대표 1~2개를 중심으로 묻기
        if isinstance(user_profile, dict):
            at = _as_list(user_profile.get("allergy_tags"))
            af = _as_list(user_profile.get("avoid_foods"))
            rel = _safe_str(user_profile.get("religion"))

            # 우선순위: allergy_tags -> avoid_foods -> religion
            if at:
                out.append(f"이 메뉴에 알러지 유발 성분({str(at[0])})이 포함되나요? (Yes/No)")
            elif af:
                out.append(f"이 메뉴에 '{str(af[0])}'가 들어가나요? (Yes/No)")
            elif rel == "islam_halal":
                out.append("이 메뉴(또는 소스/육수)에 돼지고기/라드/알코올이 들어가나요? (Yes/No)")
            else:
                out.append("이 메뉴에 알러지 유발 재료(견과류/유제품/계란/밀/해산물 등)가 포함되나요? (Yes/No)")
        else:
            out.append("이 메뉴에 알러지 유발 재료(견과류/유제품/계란/밀/해산물 등)가 포함되나요? (Yes/No)")

    # 중복 제거(순서 유지)
    seen = set()
    uniq: List[str] = []
    for s in out:
        if s not in seen:
            uniq.append(s)
            seen.add(s)
    return uniq


# ------------------------------------------------------------
# DecisionRules
# ------------------------------------------------------------

class DecisionRules:
    """
    Step05용 LLM 입력 아이템 생성 규칙 클래스 (Step4 결과 스키마 대응)

    - match_status == "exact"  : confirmed 기반으로 LLM에 제공 + (가능하면) user_risk_match/comment_ko 생성
    - match_status == "unknown": item_id/poly/menu_norm 기반으로 LLM에 제공 (LLM이 메뉴여부/추정/드랍 판단)
    """

    def __init__(
        self,
        *,
        require_poly: bool = True,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.require_poly = require_poly
        self.user_profile = user_profile

    def build_llm_items(
        self,
        rag_match: Any,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        records = self._extract_records(rag_match)

        items: List[Dict[str, Any]] = []
        dropped = 0
        exact_out = 0
        unknown_out = 0

        seq = 0
        for rec in records:
            if not isinstance(rec, dict):
                dropped += 1
                continue

            status = _get_status(rec)

            # poly check
            poly = rec.get("poly")
            if poly is None:
                m = rec.get("match")
                if isinstance(m, dict):
                    poly = m.get("poly")

            if self.require_poly and poly is None:
                dropped += 1
                continue

            # ✅ item_id: Step4에서 들어온 값 우선 사용
            item_id = _safe_str(rec.get("item_id"))
            if not item_id:
                seq += 1
                item_id = f"itm_{seq:04d}"

            if status == "exact":
                out = self._build_exact(item_id, rec, poly)
                if out:
                    items.append(out)
                    exact_out += 1
                else:
                    dropped += 1
                continue

            if status == "unknown":
                out = self._build_unknown(item_id, rec, poly)
                if out:
                    items.append(out)
                    unknown_out += 1
                else:
                    dropped += 1
                continue

            # 레거시는 일단 drop (Step4 기준에 맞추는 초안)
            dropped += 1

        meta = {
            "total_in": len(records),
            "total_out": len(items),
            "exact_out": exact_out,
            "unknown_out": unknown_out,
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
            if "match_status" in rag_match or "status" in rag_match:
                return [rag_match]
        return []

    def _build_exact(
        self,
        item_id: str,
        rec: Dict[str, Any],
        poly: Any,
    ) -> Optional[Dict[str, Any]]:

        confirmed = _extract_confirmed(rec)
        if not confirmed:
            return None

        raw_menu = _safe_str(rec.get("raw_menu")) or _pick_text(rec)
        menu_norm = _safe_str(rec.get("menu_norm")) or _safe_str(rec.get("menu_name")) or raw_menu

        # user_risk_match + comment (프로필 없으면 기본값)
        risk_match = _compute_user_risk_match(user_profile=self.user_profile, confirmed=confirmed)
        comment_ko = _build_comment_exact(confirmed=confirmed, risk_match=risk_match, user_profile=self.user_profile)
        risk_difficulty = _compute_risk_difficulty_exact(risk_match=risk_match)

        # ✅ Step4 스키마 기반 필드 (네가 요청한 핵심)
        out: Dict[str, Any] = {
            "item_id": item_id,
            "raw_menu": raw_menu,
            "menu_norm": menu_norm,
            "poly": poly,
            "match_status": "exact",
            "confirmed": confirmed,

            # 프론트 표시용(추후 step05 finalizer/translate로 carry)
            "user_risk_match": risk_match,
            "comment_ko": comment_ko,
            "risk_difficulty": risk_difficulty,
        }

        # ✅ 레거시/Step05 호환 키도 같이 유지(필요 시 prompt_builder가 그대로 사용 가능)
        out.update(
            {
                "status": "exact",
                "menu_name": confirmed.get("menu"),
                "risk_difficulty": risk_difficulty,
                "evidence": {
                    "menu_id": confirmed.get("menu_id"),
                "menu_description_ko": confirmed.get("menu_description_ko") or "",
                    "ingredients_ko": _as_list(confirmed.get("ingredients_ko")),
                    "alg_tags": _as_list(confirmed.get("alg_tags")),
                "menu_description_ko": confirmed.get("menu_description_ko") or "",
                "risk_difficulty": risk_difficulty,
                },
                # trace(기존 step05 normalize에서 사용)
                "menu": confirmed.get("menu"),
                "menu_id": confirmed.get("menu_id"),
                "ingredients_ko": _as_list(confirmed.get("ingredients_ko")),
                "alg_tags": _as_list(confirmed.get("alg_tags")),
                "menu_description_ko": confirmed.get("menu_description_ko") or "",
                "risk_difficulty": risk_difficulty,
            }
        )

        return out

    def _build_unknown(
        self,
        item_id: str,
        rec: Dict[str, Any],
        poly: Any,
    ) -> Optional[Dict[str, Any]]:

        raw_menu = _safe_str(rec.get("raw_menu")) or _pick_text(rec)
        menu_norm = _safe_str(rec.get("menu_norm")) or raw_menu
        if not menu_norm:
            return None

        out: Dict[str, Any] = {
            "item_id": item_id,
            "raw_menu": raw_menu,
            "menu_norm": menu_norm,
            "poly": poly,
            "match_status": "unknown",
            "confirmed": None,
        }

        # 레거시 키도 함께 두되, Step05에서 unknown 처리로직을 추가할 때 활용 가능
        out.update(
            {
                "status": "unknown",
                "menu_name": menu_norm,  # LLM이 이 텍스트를 보고 "메뉴인지/옵션인지/문구인지" 판별
                "evidence": {
                    "menu_id": None,
                    "ingredients_ko": [],
                    "alg_tags": [],
                },
            }
        )

        return out
