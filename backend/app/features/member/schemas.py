from typing import Optional, List
from pydantic import BaseModel

from backend.app.common.schemas.base import ORMBase

# request [요청]
# 등록
class MemberCreate(BaseModel):
    email: str
    password: str
    nickname: str
    gender: str
    country: str
    item_ids: Optional[List[int]] = None
    dislike_tags: Optional[List[str]] = None

# 수정
class MemberUpdate(BaseModel):
    nickname: Optional[str] = None
    item_ids: Optional[List[int]] = None
    dislike_tags: Optional[List[str]] = None

# response [응답]
class MemberRead(BaseModel):
    member_id: int
    email: str
    nickname: str
    gender: str
    country: str
    role: str
    item_ids: Optional[List[int]] = None
    dislike_tags: Optional[List[str]] = None

