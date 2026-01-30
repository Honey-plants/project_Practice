import os
from pathlib import Path
from dotenv import load_dotenv

# 실제 프로젝트 위치 :: backend 하위에 위치 upload 폴더 생성
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"  # backend/.env
load_dotenv(ENV_PATH, override=True)


def _read_secret(name: str, default: str = "") -> str:
    file_path = os.getenv(f"{name}_FILE")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return os.getenv(name, default)

# ---- DB ----
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "final_project")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = _read_secret("DB_PASSWORD", "")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# ---- JWT ----
JWT_SECRET_KEY = _read_secret("JWT_SECRET_KEY", "CHANGE_ME__PLEASE_SET_ENV")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
# REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "3"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))

# Redis
from urllib.parse import urlparse

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
u = urlparse(REDIS_URL)

REDIS_HOST = u.hostname or "redis"
REDIS_PORT = u.port or 6379
REDIS_DB = int((u.path or "/0").lstrip("/") or "0")


print("ENV_PATH =", ENV_PATH)
print("ENV exists =", ENV_PATH.exists())


# -- FILE UPLOAD --
# 현재 LOCAL 개발 사용
# S3: STORAGE_DRIVER=s3 + 버킷/리전/프리픽스 세팅
STORAGE_DRIVER = os.getenv("STORAGE_DRIVER", "local")  # local | s3

# 프로젝트 root 설정 :: 추후 S3 변경시 변동 적음
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 실제 저장 위치
LOCAL_UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", str(PROJECT_ROOT / "upload"))

# 추후 E2C S3 사용 예정
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "")
S3_PREFIX = os.getenv("S3_PREFIX", "uploads")
# upload :: upload/menu 폴더명 구조 잡기 좋음