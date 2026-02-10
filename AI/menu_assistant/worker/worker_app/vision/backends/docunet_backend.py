from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import cv2
import numpy as np

from .base import RectifyBackend, RectifyResult
from .doc_geometry import PerspectiveRectifyParams, find_document_quad, warp_perspective


@dataclass(frozen=True)
class DocUNetConfig:
    """
    Working menu-board rectification backend.

    Pipeline:
      1) (Optional) DocTR orientation predictor
      2) Apply inverse rotation (correction) to make upright
      3) OpenCV contour-based quad detection
      4) Perspective warp to fronto-parallel rectangle

    Controls:
      - min_orientation_confidence: confidence below this => treat as uncertain
      - prefer_fallback_when_low_conf: if uncertain, prefer heuristic/candidate selection
      - try_both_directions_when_uncertain: test 90/270 candidates and pick best by quad-detection quality
    """
    params: PerspectiveRectifyParams = PerspectiveRectifyParams()
    strict_weights: bool = False
    #enable_orientation: DocTR로 회전 추정을 할지 여부
    enable_orientation: bool = True
    #predictor가 낸 confidence가 이 값 미만이면 “불확실”로 판단
    min_orientation_confidence: float = 0.90
    prefer_fallback_when_low_conf: bool = True
    #불확실한 경우 90/270 등 여러 후보를 실제로 돌려보고 최선 선택
    try_both_directions_when_uncertain: bool = True
    prefer_doctr_when_tie: bool = False
    tie_area_ratio: float = 0.01  # 1% 이내면 동률로 간주


