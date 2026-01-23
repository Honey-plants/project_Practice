import sys
from pathlib import Path

# 1) sys.path 세팅은 다른 import들보다 먼저
ROOT_DIR = Path(__file__).resolve().parents[2]  # final_project
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

# from backend.app.core.database import Base, engine   # engine 가져와야 create_all 가능
# import backend.app.models                            # 모델 로딩 보장(필수)
from backend.app.api_router import api_router        # 상대경로 말고 절대경로 추천

app = FastAPI()

class ForceUTF8Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        ct = response.headers.get("content-type", "")
        if ct.startswith("application/json") and "charset=" not in ct:
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# def on_startup():
#     # 2) create_all은 startup에서 1번 + engine 바인딩
#     Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

app.include_router(api_router)