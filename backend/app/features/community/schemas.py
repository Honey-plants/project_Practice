# from typing import Optional, List
# from pydantic import BaseModel, Field
#
# # ----------------------------------------
# # Create (등록)
# # - content는 필수
# # - review_ids: 리스트로 받는다(없으면 [])
# # ----------------------------------------
# class CommunityCreate(BaseModel):
#     community_content: str = Field(..., min_length=1)
#     review_ids: List[int] = Field(default_factory=list, description="연결할 리뷰 ID 목록(선택)")
#
#     # (선택) community_img_name 같은 걸 다시 쓸 거면 여기에 Optional[str] 추가
#     # community_img_name: Optional[str] = None
#
#
# # ----------------------------------------
# # Update (수정)
# # - 수정: active, recommend (요구사항대로)
# # - recommend는 증가/감소가 아니라 '값 변경'으로 가정
# # ----------------------------------------
# class CommunityUpdate(BaseModel):
#     recommend: Optional[int] = Field(default=None, ge=0)
#     community_active: Optional[bool, int, str] = None
#
#     @field_validator("community_active")
#     @classmethod
#     def validate_active(cls, v):
#         return _normalize_active(v)
#
#
# # ----------------------------------------
# # Read (조회 응답)
# # - ORM -> Pydantic 변환용 from_attributes=True
# # - review_ids는 실제 DB 설계에 따라 채워서 내려주면 됨(없으면 [])
# # ----------------------------------------
# class CommunityRead(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     community_id: int
#     community_content: str
#
#     create_at: datetime
#     update_at: datetime
#
#     recommend: int
#     community_active: bool
#
#     member_id: int
#
#     # 등록 시 입력받은 review_ids를 실제로 저장/조인해서 내려줄 거면 사용
#     review_ids: List[int] = Field(default_factory=list)
#
#
# # ----------------------------------------
# # List 응답(선택)
# # - 단순 list[CommunityRead]로 내려도 되지만,
# #   프론트 확장(페이징/총개수/필터) 고려하면 wrapper도 유용함
# # ----------------------------------------
# class CommunityListResponse(BaseModel):
#     items: List[CommunityRead] = Field(default_factory=list)
#     total: int = 0