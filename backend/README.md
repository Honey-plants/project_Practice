# backend 설명 및 tree 구조 안내
각 폴더의 역할

app/models/
→ DB 테이블(SQLAlchemy) 정의만 둠 (Entity 역할)

app/features/*/schemas.py
→ 요청/응답 DTO(Pydantic) (Create/Read/Update)

app/features/*/router.py
→ FastAPI 라우팅만 (최대한 얇게)

app/features/*/service.py
→ 비즈니스 로직 (닉네임 유니크 체크, item_ids replace 등)

app/common/schemas/responses.py
→ DeleteResponse 같은 공통 응답 스키마

# restrictions의 category/item/restrictions/dislike 4개
app/models/restrictions/category.py
app/models/restrictions/item.py
app/models/restrictions/dislike.py
app/models/restrictions/member_restriction.py

# 수정 로직 예상
SQLAlchemy 모델은 무조건 app/models 아래
Pydantic 스키마는 feature별 schemas.py + 공통은 common/schemas
라우터는 얇게, 로직은 service로 :: service 추가 작업중

# JWT_SECRET_KEY 생성 
PROMPT : python -c "import secrets; print(secrets.token_urlsafe(64))"

# sub: 누구토큰인지
# type: access / refresh구분
# jti: 토큰고유ID(블랙리스트핵심)
# iat: 언제발급됐는지
# exp: 언제만료되는지

# docker
## 최상위 폴더에서 실행
실행 : docker compose -f docker/redis/docker-compose.yml up -d
중지 : docker compose -f docker/redis/docker-compose.yml down

동작 확인 : docker exec -it app_redis redis-cli ping -> pong
key 확인 : docker exec -it app_redis redis-cli keys "*"

# docker 로그인 테스트
- docker exec -it app_redis redis-cli keys "refresh:*"
- docker exec -it app_redis redis-cli get "refresh:<member_id>"

# role admin/user 구분
- db member/type으로 구분 예정
- rotate 사용으로 refresh 재발급 형태 수정중

# hash err 발생시 확인사항
- pip uninstall -y bcrypt passlib
- pip install passlib==1.7.4
- pip install bcrypt==3.2.2

- python -c "import bcrypt; from passlib.context import CryptContext; print('bcrypt', bcrypt.__version__); ctx=CryptContext(schemes=['bcrypt']); print(ctx.hash('123123'))"

# { "is_active": true }
- DB: bool/boolean (default 1)
- Model: Boolean
- Schema: bool
- Front: true/false

# FILE UPLOAD
- path = /images/{memberId}/{file_key}
- 형태로 PATH 지정
- 테이블 문의 ERD CLOUD 확인 필수!

# FILE UPLOAD 파일 구성 안내
- util.py는 “정책/선택/규칙”만 (factory, validate, path)
- storage/local, s3는 “구현체”만 (save/store/delete)

# ADMIN 관리자 계정 
- GET /members/me
- PATCH /members/me
- DELETE /members/me
- (관리자용이 필요하면) GET /members/{member_id} 는 admin만 허용

# docker refresh 확인
- SCAN 0 MATCH bl:* COUNT 100

# MENU / RECEIPT 로직 순서
- MENU: 업로드 → AI 분석 → 결과 JSON 반환 → 임시파일 삭제
- RECEIPT: 업로드 → OCR/검증 AI → Redis에 세션 저장(upload_id) → 프론트 추가입력 + 이미지(0~3) → Review 생성 + ImgFile 영구저장 → 임시파일 삭제 + Redis 세션 삭제

# 이제 이 폴더 정책을 실제 로직에 적용하는 방식
## MENU 정책 적용

- run_id 생성
- temp에 input 저장
- AI 실행 (input 경로)
- result.json 생성(디버깅용)
- 응답으로 result JSON 내려줌
- delete_prefix(menu/{run_id}) 로 폴더 통째 삭제
- RECEIPT 정책 적용
- upload_id 생성
- temp에 input 저장
- AI(OCR/검증) 실행
- (선택) ocr.json 저장
- Redis에 {upload_id, member_id, temp_prefix} 저장 + TTL
- 2단계 성공 시 delete_prefix(receipt/{upload_id}) 로 삭제
- 2단계 안 오면 → 로컬 스캔 cleanup으로 TTL 지난 폴더 삭제 / S3는 Lifecycle