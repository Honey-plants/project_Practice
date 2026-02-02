from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


def _norm_str(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def _normalize_alg_tags(tags: Any) -> List[str]:
    out: List[str] = []
    if isinstance(tags, list):
        for t in tags:
            s = _norm_str(t)
            if s.startswith("ALG_"):
                out.append(s)
    # dedup keep order
    seen = set()
    dedup = []
    for s in out:
        if s in seen:
            continue
        seen.add(s)
        dedup.append(s)
    return dedup


def _normalize_avoid_foods(vals: Any) -> List[str]:
    out: List[str] = []
    if isinstance(vals, list):
        for v in vals:
            s = _norm_str(v)
            if s:
                out.append(s)
    # dedup keep order
    seen = set()
    dedup = []
    for s in out:
        if s in seen:
            continue
        seen.add(s)
        dedup.append(s)
    return dedup


@dataclass
class RiskResult:
    risk: str  # SAFE / CAUTION / DANGER
    reason: str
    matched: List[str]


class RiskScorer:
    """
    Minimal, deterministic scorer.

    Input:
      user_profile (minimal):
        {
          "allergy_tags": ["ALG_MILK", ...],
          "avoid_foods": ["돼지고기", "알코올", ...],
          "religion": "islam_halal" | None
        }

      evidence:
        {
          "ingredients_ko": [...],  # may be English tokens in your dataset; we use substring match fallback
          "alg_tags": ["ALG_MILK", ...]
        }

    Policy:
      1) Allergy tag intersection => DANGER
      2) avoid_foods match against ingredients/menu_name => CAUTION (default)
         - If you later split avoid_foods into hard/soft, you can upgrade religion/vegan to DANGER.
    """

    def score_item(
        self,
        *,
        user_profile: Dict[str, Any],
        menu_name: str,
        evidence: Dict[str, Any],
    ) -> RiskResult:
        menu_name = _norm_str(menu_name)

        user_allergy = set(_normalize_alg_tags(user_profile.get("allergy_tags")))
        menu_alg = set(_normalize_alg_tags(evidence.get("alg_tags")))

        # 1) Allergy => DANGER
        inter = sorted(user_allergy.intersection(menu_alg))
        if inter:
            return RiskResult(risk="DANGER", reason="ALLERGY_TAG_MATCH", matched=inter)

        # 2) Avoid foods => CAUTION (string match)
        avoid = _normalize_avoid_foods(user_profile.get("avoid_foods"))
        ing = evidence.get("ingredients_ko") or []
        ing_strs = [_norm_str(x) for x in ing if _norm_str(x)]

        matched: List[str] = []
        for a in avoid:
            # direct ingredient match
            if a in ing_strs:
                matched.append(a)
                continue
            # substring fallback (handles English ingredient tokens vs Korean avoid terms weakly)
            if any(a in s for s in ing_strs):
                matched.append(a)
                continue
            # menu name fallback
            if a and a in menu_name:
                matched.append(a)

        if matched:
            # NOTE: currently CAUTION. If you add avoid_foods_hard later, upgrade those to DANGER.
            return RiskResult(risk="CAUTION", reason="AVOID_FOOD_MATCH", matched=matched)

        return RiskResult(risk="SAFE", reason="NO_MATCH", matched=[])
