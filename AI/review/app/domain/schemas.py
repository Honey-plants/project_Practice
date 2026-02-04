# ai/review/app/domain/schemas.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# -------------------------
# Common small schemas
# -------------------------
class Coords(BaseModel):
    x: Optional[str] = None  # naver mapx (TM128 * 1e7 같은 문자열)
    y: Optional[str] = None  # naver mapy


class StoreInfo(BaseModel):
    store_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    coords: Optional[Coords] = None
    store_name_en: Optional[str] = None

    # 원하면 네이버 raw도 저장 가능(디버그용)
    naver_raw: Optional[Dict[str, Any]] = None


class OCRItem(BaseModel):
    text: str
    score: float
    poly: List[List[int]]  # [[x,y]*4]
    bbox: List[int]        # [x1,y1,x2,y2]


class ReceiptExtracted(BaseModel):
    phone: Optional[str] = None
    phone_partial: Optional[str] = None  # 2253-6373 같은 형태
    area_code: Optional[str] = None      # 02/031...
    menu_ko: List[str] = Field(default_factory=list)
    menu_en: List[str] = Field(default_factory=list)

class DebugArtifacts(BaseModel):
    # 운영 모드에서는 비워도 됨
    images: Dict[str, str] = Field(default_factory=dict)   # {"00_original": ".../00.jpg", ...}
    jsons: Dict[str, str] = Field(default_factory=dict)    # {"ocr_result": ".../ocr.json", ...}
    enrich: Optional[Dict[str, Any]] = None


# -------------------------
# Pipeline Context (internal contract)
# -------------------------
class ImagesCtx(BaseModel):
    input_path: Optional[str] = None
    rectified_path: Optional[str] = None  # step1 결과 (cropped+deskew+post)
    # 필요하면 중간도 추가 가능
    cropped_path: Optional[str] = None


class OcrCtx(BaseModel):
    items: List[OCRItem] = Field(default_factory=list)
    n_items: int = 0
    overlay_path: Optional[str] = None

class NormalizeState(BaseModel):
    lines: List[str] = []
    store_name_candidates: List[str] = []

class NormalizeCtx(BaseModel):
    lines: List[str] = Field(default_factory=list)
    y_threshold: int = 15


class PipelineContext(BaseModel):
    job_id: Optional[str] = None
    mode: Literal["debug", "prod"] = "debug"

    images: ImagesCtx = Field(default_factory=ImagesCtx)
    ocr: OcrCtx = Field(default_factory=OcrCtx)
    normalize: NormalizeCtx = Field(default_factory=NormalizeCtx)

    extracted: ReceiptExtracted = Field(default_factory=ReceiptExtracted)
    store: StoreInfo = Field(default_factory=StoreInfo)

    debug: DebugArtifacts = Field(default_factory=DebugArtifacts)

    # 마지막 step에서만 세팅해도 됨(외부 응답)
    final: Optional["FinalReceiptResponse"] = None


# -------------------------
# Final Response Schema (API response)
# -------------------------
class FinalReceiptResponse(BaseModel):
    store_name: Optional[str] = None
    store_name_en: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    coords: Optional[Coords] = None
    menu_name: List[str] = Field(default_factory=list)
    menu_en: List[str] = Field(default_factory=list)

