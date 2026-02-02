from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np
from AI.review.app.pipeline.step_1_rectify.receipt_types import CropResult


@dataclass(frozen=True)
class CropConfig:
    # ---------- edge (fallback) ----------
    canny1: int = 30
    canny2: int = 120
    blur_ksize: int = 5            # 3/5/7 (5->7 줄무늬 패턴은 작은 블러로는 안죽고 edge 만 켜짐)
    dilate_iter: int = 1            #값이 크면 배경egde 를 너무 합침
    approx_eps_ratio: float = 0.02  #
    min_area_ratio: float = 0.02   # 영수증은 작을 수 있어서 낮게 시작

    border: int = 10
    max_area_ratio: float = 0.92

    # fallback: 4점 못 찾으면 minAreaRect로라도 사각형 뽑기
    allow_minarearect_fallback: bool = True

def _receipt_mask(image_bgr: np.ndarray) -> np.ndarray:
    # 밝고 채도 낮은 영역(흰 종이) 추출
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # 조건: 채도 낮고(s 작음), 밝기 높음(v 큼)
    mask = cv2.inRange(hsv, (0, 0, 160), (180, 80, 255))

    # 구멍 메우기 + 덩어리 만들기
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    return mask


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    rect[0] = pts[np.argmin(s)]      # tl
    rect[2] = pts[np.argmax(s)]      # br
    rect[1] = pts[np.argmin(diff)]   # tr
    rect[3] = pts[np.argmax(diff)]   # bl
    return rect

def _edges(image_bgr: np.ndarray, cfg: CropConfig) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    k = int(cfg.blur_ksize)
    if k >= 3 and k % 2 == 1:
        gray = cv2.GaussianBlur(gray, (k, k), 0)
    edges = cv2.Canny(gray, int(cfg.canny1), int(cfg.canny2))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
    return edges

def _quad_from_minarearect(cnt: np.ndarray) -> np.ndarray:
    rect = cv2.minAreaRect(cnt)           # (center),(w,h),angle
    box = cv2.boxPoints(rect)             # 4 points
    return _order_points(box.astype(np.float32))

def _quad_from_mask(image_bgr: np.ndarray, mask: np.ndarray, cfg: CropConfig):
    h, w = image_bgr.shape[:2]
    img_area = float(h * w)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, {"mask_found": False}

    # 가장 큰 흰 덩어리(종이) 선택
    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)

    meta = {
        "mask_found": True,
        "mask_best_area": float(area),
    }

    # 너무 작거나 너무 크면 실패 처리
    if area < cfg.min_area_ratio * img_area or area > cfg.max_area_ratio * img_area:
        meta["mask_reject_reason"] = "area_out_of_range"
        return None, meta

    peri = cv2.arcLength(cnt, True)
    eps = float(cfg.approx_eps_ratio) * peri
    approx = cv2.approxPolyDP(cnt, eps, True)

    # 4점이면 그걸 쓰고, 아니면 minAreaRect fallback
    if len(approx) == 4 and cv2.isContourConvex(approx):
        quad = _order_points(approx.reshape(4, 2).astype(np.float32))
        meta["mask_quad_type"] = "approx4"
        return quad, meta

    quad = _quad_from_minarearect(cnt)
    meta["mask_quad_type"] = "minAreaRect"
    return quad, meta


