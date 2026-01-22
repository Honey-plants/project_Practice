from fastapi import APIRouter, Depends, Response, Cookie, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member, oauth2_scheme
from backend.app.features.auth import service, schemas

from backend.app.core.security import jwt

router = APIRouter(prefix="/auth", tags=["auth"])

# front 확인 할 Cookie
COOKIE_NAME = "refresh_token"

# LOGIN
@router.post("/login", response_model=schemas.AccessTokenResponse)
def login(response: Response, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print("login form :: ", form)
    access, refresh = service.login_issue_tokens(db, email=form.username, password=form.password)

    print("acc :: ", access)

    print("refresh token : ", refresh)

    # refresh 생성 시 exp 구하기
    decode_refresh = jwt.decode_token(refresh)
    ttl = jwt.exp_seconds_left(decode_refresh)

    print("cookie name :: ", COOKIE_NAME)

    # refresh는 HttpOnly 쿠키로 저장
    response.set_cookie(
        key=COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=False,      # 로컬 http면 False, 배포(https)면 True
        samesite="lax",    # 프론트/백 완전 다른 도메인이면 none+secure 필요
        # path="/auth",    # /auth 에서 전체 관리 위해서 / 변경
        path="/",
        max_age=ttl,
    )

    print("refresh set cookie :: ", response)

    return {"access_token": access, "token_type": "bearer"}

# REFRESH TOKEN 재발급
@router.post("/refresh", response_model=schemas.AccessTokenResponse)
def refresh(response: Response, db: Session = Depends(get_db), refresh_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh cookie")

    new_access, new_refresh = service.refresh_rotate_tokens(db, refresh_token)

    new_refresh_payload = jwt.decode_token(new_refresh)
    ttl = jwt.exp_seconds_left(new_refresh_payload)

    response.set_cookie(
        key=COOKIE_NAME,
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        # path="/auth",    # /auth 에서 전체 관리 위해서 / 변경
        path="/",
        max_age=ttl,
    )
    return {"access_token": new_access, "token_type": "bearer"}

# LOGOUT
@router.post("/logout")
def logout(response: Response, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # service.logout(token)

    # logout refresh token revoked 로직 추가!
    service.logout(db, token)

    # front cookie refresh token 삭제 처리
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"ok": True}

# 현재 USER 정보
@router.get("/me")
def me(current=Depends(get_current_member)):
    return {
        "member_id": current.member_id,
        "email": current.email,
        "nickname": current.nickname,
    }

# redis test
from fastapi import APIRouter
from backend.app.core.cache.redis import redis_client

# router = APIRouter(prefix="/debug", tags=["debug"])
#
# @router.get("/redis")
# def redis_health():
#     try:
#         redis_client.set("debug:ping", "pong", ex=30)
#         v = redis_client.get("debug:ping")
#         return {"redis": "ok", "value": v}
#     except Exception as e:
#         return {"redis": "fail", "error": str(e)}