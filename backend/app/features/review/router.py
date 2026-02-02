import uuid
from typing import List
from sqlalchemy import select
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member
from backend.app.common.utils.debug import log_exception
from backend.app.features.review.schemas import ReceiptVerifyResponse, ReviewCreateResponse, ReviewContentUpdateResponse, ReviewContentUpdate, ReviewRead
from backend.app.features.review.service import verify_receipt, create_review_from_receipt, list_reviews, get_review_detail, update_review_content_only

from backend.app.models.restrictions.member_restriction import MemberRestrictions

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/receipt/verify", response_model=ReceiptVerifyResponse)
async def receipt_verify(
    type: str = Form("receipt"),
    file: UploadFile = File(...),
    current=Depends(get_current_member),
):
    if (type or "").lower().strip() != "receipt":
        raise HTTPException(status_code=400, detail="type must be 'receipt'")

    receipt_id = uuid.uuid4().hex

    try:
        out = await verify_receipt(member_id=current.member_id, file=file, receipt_id=receipt_id)
        return ReceiptVerifyResponse(receipt_id=out["receipt_id"], extracted=out.get("final") or {})
    except Exception as e:
        log_exception("router.receipt_verify", e)
        raise


@router.post("/create", response_model=ReviewCreateResponse)
async def review_create(
    receipt_id: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(...),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current=Depends(get_current_member),
):
    imgs = images or []
    if len(imgs) > 3:
        raise HTTPException(status_code=400, detail="images max 3")

    try:
        out = await create_review_from_receipt(
            db=db,
            member_id=current.member_id,
            receipt_id=receipt_id,
            title=title,
            content=content,
            rating=rating,
            images=imgs,
        )
        return ReviewCreateResponse(review_id=out["review_id"], image_urls=out["image_urls"])
    except Exception as e:
        log_exception("router.review_create", e)
        raise

@router.get("", response_model=list[ReviewRead])
def review_list(db: Session = Depends(get_db)):
    return list_reviews(db, limit=50)


@router.get("/{review_id}", response_model=ReviewRead)
def review_detail(
    review_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_member),
):
    print("review 상세 진입 :: ", current.member_id)

    return get_review_detail(db, review_id)


@router.patch("/{review_id}", response_model=ReviewContentUpdateResponse)
def review_update_content(
    review_id: int,
    payload: ReviewContentUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_member),
):
    return update_review_content_only(
        db,
        review_id=review_id,
        current_member_id=current.member_id,
        current_role=getattr(current, "role", None),
        new_content=payload.review_content,
    )