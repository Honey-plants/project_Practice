from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RestrictionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    item_label_ko: str
    item_label_en: str
    category_id: int
    item_active: bool


class RestrictionCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    category_label_ko: str
    category_label_en: str
    category_active: bool
    items: List[RestrictionItemRead] = []


class RestrictionsResponse(BaseModel):
    """ETag는 헤더로도 내려가지만, 프론트에서 편하게 쓰려고 바디에도 같이 둠(선택)."""
    etag: str
    data: List[RestrictionCategoryRead]