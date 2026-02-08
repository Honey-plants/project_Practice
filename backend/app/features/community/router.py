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
from backend.app.features.review.service import availavble_review


router = APIRouter(prefix="/community", tags=["community"])

@router.post("", response_model=CommunityListRead)
async def create_community(payload: CommunityCreate, db: Session = Depends(get_db), current=Depends(get_current_member)):

    # 1. 넘겨 받은 데이터 조회 및 조합
    total_data = service.create_step1(db, payload, member_id=current.member_id)
    print("router data :: ", total_data)


    try:
        # 2. AI 로직 시작 (예외 가능성 제일 큼)
        result = await service.create_step2(db, total_data)
        print("result :: ", result)

        # 3. AI 성공 후 TEMP1만 REVIEW available 처리
        if int(payload.template_id) == 1:
            ok = availavble_review(db, payload.review_ids)
            if not ok:
                raise HTTPException(status_code=500, detail="Failed to update review availability")

        # # 3. AI 성공 후 REVIEW available 처리
        # print("AI 처리 후 REVIEW AVAILABLE ", payload.review_ids)
        # ok = availavble_review(db, payload.review_ids)
        # if not ok:
        #     # 여기서 실패하면 절대 성공 리턴하면 안됨(데이터 정합성 깨짐)
        #     raise HTTPException(status_code=500, detail="Failed to update review availability")

        # step1/step2에서 DB write가 있었다면 여기서 한 번에 커밋
        # step2 commit 주석처리 완
        db.commit()

        return result

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Community create failed: {type(e).__name__}: {e}")



    # # 2. 넘겨 받은 데이터 AI 로직 시작
    # result = await service.create_step2(db, total_data)
    #
    # print("result :: ", result)
    #
    # # 3. AI 생성 후 완료되면 REVIEW available F or 0 수정 처리
    #
    # print("AI 처리 후 REVIEW AVAILABLE ", payload.review_ids)
    # availavble_review(db, payload.review_ids)
    #
    # return result
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

    return service.get_community_detail(db, community_id, current_member_id=current.member_id)

# 좋아요 로직
@router.post("/{community_id}/recommend")
def recommend_toggle(community_id: int, db: Session = Depends(get_db), current=Depends(get_current_member)):
    out = service.toggle_recommend(db, community_id=community_id, member_id=current.member_id)
    db.commit()
    return out