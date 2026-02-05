import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member
# from backend.app.common.utils.debug import log_exception
from backend.app.features.community.schemas import CommunityUpdate, CommunityCreate, CommunityRead, CommunityListRead
from backend.app.features.community import service
from backend.app.models.community import Community

router = APIRouter(prefix="/community", tags=["community"])

@router.post("", response_model=CommunityListRead)
async def create_community(payload: CommunityCreate, db: Session = Depends(get_db), current=Depends(get_current_member)):

    # 1. 넘겨 받은 데이터 조회 및 조합
    total_data = service.create_step1(db, payload, member_id=current.member_id)
    print("router data :: ", total_data)
    
    # 2. 넘겨 받은 데이터 AI 로직 시작
    result = await service.create_step2(db, total_data)

    print("result :: ", result)

    # 3. AI 생성 후 완료되면 REVIEW available F or 0 수정 처리

    return result
    # return CommunityListRead(community_id=result["community_id"], image_urls=result['image_urls'], member_id=result["member_id"])


@router.get("", response_model=list[CommunityListRead])
def community_list(db: Session = Depends(get_db)):
    print("community list 전체 조회중")
    return service.list_community(db, member_id=None, active_only=True)

# active 상관없이 내것 전부
@router.get("/me", response_model=list[CommunityListRead])
def community_my_list(db: Session = Depends(get_db), current=Depends(get_current_member)):
    print("community list 내것만 조회중")
    return service.list_community(db, member_id=current.member_id, active_only=None)

@router.get("/{community_id}", response_model=CommunityRead)
def get_community(community_id: int, db: Session = Depends(get_db), current=Depends(get_current_member)):

    print("community 상세 조회 :: ", current.member_id)

    return service.get_community_detail(db, community_id)
#
# @router.delete("/{community_id}")
# def delete_community(community_id: int, db: Session = Depends(get_db)):
#     c = db.query(model).filter(model.community_id == community_id).first()
#     if not c:
#         raise HTTPException(status_code=404, detail="Community not found")
#     db.delete(c)
#     db.commit()
#     return {"deleted": True, "community_id": community_id}