def find_receipt_quad(image_bgr: np.ndarray, cfg: CropConfig) -> Tuple[Optional[np.ndarray], Dict[str, Any], np.ndarray]:
    mask = _receipt_mask(image_bgr)
    quad, mask_meta = _quad_from_mask(image_bgr, mask, cfg)
    if quad is not None:
        meta = {
            "found": True,
            "used_method": "mask",
            "mask": mask_meta,
            "cfg": asdict(cfg),
            "quad": quad.tolist(),
        }
        return quad, meta, mask  # edges 대신 mask를 debug로 저장해도 됨

    h, w = image_bgr.shape[:2]
    img_area = float(h * w)

    edges = _edges(image_bgr, cfg)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    best_quad: Optional[np.ndarray] = None
    best_quad_area = 0.0
    biggest_area = 0.0
    best_cnt = None
    best_score = -1e9

    debug_candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > biggest_area:
            biggest_area = area
            best_cnt = cnt

        if area < float(cfg.min_area_ratio) * img_area:
            continue
        if area > float(cfg.max_area_ratio) * img_area:
            continue

        peri = cv2.arcLength(cnt, True)
        eps = float(cfg.approx_eps_ratio) * peri
        approx = cv2.approxPolyDP(cnt, eps, True)

        v = len(approx)

        # keep some debug info (top by area)
        if len(debug_candidates) < 10:
            debug_candidates.append({"area": float(area), "peri": float(peri), "eps": float(eps), "vertices": int(v)})
        else:
            # replace smallest-area candidate if current is bigger
            m = min(range(len(debug_candidates)), key=lambda i: debug_candidates[i]["area"])
            if area > debug_candidates[m]["area"]:
                debug_candidates[m] = {"area": float(area), "peri": float(peri), "eps": float(eps), "vertices": int(v)}

        # accept quad candidates
        if v == 4 and cv2.isContourConvex(approx):
            pts = approx.reshape(4, 2).astype(np.float32)
            quad = _order_points(pts)
            quad_area = float(cv2.contourArea(quad))

            if quad_area > best_quad_area:
                best_quad_area = quad_area
                best_quad = quad

    meta: Dict[str, Any] = {
        "found": best_quad is not None,
        "image_shape": [int(h), int(w)],
        "num_contours": int(len(contours)),
        "min_area_ratio": float(cfg.min_area_ratio),
        "max_area_ratio": float(cfg.max_area_ratio),
        "biggest_contour_area": float(biggest_area),
        "best_quad_area": float(best_quad_area),
        "used_fallback": False,
        "cfg": asdict(cfg),
        "debug_top_candidates": sorted(debug_candidates, key=lambda d: d["area"], reverse=True),
    }

    #  fallback to minAreaRect of biggest contour (still useful)
    if best_quad is None and cfg.allow_minarearect_fallback and best_cnt is not None:
        best_quad = _quad_from_minarearect(best_cnt)
        meta["found"] = True
        meta["used_fallback"] = True
        meta["fallback_type"] = "minAreaRect"

    if best_quad is not None:
        meta["quad"] = best_quad.tolist()

    return best_quad, meta, edges



def warp_receipt(image_bgr: np.ndarray, quad: np.ndarray, cfg: CropConfig) -> Tuple[np.ndarray, Dict[str, Any]]:
    tl, tr, br, bl = quad

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxW = int(max(widthA, widthB))
    maxW = max(maxW, 2)

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH = int(max(heightA, heightB))
    maxH = max(maxH, 2)

    dst = np.array([[0, 0], [maxW - 1, 0], [maxW - 1, maxH - 1], [0, maxH - 1]], dtype=np.float32)

    M = cv2.getPerspectiveTransform(quad.astype(np.float32), dst)
    warped = cv2.warpPerspective(image_bgr, M, (maxW, maxH))

    if cfg.border > 0:
        warped = cv2.copyMakeBorder(
            warped, cfg.border, cfg.border, cfg.border, cfg.border,
            borderType=cv2.BORDER_CONSTANT, value=(255, 255, 255),
        )

    return warped, {"warp_size": [int(warped.shape[0]), int(warped.shape[1])], "border": int(cfg.border)}

def crop_receipt_only(image_bgr: np.ndarray, cfg: CropConfig) -> CropResult:
    quad, find_meta, edges = find_receipt_quad(image_bgr, cfg)
    overlay = image_bgr.copy()
    if quad is not None:
        cv2.polylines(overlay, [quad.astype("int32")], True, (0, 255, 0), 3)

    if quad is None:
        # 못 찾으면 원본 반환(크롭 실패 표시)
        return CropResult(
            cropped_bgr=image_bgr,
            quad=None,
            overlay_bgr=overlay,
            edges=edges,
            meta={"find": find_meta, "warp": {"applied": False, "reason": "quad_not_found"}},
        )

    cropped, warp_meta = warp_receipt(image_bgr, quad, cfg)
    return CropResult(
        cropped_bgr=cropped,
        quad=quad,
        overlay_bgr=overlay,
        edges=edges,
        meta={"find": find_meta, "warp": warp_meta},
    )

'''
영수증 quad 찾기 + warp(펴기)
'''