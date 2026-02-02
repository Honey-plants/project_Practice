import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.core import config
from backend.app.common.utils.debug import log_exception
from backend.app.common.service.file_upload_service import (
    build_temp_prefix,
    ensure_local_path,
    upload_input_file,
    save_permanent_asset,
)
from backend.app.common.service.receipt_session_service import ReceiptSessionService
from backend.app.features.review.schemas import ReviewContentUpdate
from backend.app.models.img_file import ImgFile
from backend.app.models.review import Review
from backend.app.models.restrictions import MemberRestrictions

def run_receipt_ai_step5(*, image_path: str, receipt_id: str, base_dir: Path) -> Dict[str, Any]:
    """
     Receipt: step5까지 전부 수행 (OCR 포함)
     결과물(run_dir, final json 등)은 base_dir 아래로 떨어지게 설정
    """
    from AI.review.app.pipeline.orchestrator import PipelineConfig, run_pipeline

    print("ai 진입(receipt full pipeline)")

    # base_dir 예: <PROJECT_ROOT>/uploads/tmp/receipt/<receipt_id>/runs_root
    base_dir.mkdir(parents=True, exist_ok=True)

    cfg = PipelineConfig(
        mode="prod",
        test_base_dir=base_dir,      #  결과물 생성 위치를 temp로 고정
        run_name=receipt_id,
        # step4에서 필요하면 키 넣기 (너가 사용한다 했으니 env에서 가져오거나 config에 넣어)
        gemini_api_key=config.GEMINI_API_KEY if hasattr(config, "GEMINI_API_KEY") else None,
        naver_cfg={
            "NAVER_CLIENT_ID": getattr(config, "NAVER_CLIENT_ID", ""),
            "NAVER_CLIENT_SECRET": getattr(config, "NAVER_CLIENT_SECRET", ""),
        },
    )

    return run_pipeline(input_image_path=image_path, cfg=cfg)


