from typing import Optional, List
from pydantic import BaseModel, Field


class CommunityCreate(BaseModel):
    review_ids: List[int] = Field(default_factory=list)
    template_id: int

class CommunityUpdate(BaseModel):
    recommend: Optional[int] = Field(default=None)
    community_active: Optional[bool] = Field(default=None)

class CommunityRead(BaseModel):
    community_id: int
    community_content: str
    recommend: int
    community_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)

