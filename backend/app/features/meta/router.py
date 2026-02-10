from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.features.meta.service import get_restrictions_etag_meta, get_categories_with_items

router = APIRouter(prefix="/meta", tags=["meta"])

@router.get("/restrictions")
def get_restrictions(request: Request, db: Session = Depends(get_db)):
    etag = get_restrictions_etag_meta(db)

    inm = request.headers.get("if-none-match")
    if inm == etag:
        return Response(status_code=304, headers={"ETag": etag})

    data = get_categories_with_items(db)
    return {"etag": etag, "data": data}