from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from typing import Any, Dict, Optional, List

from starlette.concurrency import run_in_threadpool

from backend.app.models.community import Community
from backend.app.models.img_file import ImgFile

# review 로직
from backend.app.features.review.service import list_reviews_by_ids

# member 로직
from backend.app.features.member.service import get_member
from backend.app.models.member import Member
# category, item 조회
from backend.app.common.service.ai_member_info import build_user_profile_payload

# ai
from AI.journal_assistant.pipeline.orchestrator import run_orchestrator
from backend.app.common.service.file_upload_service import save_permanent_bytes, delete_prefix, build_perm_prefix

# 공통 저장(규칙은 공통에서만)
from backend.app.common.service.file_upload_service import save_permanent_bytes


# ---------------------------------------------------------------------
# 등록 Step1
# ---------------------------------------------------------------------
def create_step1(db: Session, payload, member_id: int) -> Dict[str, Any]:
    # 1) review ids 정리
    review_ids = list(payload.review_ids or [])
    review_ids = [int(x) for x in review_ids if str(x).strip().isdigit()]

    reviews = list_reviews_by_ids(
        db,
        review_ids,
        member_id=member_id,
        include_inactive=True,
    )

    if len(reviews) != len(set(review_ids)):
        raise HTTPException(status_code=403, detail="invalid review_ids (not found or not owned)")

    member_data = get_member(db, member_id)
    category_items = build_user_profile_payload(db, member_id)

    return {
        "member_id": member_id,
        "template_id": payload.template_id,
        "reviews": reviews,
        "member": member_data,
        "allergy_tags": category_items,
    }


# ---------------------------------------------------------------------
# 등록 Step2
# ---------------------------------------------------------------------

async def create_step2(db: Session, total_data: Dict[str, Any]) -> Dict[str, Any]:
    ai_payload = {
        "template": {
            "template_id": total_data.get("template_id"),
            "template_type": total_data.get("template_id"),
        },
        "member_id": total_data.get("member_id"),
        "member": total_data.get("member"),
        "allergy_tags": total_data.get("allergy_tags"),
        "reviews": total_data.get("reviews"),
    }

    # 1) AI 호출 (이벤트루프 안막도록 threadpool)
    try:
        image_bytes: bytes = await run_in_threadpool(run_orchestrator, ai_payload)
        if not image_bytes:
            raise RuntimeError("AI returned empty bytes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {type(e).__name__}: {e}")

    # 2) community 생성
    try:
        community = Community(
            member_id=int(total_data["member_id"]),
            community_active=True,
            recommend=0,
        )
        db.add(community)
        db.flush()
        community_id = community.community_id
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Community insert failed: {type(e).__name__}: {e}")

    stored = None
    perm_prefix = build_perm_prefix(owner_type="community", owner_id=community_id)

    try:
        # 3) 파일 저장
        stored = await save_permanent_bytes(
            owner_type="community",
            owner_id=community_id,
            member_id=int(total_data["member_id"]),
            data=image_bytes,
            origin_name="community.png",
            mime_type="image/png",
            sort_order=0,
        )

        # 4) ImgFile 저장
        img = ImgFile(
            origin_name=stored.org_file_name,
            storage_key=stored.stored_file_name,
            storage_path=stored.storage_path,
            mime_type=stored.mime_type,
            file_size=stored.size_bytes,
            sort_order=stored.sort_order,
            owner_type="community",
            member_id=int(total_data["member_id"]),
            community_id=community_id,
            review_id=None,
        )
        db.add(img)
        db.commit()
        db.refresh(community)

    except Exception as e:
        db.rollback()
        # ✅ DB 실패 시 파일 삭제(유령파일 방지)
        try:
            delete_prefix(prefix_key=perm_prefix)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Community create failed: {type(e).__name__}: {e}")

    return {
        "community_id": community_id,
        "member_id": community.member_id,
        "community_active": bool(community.community_active),
        "recommend": int(community.recommend or 0),
        "image_urls": [stored.storage_path],
        "template_id": total_data.get("template_id"),
        "reviews": total_data.get("reviews", []),
    }


# ---------------------------------------------------------------------
# 전체 조회 / 본인 조회 공용
# ---------------------------------------------------------------------
def list_community(
    db: Session,
    *,
    member_id: Optional[int] = None,
    active_only: Optional[bool] = True,   # Optional로 변경
) -> List[Dict[str, Any]]:

    stmt = select(Community)

    if member_id is not None:
        stmt = stmt.where(Community.member_id == member_id)

    # active_only가 True/False/None을 정확히 처리
    if active_only is True:
        stmt = stmt.where(Community.community_active.is_(True))
    elif active_only is False:
        stmt = stmt.where(Community.community_active.is_(False))
    # None이면 필터 없음

    communities = db.execute(stmt.order_by(Community.community_id.desc())).scalars().all()
    if not communities:
        return []

    # 이번 목록에 필요한 community_id만 이미지 조회 (성능/정확성)
    community_ids = [c.community_id for c in communities]

    imgs = db.execute(
        select(ImgFile)
        # 해당 부분 community_j and community_j 둘 다 조회로 변경
        .where(ImgFile.owner_type == "community")
        .where(ImgFile.community_id.in_(community_ids))
        .order_by(ImgFile.community_id.asc(), ImgFile.sort_order.asc())
    ).scalars().all()

    img_map: Dict[int, List[str]] = {}
    for img in imgs:
        img_map.setdefault(img.community_id, []).append(img.storage_path)

    # m = db.execute(select(Member).where(Member.member_id == member_id))
    # print("커뮤 :: m ", m.nickname)

    out: List[Dict[str, Any]] = []
    for c in communities:
        out.append({
            "community_id": c.community_id,
            "member_id": c.member_id,
            "recommend": int(c.recommend or 0),
            "community_active": bool(c.community_active),
            "created_at": c.create_at.isoformat() if getattr(c, "create_at", None) else None,
            "updated_at": c.update_at.isoformat() if getattr(c, "update_at", None) else None,
            "image_urls": img_map.get(c.community_id, []),
        })

    return out


# ---------------------------------------------------------------------
# 상세
# ---------------------------------------------------------------------
def get_community_detail(db: Session, community_id: int) -> Dict[str, Any]:
    c = db.get(Community, community_id)
    if not c:
        raise HTTPException(status_code=404, detail="Community not found")

    imgs = db.execute(
        select(ImgFile)
        .where(ImgFile.community_id == community_id)
        .where(ImgFile.owner_type == "community")
        .order_by(ImgFile.sort_order.asc())
    ).scalars().all()

    return {
        "community_id": c.community_id,
        "member_id": c.member_id,
        "community_active": bool(c.community_active),
        "recommend": int(c.recommend or 0),
        "created_at": c.create_at.isoformat() if getattr(c, "create_at", None) else None,
        "updated_at": c.update_at.isoformat() if getattr(c, "update_at", None) else None,
        "image_urls": [img.storage_path for img in imgs],
    }
