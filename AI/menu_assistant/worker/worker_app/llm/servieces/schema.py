# menu_assistant/worker/worker_app/services/schema.py
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Literal, Optional, Tuple, Union


# ---------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------
SchemaVersion = Literal["v1"]
MatchStatus = Literal["exact", "close"]
Decision = Literal["OK", "CAUTION", "NO"]


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_poly(poly: Any) -> Tuple[bool, str]:
    """
    Your poly is typically 4 points:
      [[x,y], [x,y], [x,y], [x,y]]
    but some pipelines may return more points.
    We accept:
      - list of points
      - each point is [x,y] numeric
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


# ---------------------------------------------------------------------
# Step05 Input (LLM payload) schema
# ---------------------------------------------------------------------
@dataclass
class UserProfileV1:
    allergy_tags: List[str] = field(default_factory=list)
    avoid_foods: List[str] = field(default_factory=list)
    religion: Optional[str] = None


@dataclass
class LLMExactItemInputV1:
    item_id: str
    status: Literal["exact"]
    poly: Any
    menu_id: Optional[str] = None
    menu: str = ""
    ingredients_ko: List[str] = field(default_factory=list)
    alg_tags: List[str] = field(default_factory=list)


@dataclass
class LLMCloseItemInputV1:
    item_id: str
    status: Literal["close"]
    poly: Any
    decided_menu: str = ""


LLMItemInputV1 = Union[LLMExactItemInputV1, LLMCloseItemInputV1]


@dataclass
class LLMPayloadV1:
    run_id: str
    user_profile: UserProfileV1
    items: List[LLMItemInputV1]
    schema_version: SchemaVersion = "v1"


# ---------------------------------------------------------------------
# Step05 Output (LLM result per item) schema
#   - Keep it stable and minimal.
#   - Do NOT let LLM control IDs.
# ---------------------------------------------------------------------
@dataclass
class LLMItemResultV1:
    item_id: str
    decision: Decision
    reason_bullets: List[str] = field(default_factory=list)
    menu_description_ko: str = ""
    confidence: float = 0.0
    # Optional: model may flag uncertainty or suggest normalized English ingredient hints later.
    notes: str = ""


@dataclass
class LLMResultV1:
    run_id: str
    items: List[LLMItemResultV1]
    schema_version: SchemaVersion = "v1"


# ---------------------------------------------------------------------
# Final Output (after merging match info + LLM + translation)
# ---------------------------------------------------------------------
@dataclass
class TranslationV1:
    final_menu_en: str = ""
    menu_description_en: str = ""


@dataclass
class FinalMatchInfoV1:
    item_id: str
    status: MatchStatus
    poly: Any
    # exact case fields
    menu_id: Optional[str] = None
    menu: Optional[str] = None
    ingredients_ko: List[str] = field(default_factory=list)
    alg_tags: List[str] = field(default_factory=list)
    # close case fields
    decided_menu: Optional[str] = None


@dataclass
class FinalItemV1:
    item_id: str
    match: FinalMatchInfoV1
    llm: LLMItemResultV1
    translation: TranslationV1 = field(default_factory=TranslationV1)


@dataclass
class FinalOutputV1:
    run_id: str
    user_profile: UserProfileV1
    items: List[FinalItemV1]
    schema_version: SchemaVersion = "v1"


# ---------------------------------------------------------------------
# Validators (lightweight, no external deps)
# ---------------------------------------------------------------------
def validate_llm_payload_v1(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "payload must be dict"
    if payload.get("schema_version", "v1") != "v1":
        return False, "unsupported schema_version"
    if not isinstance(payload.get("run_id"), str) or not payload["run_id"].strip():
        return False, "run_id missing"
    if not isinstance(payload.get("user_profile"), dict):
        return False, "user_profile must be dict"
    if not isinstance(payload.get("items"), list):
        return False, "items must be list"

    for i, it in enumerate(payload["items"]):
        if not isinstance(it, dict):
            return False, f"items[{i}] must be dict"
        if not isinstance(it.get("item_id"), str) or not it["item_id"].strip():
            return False, f"items[{i}].item_id missing"
        st = str(it.get("status", "")).lower()
        if st not in ("exact", "close"):
            return False, f"items[{i}].status must be exact|close"
        ok, msg = validate_poly(it.get("poly"))
        if not ok:
            return False, f"items[{i}].poly invalid: {msg}"

        if st == "exact":
            if not isinstance(it.get("menu"), str) or not it["menu"].strip():
                return False, f"items[{i}].menu missing for exact"
            if it.get("ingredients_ko") is not None and not isinstance(it.get("ingredients_ko"), list):
                return False, f"items[{i}].ingredients_ko must be list"
            if it.get("alg_tags") is not None and not isinstance(it.get("alg_tags"), list):
                return False, f"items[{i}].alg_tags must be list"
        else:
            if not isinstance(it.get("decided_menu"), str) or not it["decided_menu"].strip():
                return False, f"items[{i}].decided_menu missing for close"

    return True, ""


def validate_llm_result_v1(res: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(res, dict):
        return False, "llm result must be dict"
    if res.get("schema_version", "v1") != "v1":
        return False, "unsupported schema_version"
    if not isinstance(res.get("run_id"), str) or not res["run_id"].strip():
        return False, "run_id missing"
    if not isinstance(res.get("items"), list):
        return False, "items must be list"

    for i, it in enumerate(res["items"]):
        if not isinstance(it, dict):
            return False, f"items[{i}] must be dict"
        if not isinstance(it.get("item_id"), str) or not it["item_id"].strip():
            return False, f"items[{i}].item_id missing"
        dec = it.get("decision")
        if dec not in ("OK", "CAUTION", "NO"):
            return False, f"items[{i}].decision must be OK|CAUTION|NO"
        if it.get("reason_bullets") is not None and not isinstance(it.get("reason_bullets"), list):
            return False, f"items[{i}].reason_bullets must be list"
        conf = it.get("confidence", 0.0)
        if not _is_num(conf) or conf < 0.0 or conf > 1.0:
            return False, f"items[{i}].confidence must be 0.0~1.0"

    return True, ""


# Convenience: dataclass -> dict
def to_dict(obj: Any) -> Dict[str, Any]:
    return asdict(obj)