async def verify_receipt(*, member_id: int, file: UploadFile, receipt_id: str) -> Dict[str, Any]:
    """
     verify 단계에서 step5까지 수행
     최상위 uploads/tmp 밑에 결과(run_dir, json) 유지
    """
    # 업로드 temp prefix (폴더)
    tmp_prefix = build_temp_prefix(upload_type="receipt", scope_id=receipt_id)
    # run 결과를 tmp_prefix 안에 넣는다 (프론트가 이후 읽을 수 있도록)
    runs_root = Path(tmp_prefix) / "runs"

    print("검증 service 입장 :: tmp_prefix =", tmp_prefix)

    # 1) input 저장
    try:
        obj = await upload_input_file(
            upload_type="receipt",
            member_id=member_id,
            upload=file,
            scope_id=receipt_id,
            is_temp=True,
        )
    except Exception as e:
        log_exception("receipt.upload_reject", e)
        raise HTTPException(status_code=400, detail=str(e))

    # 2) 로컬 경로 확보
    local_path, cleanup = ensure_local_path(obj)

    try:
        # 3) AI step5까지 수행
        ai_out = run_receipt_ai_step5(image_path=local_path, receipt_id=receipt_id, base_dir=runs_root)

        # 4) 프론트 재사용을 위해 redis/session에 “최종 결과”도 저장 가능
        # run_pipeline 리턴 형식이 {"run_dir": "...", "final": ...} 이니까 final을 저장
        final_payload = ai_out.get("final") or {}
        ReceiptSessionService.put(receipt_id=receipt_id, member_id=member_id, payload=final_payload)

        #  그리고 temp 폴더에도 최종 파일을 하나 더 “고정 파일명”으로 만들어두면 프론트가 접근 편함
        try:
            out_path = Path(tmp_prefix) / "receipt_final.json"
            out_path.write_text(json.dumps(final_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        return {
            "receipt_id": receipt_id,
            "final": final_payload,
            "tmp_prefix": tmp_prefix,   # 디버그용(원하면 프론트엔 숨겨)
        }

    except Exception as e:
        log_exception("receipt.ai_failed", e)
        raise HTTPException(status_code=500, detail=f"receipt ai failed: {type(e).__name__}: {e}")

    finally:
        cleanup()
        #  정책: receipt는 결과를 temp에 담아둘 것이므로 prefix 삭제하지 않는다.
        # delete_prefix(prefix_key=tmp_prefix)  # ❌ 하면 안됨


def _pick_location(final_payload: Dict[str, Any]) -> str:
    # final payload 구조에 맞춰서 필요 값 뽑기
    return final_payload.get("store_name") or final_payload.get("address") or "unknown"


def _pick_menu_name(final_payload: Dict[str, Any]) -> str:
    names = final_payload.get("menu_name") or []
    if isinstance(names, list) and names:
        return str(names[0])
    return final_payload.get("menu") or "unknown"


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

    final_payload = session.get("payload") or {}


    # location  위, 경도 값
    location = _pick_location(final_payload)
    # menu_name , 형태로 저장 // 출력은 list형태로
    menu_name = _pick_menu_name(final_payload)

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1~5")
    if len(images) > 3:
        raise HTTPException(status_code=400, detail="images max 3")

    member_item_ids = db.execute(
        select(MemberRestrictions.item_id)
        .where(MemberRestrictions.member_id == member_id)
    ).scalars().all()

    # 중복 제거 + 정렬(선택)
    unique_ids = sorted(set(int(x) for x in member_item_ids))

    # CSV 문자열로 만들기: "10,11,25" (없으면 None 또는 "" 정책 선택)
    review_items_csv = ",".join(map(str, unique_ids)) if unique_ids else None

    review = Review(
        review_title=title,
        review_content=content,
        rating=rating,
        location=location,
        menu_name=menu_name,
        member_id=member_id,
        available=True,
        review_items=review_items_csv,
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

    # receipt 세션은 review create 완료 후 삭제 (정책에 맞게)
    ReceiptSessionService.delete(receipt_id=receipt_id)

    return {"review_id": review.review_id, "image_urls": image_urls}


def list_reviews(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    # 최신순
    reviews = db.execute(
        select(Review)
        .where(Review.available == True)  # available만 노출
        .order_by(Review.review_id.desc())
        .limit(limit)
    ).scalars().all()

    if not reviews:
        return []

    # review_ids = [r.review_id for r in reviews]

    # 이미지: review_id 기준으로 묶기
    imgs = db.execute(
        select(ImgFile)
        # .where(ImgFile.review_id.in_(review_ids))
        .where(ImgFile.owner_type == "review")
        .order_by(ImgFile.review_id.asc(), ImgFile.sort_order.asc())
    ).scalars().all()

    img_map: Dict[int, List[str]] = {}
    for img in imgs:
        img_map.setdefault(img.review_id, []).append(img.storage_path)

    out: List[Dict[str, Any]] = []
    for r in reviews:
        out.append({
            "review_id": r.review_id,
            "member_id": r.member_id,
            "review_title": r.review_title,
            "review_content": r.review_content,
            "rating": r.rating,
            "location": r.location,
            # "menu_name": r.menu_name,
            "menu_name": [r.menu_name] if r.menu_name else [],
            # "menu_name": _parse_csv_ids(r.menu_name),
            "review_items": _parse_csv_ids(r.review_items),
            # 프론트가 created_at/updated_at 키를 기대해서 맞춰줌
            "created_at": r.create_at.isoformat() if getattr(r, "create_at", None) else None,
            "updated_at": r.update_at.isoformat() if getattr(r, "update_at", None) else None,
            "image_urls": img_map.get(r.review_id, []),
        })
    return out


def get_review_detail(db: Session, review_id: int) -> Dict[str, Any]:
    r = db.get(Review, review_id)
    if not r or not r.available:
        raise HTTPException(status_code=404, detail="Review not found")

    imgs = db.execute(
        select(ImgFile)
        .where(ImgFile.review_id == review_id)
        .where(ImgFile.owner_type == "review")
        .order_by(ImgFile.sort_order.asc())
    ).scalars().all()

    print("detail  rr :: ", r.menu_name)

    return {
        "review_id": r.review_id,
        "member_id": r.member_id,
        "review_title": r.review_title,
        "review_content": r.review_content,
        "rating": r.rating,
        "location": r.location,
        # "menu_name": r.menu_name,
        "menu_name": [r.menu_name] if r.menu_name else [],
        # "menu_name": _parse_csv_ids(r.menu_name),
        # "menu_names": [r.menu_name] if r.menu_name else [],
        "review_items": _parse_csv_ids(r.review_items),
        "created_at": r.create_at.isoformat() if getattr(r, "create_at", None) else None,
        "updated_at": r.update_at.isoformat() if getattr(r, "update_at", None) else None,
        "image_urls": [img.storage_path for img in imgs],
    }


def update_review_content_only(
    db: Session,
    *,
    review_id: int,
    current_member_id: int,
    current_role: str | None,
    new_content: str,
) -> Dict[str, Any]:
    r = db.get(Review, review_id)
    if not r or not r.available:
        raise HTTPException(status_code=404, detail="Review not found")

    #  본인만 수정 (ADMIN 예외 허용)
    is_admin = (current_role or "").upper() == "ADMIN"
    if (r.member_id != current_member_id) and (not is_admin):
        raise HTTPException(status_code=403, detail="Not allowed")

    r.review_content = new_content
    db.add(r)
    db.commit()
    db.refresh(r)

    return {
        "review_id": r.review_id,
        "review_content": r.review_content,
        "updated_at": r.update_at.isoformat() if getattr(r, "update_at", None) else None,
    }

# Review_items str -> list 변환 출력
def _parse_csv_ids(raw) -> list[int]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw]
    # raw == "3,7,12"
    return [int(x) for x in str(raw).split(",") if str(x).strip().isdigit()]