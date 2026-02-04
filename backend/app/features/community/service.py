import json
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.app.models.community import Community
from backend.app.models.restrictions.item import Item
from backend.app.models.restrictions.dislike import Dislike
from backend.app.models.restrictions.member_restriction import MemberRestrictions
from backend.app.features.community.schemas import CommunityUpdate, CommunityCreate, CommunityRead
from backend.app.models.img_file import ImgFile

# review 로직
from backend.app.features.review import service
from backend.app.models.review import Review



# 등록
def create_community(db: Session, payload, member_id: int) -> Dict[str, Any]:
    """
    payload.review_ids = [4,2,1] 을 받아서
    리뷰 리스트를 한번에 조회한 뒤, community 저장 로직에 활용한다.
    """

    print("payload :: ", payload)


    review_ids = list(payload.review_ids or [])
    print("최종 review id :: ", review_ids)
    # 혹시 문자열/혼합으로 들어올 가능성 방어
    review_ids = [int(x) for x in review_ids if str(x).strip().isdigit()]

    # review_ids로 한 번에 조회 // temp 1(3), map(all)
    reviews = service.list_reviews_by_ids(
        db,
        review_ids,
        member_id=member_id,          # 로그인 정보 member_id
        include_inactive=True,        # True // False는 이미 사용 처리
    )

    print("reviews :: 결과 ", reviews)

    # 검증: 요청한 id 개수와 조회된 개수가 다르면
    # - 없는 review_id가 있거나
    # - 남의 리뷰가 섞인 것
    if len(reviews) != len(set(review_ids)):
        raise HTTPException(status_code=403, detail="invalid review_ids (not found or not owned)")

    # 여기서 community insert + (연결테이블 저장)이 들어가면 됨
    # 지금 질문은 "리뷰 정보를 리스트로 한번에 받는 것"이 핵심이라 여기까지만.

    return {
        "member_id": member_id,
        "review_ids": review_ids,
        "reviews": reviews,
    }

def get_community_detail(db: Session, community_id: int) -> Dict[str, Any]:
    r = db.get(Community, community_id)

    print("community r :: ", r)

    imgs = db.execute(
        select(ImgFile)
        .where(ImgFile.community_id == community_id)
        .where(ImgFile.owner_type == "community")
        .order_by(ImgFile.sort_order.asc())
    ).scalars().all()

    return {
        "community_id": r.community_id,
        "member_id": r.member_id,
        "community_content": r.community_content,
        "community_active": r.community_active,
        "recommend": r.recommend,
        "created_at": r.create_at.isoformat() if getattr(r, "create_at", None) else None,
        "updated_at": r.update_at.isoformat() if getattr(r, "update_at", None) else None,
        "image_urls": [img.storage_path for img in imgs],
    }