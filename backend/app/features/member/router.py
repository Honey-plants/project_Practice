from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import json

from backend.app.core.database import get_db
from . import schemas, service
from backend.app.common.schemas import responses

from backend.app.models.member import Member
from backend.app.core.security.deps import get_current_member
from backend.app.models.restrictions.member_restriction import MemberRestrictions
from backend.app.models.restrictions.dislike import Dislike

router = APIRouter(prefix="/member", tags=["member"])

# 회원가입
@router.post("", status_code=201)
def create_member(payload: schemas.MemberCreate, db: Session = Depends(get_db)):
    print("회원가입 :: ", payload)
    service.create_member(db, payload)
    return {"message": "register ok"}

# MyPage 연동 - 단일 계정 
@router.get("/me", response_model=schemas.MemberRead)
def get_member(current: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    print("id :: ", current.member_id)
    return service.get_member(db, current.member_id)

# MyPage 연동 - 사용자 정보 update
@router.patch("/me", response_model=schemas.MemberRead)
def update_member(payload: schemas.MemberUpdate, current: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    m = service.update_member(db, current.member_id, payload)
    print("adasdasdAS ::", current.member_id)
    # DB 기준으로 재조회
    item_ids = db.execute(
        select(MemberRestrictions.item_id).where(MemberRestrictions.member_id == m.member_id)
    ).scalars().all()

    dislike_raw = db.execute(
        select(Dislike.dislike_tag).where(Dislike.member_id == m.member_id)
    ).scalar_one_or_none()
    dislike_tags = json.loads(dislike_raw) if dislike_raw else []

    return {
        "member_id":m.member_id,
        "email": m.email,
        "nickname": m.nickname,
        "gender": m.gender,
        "country": m.country,
        "role": m.role,                       # 현재는 role 구분은 ADMIN 관리자 전용에서 요청 및 사용할 예정 // 일반 계정은 role 사용할 필요 x
        "item_ids": list(item_ids),         # 필요하면 실제 DB에서 다시 조회해서 내려주기
        "dislike_tags": dislike_tags,

        # "item_ids": payload.item_ids,         # 필요하면 실제 DB에서 다시 조회해서 내려주기
        # "dislike_tags": dislike_raw,
    }

# MyPage 회원 탈퇴
@router.delete("/me", status_code=200)
def delete_member(current: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    service.delete_member(db, current.member_id)
    return {"message": "member delete ok!"}


# MyPage - NickName 중복체크
@router.get("/nickname/check", response_model=responses.NicknameCheckResponse)
def nickname_check(nickname: str, db: Session = Depends(get_db)):

    # 추가 검증시 필요 로직 현재 사용 x
    # nickname: str = Query(..., min_length=2, max_length=50),

    ok = service.is_nickname_available(db, nickname)
    return {
        "available": ok,
        "message": "available" if ok else "nickname already exists",
    }