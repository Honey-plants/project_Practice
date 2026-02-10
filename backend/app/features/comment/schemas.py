from typing import Optional
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentRead(BaseModel):
    comment_id: int
    community_id: int
    member_id: Optional[int] = None  # 탈퇴 시 NULL 가능
    nickname: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
