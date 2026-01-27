from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.security.deps import require_admin
from backend.app.core.database import get_db
from . import schemas, service

router = APIRouter(prefix="/restrictions", tags=["restrictions"])

# Category, Item list 조회
@router.get("", response_model=list[schemas.CategoryItemRead], dependencies=[Depends(require_admin)],)
def admin_restrictions(db: Session = Depends(get_db)):
    print("router db ::", db)
    return service.get_categories_with_items(db)