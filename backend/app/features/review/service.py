import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.common.service.file_upload_service import (
    build_temp_prefix,
    delete_prefix,
    ensure_local_path,
    save_permanent_asset,
    upload_input_file,
)
from backend.app.common.service.receipt_session_service import ReceiptSessionService
from backend.app.models.img_file import ImgFile
from backend.app.models.review import Review


def run_receipt_ai(*, image_path: str, receipt_id: str) -> Dict[str, Any]:
    from AI.review.app.pipeline.orchestrator import PipelineConfig, run_pipeline
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("Missing GEMINI_API_KEY (required for receipt pipeline step4)")

    print("ai 진입")
    cfg = PipelineConfig(
        mode="prod",
        test_base_dir=Path("AI/review/test"),
        run_name=receipt_id,
        gemini_api_key=gemini_api_key,
        naver_cfg={
            "NAVER_CLIENT_ID": os.getenv("NAVER_CLIENT_ID") or "",
            "NAVER_CLIENT_SECRET": os.getenv("NAVER_CLIENT_SECRET") or "",
        },
    )

    return run_pipeline(input_image_path=image_path, cfg=cfg)


async def verify_receipt(*, member_id: int, file: UploadFile, receipt_id: str) -> Dict[str, Any]:
    tmp_prefix = build_temp_prefix(upload_type="receipt", scope_id=receipt_id)
    print("검증 service 입장 :: ")
    try:
        obj = await upload_input_file(
            upload_type="receipt",
            member_id=member_id,
            upload=file,
            scope_id=receipt_id,
            is_temp=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    local_path, cleanup = ensure_local_path(obj)
    try:
        ai_out = run_receipt_ai(image_path=local_path, receipt_id=receipt_id)
        final = ai_out.get("final") or {}

        ReceiptSessionService.put(receipt_id=receipt_id, member_id=member_id, payload=final)

        return {"receipt_id": receipt_id, "extracted": final}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"receipt ai failed: {type(e).__name__}: {e}")
    finally:
        print("마지막 finally")
        cleanup()
        delete_prefix(prefix_key=tmp_prefix)


def _pick_location(extracted: Dict[str, Any]) -> str:
    return (
        (extracted.get("store_name") or "")
        or (extracted.get("address") or "")
        or (extracted.get("city") or "")
        or "unknown"
    )


def _pick_menu_name(extracted: Dict[str, Any]) -> str:
    names = extracted.get("menu_name") or []
    if isinstance(names, list) and names:
        return str(names[0])
    return "unknown"


async def create_review_from_receipt(
    *,
    db: Session,
    member_id: int,
    receipt_id: str,
    title: str,
    content: str,
    rating: int,
    images: List[UploadFile],
) -> Dict[str, Any]:
    session = ReceiptSessionService.get(receipt_id=receipt_id)
    if not session:
        raise HTTPException(status_code=400, detail="receipt expired (verify again)")
    if int(session.get("member_id") or 0) != int(member_id):
        raise HTTPException(status_code=403, detail="forbidden")

    extracted = session.get("payload") or {}

    location = _pick_location(extracted)
    menu_name = _pick_menu_name(extracted)

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1~5")
    if len(images) > 3:
        raise HTTPException(status_code=400, detail="images max 3")

    review = Review(
        review_title=title,
        review_content=content,
        rating=rating,
        location=location,
        menu_name=menu_name,
        review_items=None,
        member_id=member_id,
        available=True,
    )
    db.add(review)
    db.flush()

    image_urls: List[str] = []

    for idx, img in enumerate(images):
        stored = await save_permanent_asset(
            owner_type="review",
            owner_id=review.review_id,
            member_id=member_id,
            upload=img,
            sort_order=idx,
        )

        db.add(
            ImgFile(
                origin_name=stored.org_file_name,
                storage_key=stored.stored_file_name,
                storage_path=stored.storage_path,
                mime_type=stored.mime_type,
                file_size=stored.size_bytes,
                sort_order=idx,
                owner_type="review",
                member_id=member_id,
                review_id=review.review_id,
                community_id=None,
            )
        )
        image_urls.append(stored.storage_path)

    db.commit()

    ReceiptSessionService.delete(receipt_id=receipt_id)

    return {"review_id": review.review_id, "image_urls": image_urls}
