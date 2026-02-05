# menu_assistant/worker/worker_app/translate/schema.py
from typing import Any, Dict, Tuple


REQUIRED_KEYS = {
    "menu_description_en",
    "risk_description_en",
    "comment_en",
}


def validate_translate_output(obj: Any) -> Tuple[bool, str]:
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

    if keys != REQUIRED_KEYS:
        return (
            False,
            f"Translation output keys mismatch. "
            f"expected={sorted(REQUIRED_KEYS)} got={sorted(keys)}"
        )

    for k in REQUIRED_KEYS:
        v = obj.get(k)
        if not isinstance(v, str):
            return False, f"Field '{k}' must be a string"

    return True, "OK"
