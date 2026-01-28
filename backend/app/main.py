import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 1) sys.path 세팅은 다른 import들보다 먼저
ROOT_DIR = Path(__file__).resolve().parents[2]  # final_project
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# from backend.app.core.database import Base, engine   # engine 가져와야 create_all 가능
# import backend.app.models                            # 모델 로딩 보장(필수)
from backend.app.api_router import api_router        # 상대경로 말고 절대경로 추천


# import api_router  # 공통 router 설정
app = FastAPI()


class ForceUTF8Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        ct = response.headers.get("content-type", "")
        # JSON 응답에 charset이 없으면 강제로 붙임
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


# ---------------------------
# Async job enqueue endpoints
# ---------------------------

from .core.job_queue import connect_redis, set_job, get_job, enqueue_task, utc_now_iso, QUEUE_NAME

class EnqueueRequest(BaseModel):
    task: str = Field(..., examples=["ping", "sleep", "review_receipt_ocr", "menu_assistant_pipeline", "journal_generate"])
    payload: Dict[str, Any] = Field(default_factory=dict)


class EnqueueResponse(BaseModel):
    job_id: str
    status: str
    queued_at: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    updated_at: Optional[str] = None
    task: Optional[str] = None
    queued_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Any] = None


@app.post("/jobs", response_model=EnqueueResponse, status_code=202)
def create_job(req: EnqueueRequest):
    try:
        r = connect_redis()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {type(e).__name__}: {e}")

    job_id = enqueue_task(r, req.task, req.payload)

    # job_id로 조회하여 queued_at 등 확인 (enqueue_task 내부에서 이미 세팅됨)
    # 성능 최적화를 위해 여기서는 직접 생성했던 값 등을 반환하거나 재조회
    # 여기선 간단히 get_job 호출 없이 리턴

    return EnqueueResponse(job_id=job_id, status="PENDING", queued_at=utc_now_iso())


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def read_job(job_id: str):
    try:
        r = connect_redis()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"redis unavailable: {type(e).__name__}: {e}")

    data = get_job(r, job_id)
    if not data:
        raise HTTPException(status_code=404, detail="job not found")

    def _maybe_json(v: Optional[str]) -> Any:
        if v is None:
            return None
        try:
            return json.loads(v)
        except Exception:
            return v

    return JobStatusResponse(
        job_id=data.get("job_id", job_id),
        status=data.get("status", "UNKNOWN"),
        updated_at=data.get("updated_at"),
        task=data.get("task"),
        queued_at=data.get("queued_at"),
        started_at=data.get("started_at"),
        finished_at=data.get("finished_at"),
        result=_maybe_json(data.get("result")),
        error=_maybe_json(data.get("error")),
    )


# 기존 라우터 유지
app.include_router(api_router)
