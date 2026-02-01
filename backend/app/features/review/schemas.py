from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReceiptVerifyResponse(BaseModel):
    receipt_id: str
    extracted: Dict[str, Any]


class ReviewCreateResponse(BaseModel):
    review_id: int
    image_urls: List[str] = Field(default_factory=list)


class ReviewCreatePayload(BaseModel):
    receipt_id: str
    title: str
    content: str
    rating: int
    location: Optional[str] = None
    menu_name: Optional[str] = None


# from datetime import datetime
# from typing import Optional
# from pydantic import BaseModel, Field
#
# from app.models import ORMBase
#
# class ReviewCreate(BaseModel):
#     review_title: str
#     review_content: str
#     rating: Optional[int] = Field(default=None, ge=1, le=5)
#     location: Optional[str] = None
#     member_id: int
#
# class ReviewRead(ORMBase):
#     review_id: int
#     review_title: str
#     review_content: str
#     rating: Optional[int] = None
#     location: Optional[str] = None
#     create_review: datetime
#     member_id: int
#
# class ReviewUpdate(BaseModel):
#     review_title: Optional[str] = None
#     review_content: Optional[str] = None
#     rating: Optional[int] = Field(default=None, ge=1, le=5)
#     location: Optional[str] = None
#     member_id: Optional[int] = None