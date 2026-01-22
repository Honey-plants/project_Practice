# menu_assistant/worker/worker_app/services/schema.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple

# ============================================================
# Constants / Types
# ============================================================
SchemaVersion = Literal["v1"]
RiskLevel = Literal["OK", "CAUTION", "NO"]


# ============================================================
# Low-level validators
# ============================================================
def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_poly(poly: Any) -> Tuple[bool, str]:
    """
    poly must be:
      - list of points (>=4)
      - each point: [x, y] where x,y are numeric
    """
    if poly is None:
        return False, "poly is None"
    if not isinstance(poly, list) or len(poly) < 4:
        return False, "poly must be a list with >=4 points"
    for i, p in enumerate(poly):
        if not isinstance(p, list) or len(p) != 2:
            return False, f"poly point {i} must be [x,y]"
        if not _is_num(p[0]) or not _is_num(p[1]):
            return False, f"poly point {i} coordinates must be numeric"
    return True, ""


def _require_nonempty_str(d: Dict[str, Any], key: str, path: str) -> Tuple[bool, str]:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        return False, f"{path}.{key} missing"
    return True, ""


# ============================================================
# User Profile (optional in final output, but useful for trace)
# ============================================================
@dataclass
class UserProfileV1:
    allergy_tags: List[str] = field(default_factory=list)
    avoid_foods: List[str] = field(default_factory=list)
    religion: Optional[str] = None


# ============================================================
# LLM OUTPUT / FINAL OUTPUT (Front-friendly)
# - You requested LLM output MUST include:
#   item_id, menu_name, poly, menu_description_ko, risk_description_ko
# - We keep the container shape stable:
#   { schema_version, run_id, items[...] }
# ============================================================
@dataclass
class LLMItemOutputV1:
    # REQUIRED (must always exist)
    item_id: str
    menu_name: str
    poly: Any
    menu_description_ko: str
    risk_description_ko: str

    # OPTIONAL but recommended
    risk_level: RiskLevel = "CAUTION"
    reason_bullets: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class LLMOutputV1:
    schema_version: SchemaVersion
    run_id: str
    items: List[LLMItemOutputV1]
    # Optional trace: you may store user_profile here for final output
    user_profile: Optional[UserProfileV1] = None


# ============================================================
# Validators (used by parsers.py)
# ============================================================
def validate_llm_output_v1(obj: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates the exact output schema expected from LLM.
    Strict on required fields; tolerant on optional keys.
    """
    if not isinstance(obj, dict):
        return False, "LLM output must be dict"

    # schema_version: allow missing -> treated as v1 in parsers
    sv = obj.get("schema_version")
    if sv is not None and sv != "v1":
        return False, "unsupported schema_version"

    # run_id
    if not isinstance(obj.get("run_id"), str) or not obj["run_id"].strip():
        return False, "run_id missing"

    # items
    if not isinstance(obj.get("items"), list):
        return False, "items must be list"

    for i, it in enumerate(obj["items"]):
        if not isinstance(it, dict):
            return False, f"items[{i}] must be dict"

        # REQUIRED 5 fields
        ok, msg = _require_nonempty_str(it, "item_id", f"items[{i}]")
        if not ok:
            return False, msg

        ok, msg = _require_nonempty_str(it, "menu_name", f"items[{i}]")
        if not ok:
            return False, msg

        ok_poly, msg_poly = validate_poly(it.get("poly"))
        if not ok_poly:
            return False, f"items[{i}].poly invalid: {msg_poly}"

        ok, msg = _require_nonempty_str(it, "menu_description_ko", f"items[{i}]")
        if not ok:
            return False, msg

        ok, msg = _require_nonempty_str(it, "risk_description_ko", f"items[{i}]")
        if not ok:
            return False, msg

        # OPTIONAL fields validation
        if "risk_level" in it:
            if it["risk_level"] not in ("OK", "CAUTION", "NO"):
                return False, f"items[{i}].risk_level must be OK|CAUTION|NO"

        if "reason_bullets" in it and it["reason_bullets"] is not None:
            if not isinstance(it["reason_bullets"], list):
                return False, f"items[{i}].reason_bullets must be list"

        if "confidence" in it and it["confidence"] is not None:
            try:
                c = float(it["confidence"])
            except Exception:
                return False, f"items[{i}].confidence must be numeric"
            if c < 0.0 or c > 1.0:
                return False, f"items[{i}].confidence must be 0.0~1.0"

    return True, ""


# ============================================================
# Cross-check helpers (strongly recommended in Step05)
# ============================================================
def validate_llm_output_against_input_ids(
    llm_obj: Dict[str, Any],
    expected_item_ids: List[str],
) -> Tuple[bool, str]:
    """
    Optional but recommended:
    Ensure output covers exactly the same item_ids as input.
    """
    if not isinstance(llm_obj, dict) or not isinstance(llm_obj.get("items"), list):
        return False, "llm_obj/items invalid"

    out_ids: List[str] = []
    for it in llm_obj["items"]:
        if isinstance(it, dict) and isinstance(it.get("item_id"), str):
            out_ids.append(it["item_id"])

    exp_set = set(expected_item_ids)
    out_set = set(out_ids)

    missing = sorted(exp_set - out_set)
    extra = sorted(out_set - exp_set)

    if missing:
        return False, f"LLM output missing item_id(s): {missing}"
    if extra:
        return False, f"LLM output has unexpected item_id(s): {extra}"

    return True, ""


# Convenience
def to_dict(obj: Any) -> Dict[str, Any]:
    return asdict(obj)
