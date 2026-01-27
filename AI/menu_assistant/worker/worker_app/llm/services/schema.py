# menu_assistant/worker/worker_app/services/schema.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple

# ============================================================
# Constants / Types
# ============================================================
# - SchemaVersion: LLM/서비스 출력 스키마 버전 관리용
#   * v1만 허용(현 시점)
# - RiskLevel: 최종 위험도 레벨 (프론트/UI에서 그대로 사용하기 쉬운 문자열)
SchemaVersion = Literal["v1"]
RiskLevel = Literal["OK", "CAUTION", "NO"]

# ============================================================
# Allowed ALG tags (UI/정렬 기준 고정)
# ============================================================
ALLOWED_ALG_TAGS = {
    "ALG_CELERY",
    "ALG_CEREALS_GLUTEN",
    "ALG_CRUSTACEANS",
    "ALG_EGGS",
    "ALG_FISH",
    "ALG_MILK",
    "ALG_MOLLUSCS",
    "ALG_MUSTARD",
    "ALG_SESAME",
    "ALG_SOY",
    "ALG_TREE_NUTS",
}

# ============================================================
# Low-level validators
# ============================================================
def _is_num(x: Any) -> bool:
    """
    숫자 판별 헬퍼.
    - int/float는 True
    - bool은 int의 서브클래스이므로 제외(False) 처리
      (True/False가 좌표나 score로 들어오는 것을 방지)
    """
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_poly(poly: Any) -> Tuple[bool, str]:
    """
    poly 유효성 검증.
    목적:
      - 메뉴 항목의 bounding polygon(텍스트 영역)을 프론트에서 오버레이/하이라이트할 때
        좌표 구조가 반드시 안정적으로 들어오도록 강제한다.

    poly 규칙:
      - list of points (>=4)
      - 각 point는 [x, y]
      - x,y는 numeric(int/float)이어야 함

    반환:
      (True, "")  : 유효
      (False, msg): 무효 + 원인 메시지
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
    """
    필수 문자열 필드 검증 헬퍼.
    - d[key]가 str이고 strip() 후 비어있지 않아야 통과
    - 실패 시 'path.key missing' 형태의 에러 메시지를 반환

    예:
      _require_nonempty_str(item, "menu_name", "items[0]")
      → menu_name이 없으면 "items[0].menu_name missing"
    """
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        return False, f"{path}.{key} missing"
    return True, ""


# ============================================================
# User Profile (optional in final output, but useful for trace)
# ============================================================
@dataclass
class UserProfileV1:
    """
    사용자 프로필(선택):
    - LLM 프롬프트에 포함하거나, 최종 결과에 trace/debug 목적으로 포함 가능
    - 최종 출력에서 반드시 필요하지는 않지만, '왜 위험도가 그렇게 나왔는지' 근거 추적에 유리

    필드:
      allergy_tags: 사용자의 알러지 태그(예: ALG_MILK, ALG_PEANUTS ...)
      avoid_foods : 비선호/회피 음식(텍스트 리스트)
      religion    : 종교적 제한(예: halal/vegan 등과 결합될 수도 있으나 현재는 문자열)
    """
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
    """
    LLM이 "메뉴 1개"에 대해 반환해야 하는 최소 단위 출력 스키마(v1)

    REQUIRED (반드시 존재해야 하는 5개):
      - item_id              : 입력과 1:1 매핑하기 위한 키(DecisionRules의 itm_0001 형태)
      - menu_name            : 최종 메뉴명(프롬프트/후처리 공통 키)
      - poly                 : 해당 메뉴 텍스트 영역(오버레이/하이라이트 목적)
      - menu_description_ko  : 메뉴 설명(한국어) - 외국인용 번역/추가설명 만들 때 기반 정보
      - risk_description_ko  : 위험도 설명(한국어) - 사용자의 알러지/종교/회피를 반영한 요약 근거

    OPTIONAL (있으면 좋은 필드):
      - risk_level     : OK / CAUTION / NO (기본 CAUTION)
      - reason_bullets : 근거를 bullet로 분리(프론트 UI에 그대로 활용 가능)
      - confidence     : 0~1 범위의 신뢰도(모델 응답 품질/추정치 표기)

    EXTENDED OPTIONAL (프롬프트 확장용):
      - matched_constraints : 사용자 조건과 충돌한다고 판단된 항목 요약
          {
            "allergy_tags": ["ALG_MILK"] or null,
            "religion": "..." or null,
            "avoid_foods": ["고수"] or null
          }
    """
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
    # NOTE: dataclass level typing is optional; validator handles runtime checks
    matched_constraints: Optional[Dict[str, Any]] = None


@dataclass
class LLMOutputV1:
    """
    LLM의 최종 출력 컨테이너 스키마(v1)

    필드:
      schema_version : "v1" (또는 생략 가능 - validators에서 허용, parsers에서 v1로 취급)
      run_id         : 파이프라인 실행 단위 식별자
      items          : LLMItemOutputV1 리스트 (메뉴 단위 출력)
      user_profile   : 선택(trace/debug) - 사용자 조건을 최종 결과에 남기고 싶을 때 사용
    """
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
    LLM이 반환한 dict가 "정확히" v1 스키마 요건을 만족하는지 검증한다.

    설계 의도:
      - REQUIRED 필드는 엄격히 검사(누락/빈문자열/형식 오류면 실패)
      - OPTIONAL 필드는 존재할 경우에만 타입/범위 검사(관대한 정책)
      - schema_version은 누락 가능(파서에서 v1로 처리한다고 주석에 명시)

    반환:
      (True, "")  : 유효
      (False, msg): 무효 + 원인 메시지
    """
    if not isinstance(obj, dict):
        return False, "LLM output must be dict"

    # schema_version: allow missing -> treated as v1 in parsers
    sv = obj.get("schema_version")
    if sv is not None and sv != "v1":
        return False, "unsupported schema_version"

    # run_id (반드시 존재해야 하며 비어있으면 안 됨)
    if not isinstance(obj.get("run_id"), str) or not obj["run_id"].strip():
        return False, "run_id missing"

    # items는 list여야 함
    if not isinstance(obj.get("items"), list):
        return False, "items must be list"

    # items 내부 각 항목을 순회하며 필수/옵션 필드 검증
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

        # poly는 별도 정밀 검증(좌표 구조/타입)
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
        # risk_level: 존재하면 허용 값(OK|CAUTION|NO)인지 확인
        if "risk_level" in it:
            if it["risk_level"] not in ("OK", "CAUTION", "NO"):
                return False, f"items[{i}].risk_level must be OK|CAUTION|NO"

        # reason_bullets: 존재하면 list인지 확인 (None은 허용)
        if "reason_bullets" in it and it["reason_bullets"] is not None:
            if not isinstance(it["reason_bullets"], list):
                return False, f"items[{i}].reason_bullets must be list"

        # confidence: 존재하면 float 변환 가능 + 0~1 범위인지 확인 (None 허용)
        if "confidence" in it and it["confidence"] is not None:
            try:
                c = float(it["confidence"])
            except Exception:
                return False, f"items[{i}].confidence must be numeric"
            if c < 0.0 or c > 1.0:
                return False, f"items[{i}].confidence must be 0.0~1.0"

        # OPTIONAL: matched_constraints
        # - if present, must be object or null
        # - fields inside must be:
        #   allergy_tags: list[str] subset of ALLOWED_ALG_TAGS OR null
        #   religion: str OR null
        #   avoid_foods: list[str] OR null
        if "matched_constraints" in it:
            mc = it.get("matched_constraints")
            if mc is not None:
                if not isinstance(mc, dict):
                    return False, f"items[{i}].matched_constraints must be object or null"

                # allergy_tags
                if "allergy_tags" in mc:
                    v = mc.get("allergy_tags")
                    if v is not None:
                        if not isinstance(v, list):
                            return False, f"items[{i}].matched_constraints.allergy_tags must be list or null"
                        for t in v:
                            if not isinstance(t, str) or not t.startswith("ALG_"):
                                return False, f"items[{i}].matched_constraints.allergy_tags invalid value: {t}"
                            if t not in ALLOWED_ALG_TAGS:
                                return False, f"items[{i}].matched_constraints.allergy_tags not allowed: {t}"

                # religion
                if "religion" in mc:
                    v = mc.get("religion")
                    if v is not None and not isinstance(v, str):
                        return False, f"items[{i}].matched_constraints.religion must be string or null"

                # avoid_foods
                if "avoid_foods" in mc:
                    v = mc.get("avoid_foods")
                    if v is not None:
                        if not isinstance(v, list):
                            return False, f"items[{i}].matched_constraints.avoid_foods must be list or null"
                        for x in v:
                            if not isinstance(x, str):
                                return False, f"items[{i}].matched_constraints.avoid_foods must be list[str]"

    return True, ""


