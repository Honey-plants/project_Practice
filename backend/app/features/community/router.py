import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member
# from backend.app.common.utils.debug import log_exception
from backend.app.features.community.schemas import CommunityUpdate, CommunityCreate, CommunityRead
from backend.app.features.community import service
from backend.app.models.community import Community

router = APIRouter(prefix="/community", tags=["community"])

@router.post("", response_model=CommunityRead)
def create_community(payload: CommunityCreate, db: Session = Depends(get_db), current=Depends(get_current_member)):

    # 회원 정보
    # member_data =

    # review
    review_data = service.create_community(db, payload, member_id=current.member_id)
    print("router data :: ", review_data)



    # member service member / category, item / dislike
    # get_member

    # review 조회
    # list_reviews active, member_id 조회 후 active false or 0 번경 작업 추가



    # print("member_gender :: ", current.member_gender)
    # print("member_country :: ", current.member_country)
    # print("member_nickname :: ", current.member_nickname)

    # print("community 등록 : ", payload)
    # review_id / template



    # m = db.query(model).filter(model.member_id == payload.member_id).first()
    # if not m:
    #     raise HTTPException(status_code=400, detail="Invalid member_id")
    #
    # c = model(**payload.model_dump())
    # db.add(c)
    # db.commit()
    # db.refresh(c)
    return "등록 진행중"

# @router.get("", response_model=list[CommunityRead])
# def list_communities(db: Session = Depends(get_db), current=Depends(get_current_member)):
#     q = db.query(model.Community)
#     if member_id is not None:
#         q = q.filter(model.member_id == member_id)
#     return q.order_by(model.community_id.desc()).all()

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
