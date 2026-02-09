from __future__ import annotations
from typing import Any, Dict, List

from AI.review.app.pipeline.step_3_normalize.normalize_lines import normalize_lines
from AI.review.app.pipeline.step_3_normalize.store_info import extract_phone
from AI.review.app.pipeline.step_3_normalize.menu_name import extract_menu_items

def normalize_receipt_data(
    ocr_items: List[Dict[str, Any]],
    *,
    y_threshold: int = 15,
) -> Dict[str, Any]:


    lines = normalize_lines(
        ocr_items,
        y_threshold=y_threshold,
    )

    return {
        "lines": lines,
        "phone": extract_phone(lines),
        "menu_ko": extract_menu_items(lines),
    }