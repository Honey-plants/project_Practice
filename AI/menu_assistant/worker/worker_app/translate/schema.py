# menu_assistant/worker/worker_app/translate/schema.py
from typing import Any, Dict, Tuple

REQUIRED_KEYS_BASE = {
    "menu_description_en",
    "risk_description_en",
    "comment_en",
}

REQUIRED_KEYS_WITH_NAME = {
    *REQUIRED_KEYS_BASE,
    "menu_name_en",
}


def validate_translate_output(obj: Any, *, require_menu_name_en: bool = False) -> Tuple[bool, str]:
    """
    Validate Step6 translation output.

    Rules:
    - obj must be a dict
    - MUST contain exactly the required keys
    - All values must be strings (empty string allowed)
    - No extra keys allowed
    """
    if not isinstance(obj, dict):
        return False, "Translation output must be a JSON object"

    keys = set(obj.keys())
    required = REQUIRED_KEYS_WITH_NAME if require_menu_name_en else REQUIRED_KEYS_BASE

    if keys != required:
        return (
            False,
            f"Translation output keys mismatch. "
            f"expected={sorted(required)} got={sorted(keys)}"
        )

    for k in required:
        v = obj.get(k)
        if not isinstance(v, str):
            return False, f"Field '{k}' must be a string"

    return True, "OK"
