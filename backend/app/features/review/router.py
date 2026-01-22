from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from backend.app.core.security.deps import get_current_member
from backend.app.common.service.file_upload_service import (
    upload_input_file, ensure_local_path, delete_input_file
)
from backend.app.common.schemas.file_upload_schema import UploadInputResponse

router = APIRouter(prefix="/review", tags=["review"])

@router.post("/upload", response_model=UploadInputResponse)
async def review_upload(type: str = Form("review"), image: UploadFile = File(...), current=Depends(get_current_member), ):
    obj = await upload_input_file(upload_type=type, member_id=current.member_id, upload=image)

    cleanup_download = lambda: None

    try:
        local_path, cleanup_download = ensure_local_path(obj)

        # review 로직 실행
        # result = review_service.process(local_path)

        return UploadInputResponse(
            upload_type=obj.upload_type,
            member_id=obj.member_id,
            file_key=obj.file_key,
            stored_file_name=obj.stored_file_name,
            org_file_name=obj.org_file_name,
            mime_type=obj.mime_type,
            size_bytes=obj.size_bytes,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cleanup_download()
        delete_input_file(file_key=obj.file_key)


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
#
# from app.core.database import get_db
# from . import schemas
# from ...models.review import model
#
# router = APIRouter(prefix="/reviews", tags=["reviews"])
#
# @router.post("", response_model=schemas.ReviewRead)
# def create_review(payload: schemas.ReviewCreate, db: Session = Depends(get_db)):
#     m = db.query(model).filter(model.member_id == payload.member_id).first()
#     if not m:
#         raise HTTPException(status_code=400, detail="Invalid member_id")
#
#     r = model(**payload.model_dump())
#     db.add(r)
#     db.commit()
#     db.refresh(r)
#     return r
#
# @router.get("", response_model=list[schemas.ReviewRead])
# def list_reviews(member_id: int | None = None, db: Session = Depends(get_db)):
#     q = db.query(model)
#     if member_id is not None:
#         q = q.filter(model.member_id == member_id)
#     return q.order_by(model.review_id.desc()).all()
#
# @router.get("/{review_id}", response_model=schemas.ReviewRead)
# def get_review(review_id: int, db: Session = Depends(get_db)):
#     r = db.query(model).filter(model.review_id == review_id).first()
#     if not r:
#         raise HTTPException(status_code=404, detail="Review not found")
#     return r
#
# @router.delete("/{review_id}")
# def delete_review(review_id: int, db: Session = Depends(get_db)):
#     r = db.query(model).filter(model.review_id == review_id).first()
#     if not r:
#         raise HTTPException(status_code=404, detail="Review not found")
#     db.delete(r)
#     db.commit()
#     return {"deleted": True, "review_id": review_id}
#
#
# @router.patch("/{review_id}", response_model=schemas.ReviewRead)
# def update_review(review_id: int, payload: schemas.ReviewUpdate, db: Session = Depends(get_db)):
#     r = db.query(model).filter(model.review_id == review_id).first()
#     if not r:
#         raise HTTPException(status_code=404, detail="Review not found")
#
#     data = payload.model_dump(exclude_unset=True)
#     if not data:
#         return r
#
#     # member_id 변경 시 존재 확인
#     if "member_id" in data and data["member_id"] is not None:
#         m = db.query(model).filter(model.member_id == data["member_id"]).first()
#         if not m:
#             raise HTTPException(status_code=400, detail="Invalid member_id")
#
#     for k, v in data.items():
#         setattr(r, k, v)
#
#     db.commit()
#     db.refresh(r)
#     return r