# ============================================================
# Cross-check helpers (strongly recommended in Step05)
# ============================================================
def validate_llm_output_against_input_ids(
    llm_obj: Dict[str, Any],
    expected_item_ids: List[str],
) -> Tuple[bool, str]:
    """
    (권장) 입력 item_id와 LLM 출력 item_id의 정합성 검사.

    목적:
      - Step05에서 DecisionRules로 만든 items의 item_id 목록과
        LLM이 실제로 반환한 items의 item_id 목록이 "동일"해야
        후속 단계(오버레이/저장/사용자 노출)가 안전해진다.

    정책:
      - 누락(missing) 있으면 실패
      - 추가(extra) 있으면 실패
      - 순서(order)는 보지 않고, set 기반으로 "구성 동일"만 검사

    반환:
      (True, "")  : 정합
      (False, msg): 불일치 + 원인 메시지
    """
    if not isinstance(llm_obj, dict) or not isinstance(llm_obj.get("items"), list):
        return False, "llm_obj/items invalid"

    # 출력에서 item_id만 수집 (dict이며 item_id가 str인 경우만)
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
    """
    dataclass 인스턴스를 dict로 변환하는 편의 함수.
    - 내부적으로 dataclasses.asdict 사용
    - LLMOutputV1 / LLMItemOutputV1 / UserProfileV1 등 직렬화에 활용
    """
    return asdict(obj)
