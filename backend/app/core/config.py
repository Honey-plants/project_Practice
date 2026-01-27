import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[3] / ".env"  # backend/.env
load_dotenv(ENV_PATH)

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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
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
