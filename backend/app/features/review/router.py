import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member
from backend.app.features.review.schemas import ReceiptVerifyResponse, ReviewCreateResponse
from backend.app.features.review.service import create_review_from_receipt, verify_receipt

router = APIRouter(prefix="/review", tags=["review"])

@router.post("/receipt/verify", response_model=ReceiptVerifyResponse)
async def receipt_verify(
    type: str = Form("receipt"),
    file: UploadFile = File(...),
    current=Depends(get_current_member),
):
    if (type or "").lower() not in ("receipt", "review"):
        raise HTTPException(status_code=400, detail="type must be 'receipt'")

    receipt_id = uuid.uuid4().hex
    print("영수증 id :: ", receipt_id)

    out = await verify_receipt(member_id=current.member_id, file=file, receipt_id=receipt_id)
    return ReceiptVerifyResponse(receipt_id=out["receipt_id"], extracted=out["extracted"])


@router.post("/review/create", response_model=ReviewCreateResponse)
async def review_create(
    receipt_id: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    rating: int = Form(...),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current=Depends(get_current_member),
):
    out = await create_review_from_receipt(
        db=db,
        member_id=current.member_id,
        receipt_id=receipt_id,
        title=title,
        content=content,
        rating=rating,
        images=images or [],
    )
    return ReviewCreateResponse(review_id=out["review_id"], image_urls=out["image_urls"])