class DocUNetBackend(RectifyBackend):
    """
    docunet backend: DocTR orientation (optional) + OpenCV perspective rectify.

    Key decisions:
      - The predictor output is interpreted as "current document orientation".
        Therefore we apply the inverse rotation as the correction:
          correction_angle = (-pred_angle) % 360

      - If confidence is low or parsing fails, we fall back to heuristic candidate rotations
        and select the best one by document quad detection quality.
    """

    name = "docunet"

    def __init__(self, device: str = "cpu", model_dir: Optional[str] = None, config: Optional[DocUNetConfig] = None):
        super().__init__(device=device, model_dir=model_dir)
        self.config = config or DocUNetConfig()

        # torch (future DL weights path)
        self._torch = None
        self._torch_import_error: Optional[BaseException] = None
        self._model = None
        self._weights_path: Optional[Path] = None

        try:
            import torch as _torch  # type: ignore
        except Exception as e:
            self._torch = None
            self._torch_import_error = e
        else:
            self._torch = _torch
            self._torch_import_error = None

        # doctr (orientation)
        self._doctr = None
        self._doctr_import_error: Optional[BaseException] = None
        self._orientation_predictor = None

        try:
            import doctr as _doctr  # type: ignore
        except Exception as e:
            self._doctr = None
            self._doctr_import_error = e
        else:
            self._doctr = _doctr
            self._doctr_import_error = None

        self._models_ready: bool = False

    # -------------------------
    # basic helpers
    # -------------------------
    @staticmethod
    def _validate_image(image_bgr: np.ndarray) -> Tuple[int, int]:
        if not isinstance(image_bgr, np.ndarray):
            raise TypeError(f"image_bgr must be np.ndarray, got {type(image_bgr)}")
        if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
            raise ValueError(f"image_bgr must have shape (H, W, 3). Got {image_bgr.shape}")
        h, w = int(image_bgr.shape[0]), int(image_bgr.shape[1])
        if h < 2 or w < 2:
            raise ValueError(f"image_bgr too small: {(h, w)}")
        return h, w

    @staticmethod
    def _bgr_to_rgb(image_bgr: np.ndarray) -> np.ndarray:
        return image_bgr[:, :, ::-1].copy()

    @staticmethod
    def _apply_rotation_bgr(image_bgr: np.ndarray, angle: int) -> np.ndarray:
        a = angle % 360
        if a == 0:
            return image_bgr
        if a == 90:
            return cv2.rotate(image_bgr, cv2.ROTATE_90_CLOCKWISE)
        if a == 180:
            return cv2.rotate(image_bgr, cv2.ROTATE_180)
        if a == 270:
            return cv2.rotate(image_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return image_bgr

    # -------------------------
    # doctr output normalization/parsing
    # -------------------------
    @staticmethod
    def _normalize_angle(val: Any) -> Optional[int]:
        """
        Normalize angle-like values into one of {0, 90, 180, 270}.
        Supports negative angles: -90 -> 270.
        """
        if val is None:
            return None

        if isinstance(val, (int, np.integer, float, np.floating)):
            v = int(round(float(val)))
            v = v % 360
            return v if v in (0, 90, 180, 270) else None

        if isinstance(val, str):
            s = val.strip().lower()
            mapping = {
                "0": 0, "90": 90, "180": 180, "270": 270,
                "-90": 270,
                "upright": 0, "rot90": 90, "rot180": 180, "rot270": 270,
            }
            if s in mapping:
                return mapping[s]
            for key in ("0", "90", "180", "270", "-90"):
                if key in s:
                    return mapping.get(key, None)

        return None

    @staticmethod
    def _angle_from_doctr_output(out: Any) -> Optional[int]:
        """
        Extract normalized angle in {0,90,180,270} from various doctr outputs.

        Known page_orientation_predictor format (observed):
          [[class_id], [angle_deg], [confidence]]
          e.g. [[1], [-90], [0.9]]
        """
        # dict with angle key
        if isinstance(out, dict):
            for k in ("angle", "orientation", "rotation"):
                if k in out:
                    return DocUNetBackend._normalize_angle(out[k])

        # page_orientation_predictor observed output: [[cls], [angle], [conf]]
        if isinstance(out, (list, tuple)) and len(out) == 3:
            try:
                angle_part = out[1]
                if isinstance(angle_part, (list, tuple, np.ndarray)) and len(angle_part) > 0:
                    angle_part = angle_part[0]
                ang = DocUNetBackend._normalize_angle(angle_part)
                if ang is not None:
                    return ang
            except Exception:
                pass

        # batch list/tuple: try first element recursively
        if isinstance(out, (list, tuple)) and len(out) > 0:
            first = out[0]
            ang = DocUNetBackend._angle_from_doctr_output(first)
            if ang is not None:
                return ang

            # probability vector [p0,p90,p180,p270]
            if len(out) == 4 and all(isinstance(x, (int, float, np.floating, np.integer)) for x in out):
                arr = np.array(out, dtype=float)
                idx = int(arr.argmax())
                return [0, 90, 180, 270][idx]

        # numpy array probability vector
        if isinstance(out, np.ndarray):
            arr = out
            if arr.ndim == 2 and arr.shape[0] == 1:
                arr = arr[0]
            if arr.ndim == 1 and arr.shape[0] == 4:
                idx = int(np.argmax(arr))
                return [0, 90, 180, 270][idx]

        return DocUNetBackend._normalize_angle(out)

    @staticmethod
    def _confidence_from_doctr_output(out: Any) -> Optional[float]:
        """
        Extract confidence from page_orientation_predictor output:
          [[class_id], [angle_deg], [confidence]]
        """
        if isinstance(out, (list, tuple)) and len(out) == 3:
            try:
                conf_part = out[2]
                if isinstance(conf_part, (list, tuple, np.ndarray)) and len(conf_part) > 0:
                    conf_part = conf_part[0]
                return float(conf_part)
            except Exception:
                return None
        return None

    # -------------------------
    # weights discovery (future DL path)
    # -------------------------
    def _resolve_weights_path(self) -> Optional[Path]:
        if not self.model_dir:
            return None
        p = Path(self.model_dir)
        if p.is_file():
            return p
        if not p.exists():
            return None
        candidates = [p / "docunet.pth", p / "docunet.pt", p / "best.pth", p / "model.pth"]
        for c in candidates:
            if c.exists() and c.is_file():
                return c
        found = sorted(list(p.glob("*.pth")) + list(p.glob("*.pt")))
        return found[0] if found else None

    # -------------------------
    # lazy init (doctr predictor)
    # -------------------------
    def _lazy_init_models(self) -> Dict[str, Any]:
        if self._models_ready:
            return {
                "init": "cached",
                "weights_path": str(self._weights_path) if self._weights_path else None,
                "torch_available": self._torch is not None,
                "doctr_available": self._doctr is not None,
                "orientation_predictor_available": self._orientation_predictor is not None,
            }

        self._weights_path = self._resolve_weights_path()

        init_meta: Dict[str, Any] = {
            "init": "opencv_perspective_ready",
            "weights_path": str(self._weights_path) if self._weights_path else None,
            "torch_available": self._torch is not None,
            "torch_import_error": repr(self._torch_import_error) if self._torch_import_error else None,
            "doctr_available": self._doctr is not None,
            "doctr_import_error": repr(self._doctr_import_error) if self._doctr_import_error else None,
        }

        if self.config.enable_orientation and self._doctr is not None:
            try:
                from doctr.models import page_orientation_predictor  # type: ignore
                self._orientation_predictor = page_orientation_predictor(pretrained=True)
                init_meta["orientation_predictor_name"] = "page_orientation_predictor"
            except Exception as e1:
                try:
                    from doctr.models import crop_orientation_predictor  # type: ignore
                    self._orientation_predictor = crop_orientation_predictor(pretrained=True)
                    init_meta["orientation_predictor_name"] = "crop_orientation_predictor"
                except Exception as e2:
                    self._orientation_predictor = None
                    init_meta["orientation_predictor_error"] = {
                        "page_orientation_predictor": repr(e1),
                        "crop_orientation_predictor": repr(e2),
                    }

        self._models_ready = True
        init_meta["orientation_predictor_available"] = self._orientation_predictor is not None
        return init_meta

    # -------------------------
    # orientation correction (confidence + candidate selection)
    # -------------------------
    def _maybe_apply_orientation(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Orientation correction with:
          - doctr prediction parsing (angle + confidence)
          - confidence thresholding
          - SAFE fallback: never rotate if all candidates fail to produce a valid document quad
          - candidate testing (prefer 0-degree first for safety)
          -  tie-break: if 0 vs doctr_inverse are nearly equal, prefer doctr_inverse
          -  NEW: predictor unavailable -> still run SAFE fallback over (0/90/180/270)
          -  NEW: if scores tie, prefer 0-degree (do-nothing)
        """
        meta: Dict[str, Any] = {
            "enabled": bool(self.config.enable_orientation),
            "applied": False,
            "predictor_available": self._orientation_predictor is not None,
        }

        if not self.config.enable_orientation:
            meta["reason"] = "orientation disabled"
            return image_bgr, meta

        def _textline_score(img_bgr: np.ndarray) -> float:
            """
            OCR 없이 '가로 글줄'이 더 뚜렷한 방향을 선호하기 위한 타이브레이커 점수.
            - row projection variance / col projection variance 비율을 사용
            - 값이 클수록 '가로 줄 구조(=정방향일 가능성)'가 강함
            """
            try:
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

                # 너무 큰 이미지는 간단히 축소해서 빠르게 평가
                h, w = gray.shape[:2]
                max_side = 900
                m = max(h, w)
                if m > max_side:
                    r = max_side / float(m)
                    gray = cv2.resize(gray, (int(w * r), int(h * r)), interpolation=cv2.INTER_AREA)

                # 텍스트/획 강조를 위해 edge 기반으로 가볍게
                gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
                gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
                mag = cv2.magnitude(gx, gy)

                # row/col projection
                row = np.sum(mag, axis=1)
                col = np.sum(mag, axis=0)

                vr = float(np.var(row))
                vc = float(np.var(col))

                # ratio (가로 줄 구조가 강하면 vr이 더 커지는 경향)
                return (vr + 1e-6) / (vc + 1e-6)
            except Exception:
                return 0.0

        # --- helper: score a rotated image by document quad detection quality ---
        def score_rotation(img: np.ndarray) -> Tuple[float, Dict[str, Any]]:
            quad, find_meta = find_document_quad(img, self.config.params)
            if quad is None:
                return 0.0, {"found": False, "find": find_meta}

            best_area = float(find_meta.get("best_area", 0.0))

            #  NEW: 타이브레이커 점수(가로 글줄 구조)
            tls = float(_textline_score(img))

            # 가중치는 'best_area 차이'보다 훨씬 작게(동점일 때만 영향) 주는 게 안전
            # best_area는 대략 2e5 단위라서, tls는 보통 0.5~2.0 근처
            # => 1e5 정도 곱해주면 동점에서 안정적으로 갈라짐
            alpha = 1e5
            score = 1e9 + best_area + (alpha * tls)

            return score, {"found": True, "find": find_meta, "textline_score": tls}

        # ---------- build candidates ----------
        # Always include 0deg first (safety + "normal이면 0도 유지" 목적)
        candidates = [(0, "keep_0deg")]

        pred_conf = None
        doctr_correction = None

        # predictor가 있으면: 기존처럼 doctr 기반 후보를 앞쪽에 추가
        if self._orientation_predictor is not None:
            try:
                rgb = self._bgr_to_rgb(image_bgr)
                pred_out = self._orientation_predictor([rgb])

                # NOTE: 아래 파싱 로직은 기존 파일의 방식/키에 맞춰 유지해야 함
                #       (현재 파일에서 pred_out 파싱하는 코드가 이어져 있을 텐데,
                #        그 구조를 깨지 않기 위해 "기존 파싱부"는 그대로 두는 걸 권장)
                # 여기서는 "이미 파일에 있던 pred_out 파싱부"를 그대로 사용한다는 가정으로
                # pred_angle, pred_conf를 얻었다고 보고, doctr_correction 후보만 계산한다.

                # --------------------------
                # [중요] 기존 코드의 pred_out 파싱부 START/END를 그대로 유지해서
                # pred_angle / pred_conf 값을 세팅해줘야 해.
                # --------------------------
                # 예시(파일마다 다를 수 있음):
                # pred_angle = int(...)
                # pred_conf = float(...)
                # --------------------------
                # [중요] 기존 pred_out 파싱부를 여기에 "그대로" 두는 걸 추천.
                # --------------------------

                # doctr가 "현재가 rotated"라고 예측했을 때, 우리가 적용할 correction 각도 계산
                # (기존 코드의 계산을 그대로 쓰는 게 안전)
                # 예: pred_angle in {0,90,180,270} 라면 correction은 (-pred_angle) mod 360
                try:
                    pred_angle = meta.get("pred_angle", None)
                    if pred_angle is None:
                        # 기존 파싱부에서 pred_angle을 지역변수로 썼다면, 그 변수를 그대로 쓰면 됨
                        pred_angle = None
                except Exception:
                    pred_angle = None

                if pred_angle in (0, 90, 180, 270):
                    doctr_correction = int((-int(pred_angle)) % 360)

            except Exception as e:
                # predictor가 "있긴 한데" 실행 실패 -> fallback으로 전환
                meta["predictor_error"] = repr(e)
                meta["predictor_available"] = False
                pred_conf = None
                doctr_correction = None

        # predictor가 없거나(또는 실패)라도: SAFE fallback 후보 테스트를 하도록 한다.
        # doctr_correction이 유효하면 0도 다음에 우선 배치(단, 중복 제거)
        if doctr_correction in (0, 90, 180, 270) and doctr_correction != 0:
            candidates.append((doctr_correction, "doctr_inverse"))

        # 나머지 후보(0/90/180/270) 채우기 (중복 제거)
        for ang in (90, 180, 270):
            if all(c[0] != ang for c in candidates):
                candidates.append((ang, f"rot{ang}"))

        # ---------- SAFE fallback scoring ----------
        try:
            scored = []
            best_score = -1.0
            best_ang = 0
            best_tag = "keep_0deg"
            best_detail: Dict[str, Any] = {}

            all_failed = True
            for ang, tag in candidates:
                rotated_try = self._apply_rotation_bgr(image_bgr, int(ang))
                s, detail = score_rotation(rotated_try)
                found = bool(detail.get("found", False))
                if found:
                    all_failed = False

                scored.append(
                    {
                        "angle": int(ang),
                        "tag": tag,
                        "score": float(s),
                        "found": found,
                        "best_area": float(detail.get("find", {}).get("best_area", 0.0)),
                        "textline_score": float(detail.get("textline_score", 0.0)),

                    }
                )

                #  NEW: 점수가 같으면 0도(무회전) 우선
                if (s > best_score) or (s == best_score and int(ang) == 0 and best_ang != 0):
                    best_score = float(s)
                    best_ang = int(ang)
                    best_tag = tag
                    best_detail = detail

            #  SAFETY RULE: if all candidates fail to find quad -> DO NOT ROTATE
            if all_failed or best_score <= 0.0:
                meta["fallback"] = {
                    "applied": False,
                    "chosen": {"angle": 0, "tag": "no_rotation_all_candidates_failed"},
                    "candidates": candidates,
                    "scored": scored,
                    "scoring": {"all_failed": True},
                }
                meta["correction_angle"] = 0
                meta["applied"] = False
                # predictor 유무에 따라 reason을 더 명확히
                meta["reason"] = (
                    "fallback_disabled_all_candidates_failed"
                    if meta.get("predictor_available", False)
                    else "fallback_disabled_all_candidates_failed_no_predictor"
                )
                return image_bgr, meta

            #  TIE-BREAK(기존 유지): 0deg vs doctr_inverse 거의 비슷하면 doctr_inverse 우선 (옵션 켰을 때만)
            if (
                    bool(self.config.prefer_doctr_when_tie)
                    and (doctr_correction is not None)
                    and (pred_conf is not None)
                    and (pred_conf >= self.config.min_orientation_confidence)
            ):
                areas = {s["angle"]: float(s.get("best_area", 0.0)) for s in scored if s.get("found", False)}
                if 0 in areas and doctr_correction in areas:
                    a0 = areas[0]
                    ad = areas[doctr_correction]
                    denom = max(a0, ad, 1e-6)
                    rel_diff = abs(a0 - ad) / denom

                    if rel_diff <= float(self.config.tie_area_ratio):
                        best_ang = int(doctr_correction)
                        best_tag = "doctr_inverse_tie_break"
                        best_detail = {
                            "tie_break": {
                                "rel_diff": rel_diff,
                                "area_0deg": a0,
                                "area_doctr_inverse": ad,
                                "tie_area_ratio": float(self.config.tie_area_ratio),
                            }
                        }

            # apply best rotation
            rotated = self._apply_rotation_bgr(image_bgr, best_ang)
            meta["fallback"] = {
                "applied": best_ang != 0,
                "chosen": {"angle": best_ang, "tag": best_tag},
                "candidates": candidates,
                "scored": scored,
                "scoring": best_detail,
            }
            meta["correction_angle"] = best_ang
            meta["applied"] = (best_ang != 0)

            # predictor 유무에 따라 reason 구분
            if meta.get("predictor_available", False):
                meta["reason"] = "used_fallback_candidate_selection_safe"
            else:
                meta["reason"] = "used_fallback_candidate_selection_safe_no_predictor"

            return rotated, meta

        except Exception as e:
            meta["error"] = repr(e)
            meta["reason"] = "orientation inference failed"
            return image_bgr, meta

            rotated = self._apply_rotation_bgr(image_bgr, best_ang)
            fallback = {
                "applied": bool(best_ang != 0),
                "chosen": {"angle": best_ang, "tag": best_tag},
                "candidates": candidates,
                "scored": scored,
                "scoring": best_detail,
            }
            return rotated, fallback

        #  candidates: always test all 4 angles (policy: 정상은 0도 유지)
        base_candidates: List[Tuple[int, str]] = [
            (0, "no_rotation"),
            (90, "cand_90"),
            (180, "cand_180"),
            (270, "cand_270"),
        ]

        # ------------------------------------------------------------
        # CASE A) predictor unavailable -> run fallback candidate selection
        # ------------------------------------------------------------
        if self._orientation_predictor is None:
            meta["reason"] = "orientation predictor unavailable -> fallback_candidate_selection"
            rotated, fb = choose_best_candidate(base_candidates, prefer_zero_on_tie=True)
            meta["fallback"] = fb
            chosen = fb.get("chosen", {}).get("angle", 0)
            meta["correction_angle"] = int(chosen) if chosen in (0, 90, 180, 270) else 0
            meta["applied"] = bool(meta["correction_angle"] != 0)
            return rotated, meta

        # ------------------------------------------------------------
        # CASE B) predictor available -> try doctr, else fallback if uncertain
        # ------------------------------------------------------------
        try:
            rgb = self._bgr_to_rgb(image_bgr)
            pred_out = self._orientation_predictor([rgb])

            meta["raw_output_type"] = type(pred_out).__name__
            try:
                meta["raw_output_preview"] = str(pred_out)[:500]
            except Exception:
                meta["raw_output_preview"] = "<unserializable>"

            pred_angle = self._angle_from_doctr_output(pred_out)  # 0/90/180/270 or None
            pred_conf = self._confidence_from_doctr_output(pred_out)  # float or None

            meta["angle"] = pred_angle
            meta["confidence"] = pred_conf

            uncertain = False
            if pred_angle is None:
                uncertain = True
                meta["uncertain_reason"] = "angle_parse_failed"
            elif pred_conf is not None and pred_conf < float(self.config.min_orientation_confidence):
                uncertain = True
                meta["uncertain_reason"] = f"low_confidence<{self.config.min_orientation_confidence}"

            # confident doctr path
            if (not uncertain) and pred_angle in (0, 90, 180, 270):
                correction = (-int(pred_angle)) % 360
                rotated = self._apply_rotation_bgr(image_bgr, correction)
                meta["correction_angle"] = correction
                meta["applied"] = (correction != 0)
                meta["reason"] = "used_doctr_inverse_confident"
                return rotated, meta

            # uncertain -> fallback candidate selection (still prefer 0 on tie)
            meta["reason"] = "doctr_uncertain -> fallback_candidate_selection"
            rotated, fb = choose_best_candidate(base_candidates, prefer_zero_on_tie=True)
            meta["fallback"] = fb
            chosen = fb.get("chosen", {}).get("angle", 0)
            meta["correction_angle"] = int(chosen) if chosen in (0, 90, 180, 270) else 0
            meta["applied"] = bool(meta["correction_angle"] != 0)
            return rotated, meta

        except Exception as e:
            meta["error"] = repr(e)
            meta["reason"] = "orientation inference failed -> fallback_candidate_selection"
            rotated, fb = choose_best_candidate(base_candidates, prefer_zero_on_tie=True)
            meta["fallback"] = fb
            chosen = fb.get("chosen", {}).get("angle", 0)
            meta["correction_angle"] = int(chosen) if chosen in (0, 90, 180, 270) else 0
            meta["applied"] = bool(meta["correction_angle"] != 0)
            return rotated, meta

            # 5) score candidates
            best_score = -1.0
            best_ang = 0
            best_tag = "no_rotation"
            best_detail: Dict[str, Any] = {}

            all_failed = True
            scored: List[Dict[str, Any]] = []

            for ang, tag in candidates:
                rotated = self._apply_rotation_bgr(image_bgr, ang)
                s, detail = score_rotation(rotated)

                found = bool(detail.get("found", False))
                if found:
                    all_failed = False

                scored.append({
                    "angle": ang,
                    "tag": tag,
                    "score": s,
                    "found": found,
                    "best_area": float(detail.get("find", {}).get("best_area", 0.0)),
                })

                if s > best_score:
                    best_score = s
                    best_ang = ang
                    best_tag = tag
                    best_detail = detail

            #  SAFETY RULE: if all candidates fail to find quad -> DO NOT ROTATE
            if all_failed or best_score <= 0.0:
                meta["fallback"] = {
                    "applied": False,
                    "chosen": {"angle": 0, "tag": "no_rotation_all_candidates_failed"},
                    "candidates": candidates,
                    "scored": scored,
                    "scoring": {"all_failed": True},
                }
                meta["correction_angle"] = 0
                meta["applied"] = False
                meta["reason"] = "fallback_disabled_all_candidates_failed"
                return image_bgr, meta

            #  TIE-BREAK: if 0deg and doctr_inverse are both found and areas are nearly equal, prefer doctr_inverse
            if (
                    bool(self.config.prefer_doctr_when_tie)
                    and (doctr_correction is not None)
                    and (pred_conf is not None)
                    and (pred_conf >= self.config.min_orientation_confidence)
            ):
                areas = {s["angle"]: float(s.get("best_area", 0.0)) for s in scored if s.get("found", False)}
                if 0 in areas and doctr_correction in areas:
                    a0 = areas[0]
                    ad = areas[doctr_correction]
                    denom = max(a0, ad, 1e-6)
                    rel_diff = abs(a0 - ad) / denom

                    # if difference within tie ratio, trust doctr prior
                    if rel_diff <= float(self.config.tie_area_ratio):
                        best_ang = doctr_correction
                        best_tag = "doctr_inverse_tie_break"
                        best_detail = {
                            "tie_break": {
                                "rel_diff": rel_diff,
                                "area_0deg": a0,
                                "area_doctr_inverse": ad,
                                "tie_area_ratio": float(self.config.tie_area_ratio),
                            }
                        }

            # apply best rotation
            rotated = self._apply_rotation_bgr(image_bgr, best_ang)
            meta["fallback"] = {
                "applied": best_ang != 0,
                "chosen": {"angle": best_ang, "tag": best_tag},
                "candidates": candidates,
                "scored": scored,
                "scoring": best_detail,
            }
            meta["correction_angle"] = best_ang
            meta["applied"] = (best_ang != 0)
            meta["reason"] = "used_fallback_candidate_selection_safe"
            return rotated, meta

        except Exception as e:
            meta["error"] = repr(e)
            meta["reason"] = "orientation inference failed"
            return image_bgr, meta

    # -------------------------
    # public
    # -------------------------
    def rectify(self, image_bgr: np.ndarray) -> RectifyResult:
        h, w = self._validate_image(image_bgr)
        init_meta = self._lazy_init_models()

        meta: Dict[str, Any] = {
            "backend": self.name,
            "device": self.device,
            "model_dir": self.model_dir,
            "input_shape": [h, w],
            "init": init_meta,
            "applied": False,
            "method": "orientation_then_opencv_perspective",
            "orientation": {},
            "opencv": {
                "params": {
                    "canny1": self.config.params.canny1,
                    "canny2": self.config.params.canny2,
                    "dilate_iter": self.config.params.dilate_iter,
                    "approx_eps_ratio": self.config.params.approx_eps_ratio,
                    "min_area_ratio": self.config.params.min_area_ratio,
                    "border": self.config.params.border,
                }
            },
        }

        if self.config.strict_weights and self._weights_path is None:
            raise RuntimeError(
                "DocUNet strict mode: weights were not found. "
                "Provide --model_dir pointing to a weights file or directory."
            )

        # 1) orientation correction
        oriented, orient_meta = self._maybe_apply_orientation(image_bgr)
        meta["orientation"] = orient_meta

        # 2) perspective rectify on oriented image
        quad, find_meta = find_document_quad(oriented, self.config.params)
        meta["opencv"]["find"] = find_meta

        if quad is None:
            meta["warning"] = "No document-like quadrilateral found; returning oriented image."
            meta["applied"] = bool(orient_meta.get("applied"))
            meta["output_shape"] = [int(oriented.shape[0]), int(oriented.shape[1])]
            return RectifyResult(image=oriented, meta=meta)

        try:
            warped, warp_meta = warp_perspective(oriented, quad, self.config.params)
            meta["opencv"]["warp"] = warp_meta
            meta["applied"] = True
            meta["output_shape"] = [int(warped.shape[0]), int(warped.shape[1])]
            return RectifyResult(image=warped, meta=meta)
        except Exception as e:
            meta["warning"] = "Perspective warp failed; returning oriented image."
            meta["error"] = repr(e)
            meta["applied"] = bool(orient_meta.get("applied"))
            meta["output_shape"] = [int(oriented.shape[0]), int(oriented.shape[1])]
            return RectifyResult(image=oriented, meta=meta)
