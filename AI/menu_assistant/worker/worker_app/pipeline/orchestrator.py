from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class Step5Options:
    user_profile_json: Optional[str] = None


class PipelineOrchestrator:
    """
    Menu pipeline orchestrator

     핵심
    - runs_root: 실행 산출물(run 폴더)이 떨어질 위치 (tmp여도 OK)
    - data_dir : chroma / datasets / resources 등 '정적 데이터'가 있는 위치
               반드시 PROJECT_ROOT/AI/menu_assistant/data 를 바라보게 해야 함
    """

    def __init__(self, runs_root: Path, data_dir: Path | None = None):
        self.runs_root = Path(runs_root).expanduser().resolve()
        self.runs_root.mkdir(parents=True, exist_ok=True)

        #  핵심: data_dir을 외부에서 주입 가능하게
        self.data_dir = Path(data_dir).expanduser().resolve() if data_dir else self.runs_root.parent

        # AI 루트(sys.path) 세팅 (프로젝트 구조에 맞게 조절 가능)
        # 보통: .../AI/menu_assistant/worker/worker_app/pipeline/orchestrator.py
        # self.ai_root -> .../AI
        self.ai_root = self.runs_root.parents[2] if len(self.runs_root.parents) >= 3 else Path.cwd()
        ai_root_str = str(self.ai_root)
        if ai_root_str not in sys.path:
            sys.path.insert(0, ai_root_str)

    def make_run_dir(self, run_id: str) -> Path:
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def run_cmd(
        self,
        cmd: list[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        subprocess 실행 헬퍼
        실패 시 stderr/stdout을 예외에 포함시켜 500 원인 바로 보이게 함
        """
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if p.returncode != 0:
            raise RuntimeError(
                "subprocess failed\n"
                f"cmd: {' '.join(cmd)}\n"
                f"cwd: {cwd}\n"
                f"stdout:\n{p.stdout}\n"
                f"stderr:\n{p.stderr}\n"
            )

    def run(
        self,
        *,
        image_path: Path,
        run_id: str,
        step5: Step5Options,
        run_step4: bool = True,
        run_step5: bool = True,
        run_step6: bool = True,
        do_check: bool = False,
    ) -> Path:
        """
        메뉴 파이프라인 실행
        - 여기서는 "각 step을 실행하는 커맨드/스크립트"를 너 프로젝트에 맞춰 연결해야 함
        - 중요한 건 data_dir이 올바르게 세팅되어야 step4(RAG)가 죽지 않음
        """
        image_path = Path(image_path).expanduser().resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"image not found: {image_path}")

        run_dir = self.make_run_dir(run_id)

        # 각 step 결과 디렉터리
        step4_dir = run_dir / "step4"
        final_dir = run_dir / "final"
        step4_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)

        #  공통 env: data_dir 주입 (너 step 스크립트들이 이 env를 읽어서 경로를 잡게 만드는 게 가장 안정적)
        env = {
            "MENU_DATA_DIR": str(self.data_dir),
            "RUN_DIR": str(run_dir),
            "IMAGE_PATH": str(image_path),
        }

        # --- Step4 (RAG/검색) ---
        if run_step4:
            # 예시: 너 프로젝트 step4 실행 스크립트/모듈에 맞게 cmd 구성
            # cmd = ["python", "-m", "AI.menu_assistant.worker.worker_app.pipeline.step4_rag", ...]
            cmd = ["python", "-m", "AI.menu_assistant.worker.worker_app.pipeline.step4_rag"]
            self.run_cmd(cmd, cwd=self.ai_root, env=env)

        # --- Step5 (정리/번역/결과 구성) ---
        if run_step5:
            cmd = ["python", "-m", "AI.menu_assistant.worker.worker_app.pipeline.step5_build"]
            # user_profile_json 등 옵션이 있으면 env로 넘기거나 args로 넘겨
            if step5.user_profile_json:
                env["USER_PROFILE_JSON"] = step5.user_profile_json
            self.run_cmd(cmd, cwd=self.ai_root, env=env)

        # --- Step6 (LLM 최종 요약/정제 등) ---
        if run_step6:
            cmd = ["python", "-m", "AI.menu_assistant.worker.worker_app.pipeline.step6_finalize"]
            self.run_cmd(cmd, cwd=self.ai_root, env=env)

        # 최종 파일 위치(너 기존 코드와 맞춰)
        # final_translated.json 또는 final.json을 만들어주도록 step5/6에서 저장하도록 구성해야 함
        final_translated = final_dir / "final_translated.json"
        final_json = final_dir / "final.json"

        # 혹시 step들이 final 파일을 안 만들면 여기서 실패 처리
        if not final_translated.exists() and not final_json.exists():
            raise FileNotFoundError(f"final output not found in {final_dir}")

        return run_dir


# from __future__ import annotations
#
# import os
# import sys
# import subprocess
# from dataclasses import dataclass
# from datetime import datetime
# from pathlib import Path
# from typing import Optional, List
# import json
# import time
#
#
# # ============================================================
# # Path routing (Docker-friendly)
# # ============================================================
#
# def _project_root() -> Path:
#     """
#     Resolve repository/project root robustly.
#     This file is: <root>/AI/menu_assistant/worker/worker_app/pipeline/orchestrator.py
#     So parents[4] => <root>/AI, parents[5] => <root>
#     """
#     here = Path(__file__).resolve()
#     # .../AI/menu_assistant/worker/worker_app/pipeline/orchestrator.py
#     # parents: [pipeline, worker_app, worker, menu_assistant, AI, <root>]
#     return here.parents[5]
#
#
# def _default_image_base() -> Path:
#     """
#     Default image base (no hard-coded Windows paths).
#     Priority:
#       1) ENV: MENU_ASSISTANT_IMAGE_BASE
#       2) <project_root>/AI/Upload_Images
#     """
#     env = os.environ.get("MENU_ASSISTANT_IMAGE_BASE")
#     if env:
#         return Path(env).expanduser().resolve()
#     return (_project_root() / "AI" / "Upload_Images").resolve()
#
#
# def _default_runs_root() -> Path:
#     """
#     Default runs root (no hard-coded Windows paths).
#     Priority:
#       1) ENV: MENU_ASSISTANT_RUNS_ROOT
#       2) <project_root>/AI/menu_assistant/data/runs
#     """
#     env = os.environ.get("MENU_ASSISTANT_RUNS_ROOT")
#     if env:
#         return Path(env).expanduser().resolve()
#     return (_project_root() / "AI" / "menu_assistant" / "data" / "runs").resolve()
#
#
# def _resolve_image_arg(image_arg: str, image_base: Path) -> Path:
#     """
#     Resolve --image argument into an absolute path.
#
#     Supported inputs:
#       - absolute path: returned as-is
#       - "Upload_Images/xxx.jpg": mapped under image_base/xxx.jpg
#       - "xxx.jpg": mapped under image_base/xxx.jpg
#       - other relative paths: resolved against current working directory
#         (but we still try image_base first to keep UX consistent)
#     """
#     p = Path(image_arg)
#
#     # Absolute path
#     if p.is_absolute():
#         return p
#
#     parts = p.parts
#     if parts and parts[0].lower() == "upload_images":
#         # Upload_Images/xxx.jpg -> <image_base>/xxx.jpg
#         tail = Path(*parts[1:]) if len(parts) > 1 else Path()
#         return (image_base / tail).resolve()
#
#     # Try <image_base>/<relative>
#     candidate = (image_base / p).resolve()
#     if candidate.exists():
#         return candidate
#
#     # Fallback: resolve relative to CWD
#     return p.resolve()
#
#
# # ============================================================
# # Utilities
# # ============================================================
#
# def make_run_id() -> str:
#     # runs/20260113_114232 형태
#     return datetime.now().strftime("%Y%m%d_%H%M%S")
#
#
# def run_cmd(cmd: List[str], env: Optional[dict] = None, cwd: Optional[Path] = None) -> None:
#     """Run a command and raise on failure."""
#     print("\n[RUN]", " ".join(cmd))
#     p = subprocess.run(cmd, shell=False, env=env, cwd=str(cwd) if cwd else None)
#     if p.returncode != 0:
#         raise RuntimeError(f"Command failed (exit={p.returncode}): {' '.join(cmd)}")
#
#
#
# def ensure_exists(path: Path, msg: str) -> None:
#     if not path.exists():
#         raise RuntimeError(f"{msg}: {path}")
#
#
# def _resolve_chroma_dir(data_dir: Path, chroma_dir_arg: Optional[str]) -> Path:
#     """Resolve the chroma persist directory deterministically.
#
#     Priority:
#       1) --chroma-dir CLI argument (if provided)
#       2) <data_dir>/chroma (if exists)
#       3) Windows known path fallback (only on Windows)
#
#     We intentionally do NOT create directories here; retrieval should fail fast if the path is wrong.
#     """
#     if chroma_dir_arg:
#         return Path(chroma_dir_arg).expanduser().resolve()
#
#     candidate = (data_dir / "chroma")
#     if candidate.exists():
#         return candidate.resolve()
#
#     # Optional Windows fallback for this project layout
#     if os.name == "nt":
#         win_fallback = Path(r"C:\\Users\\201\\Desktop\\PGHfolder\\haenet\\AI\\menu_assistant\\data\\chroma")
#         if win_fallback.exists():
#             return win_fallback
#
#     # Last resort: still return the standard location (will error later if missing)
#     return candidate
#
#
# # ============================================================
# # Orchestrator
# # ============================================================
#
# @dataclass
# class Step1Options:
#     backend: str = "auto"  # {none,doctr,dewarpnet,docunet,auto}
#     device: str = "cpu"
#     model_dir: Optional[str] = None
#     gamma: float = 1.15
#     clahe_clip: float = 2.0
#     shadow_strength: float = 0.85
#
#
# @dataclass
# class Step2Options:
#     # PaddleOCR / OCR options (pass-through)
#     lang: str = "korean"
#     det_limit_side_len: int = 4000
#     det_limit_type: str = "max"
#     use_doc_unwarping: bool = False
#     use_textline_orientation: bool = False
#     det_model_dir: Optional[str] = None
#     rec_model_dir: Optional[str] = None
#     cls_model_dir: Optional[str] = None
#     det_box_thresh: Optional[float] = None
#     det_thresh: Optional[float] = None
#     det_unclip_ratio: Optional[float] = None
#
#     use_preprocess: bool = False
#     preprocess_mode: Optional[str] = None
#
#     dump_raw: bool = False
#     out: Optional[str] = None
#     vis: Optional[str] = None
#
#
# @dataclass
# class Step3Options:
#     min_len: int = 2
#     line_y_tol: int = 20
#     merge_gap_px: int = 25
#     min_score: float = 0.0
#
#     # NEW: stabilized merge controls (pass2 is OFF by default)
#     aggressive_merge: bool = False
#     merge_gap_ratio: float = 0.75
#     pass2_gap_px: int = 14
#     pass2_gap_ratio: float = 0.45
#
#
# @dataclass
# class Step4Options:
#     # RAG match options (match step_04_rag_match.py)
#     top_k: int = 20
#     embed_ambiguous: float = 0.90
#     jamo_threshold: float = 0.55
#     score_threshold: float = 0.55
#     save_top_n: int = 2
#
#     # kept for compatibility only (step_04 accepts but does not use)
#     rerank_top_k: int = 5
#     use_rerank: bool = True
#
#     include_debug: bool = False
#
#     # Retrieval routing (stability)
#     chroma_dir: Optional[str] = None
#     collection: str = "menu_index"
#
#
# # orchestrator.py
#
# @dataclass
# class Step5Options:
#     # Step05 (LLM) options
#     user_profile_json: Optional[str] = None
#     include_debug: bool = False
#     max_retries: int = 2
#     require_poly: bool = True
#
#     #  NEW: orchestrator-level retry backoff (seconds)
#     sleep_base: float = 2.0
#
#
#
# #  NEW: Step6 options (Translate)
# @dataclass
# class Step6Options:
#     model: str = "gemini-2.5-flash"
#     api_key_env: str = "GEMINI_API_KEY"
#
#     temperature: float = 0.2
#     top_p: float = 0.95
#     top_k: int = 40
#
#     max_retries: int = 2
#     sleep_base: float = 0.7
#
#     # .env 로딩(선택) - client.py가 상위 탐색하지만 필요하면 강제 지정
#     dotenv_path: Optional[str] = None
#     max_dotenv_up: int = 8
#
#
# class PipelineOrchestrator:
#     def __init__(self, runs_root: Path):
#         self.runs_root = runs_root
#         self.data_dir = runs_root.parent
#         self.ai_root = runs_root.parents[2]  # .../AI
#
#         #  FastAPI 프로세스에서 menu_assistant import가 되도록 보장
#         ai_root_str = str(self.ai_root)
#         if ai_root_str not in sys.path:
#             sys.path.insert(0, ai_root_str)
#
#
#     def run(
#             self,
#             image_path: Path,
#             run_id: Optional[str] = None,
#             *,
#             step1: Optional[Step1Options] = None,
#             step2: Optional[Step2Options] = None,
#             step3: Optional[Step3Options] = None,
#             step4: Optional[Step4Options] = None,
#             step5: Optional[Step5Options] = None,
#             step6: Optional[Step6Options] = None,
#
#             run_step5: bool = True,
#             run_step6: bool = True,
#
#             do_check: bool = True,
#             check_keywords: Optional[List[str]] = None,
#             show_structured: bool = True,
#             run_step4: bool = True,
#     ) -> Path:
#         if not image_path.exists():
#             raise FileNotFoundError(f"Input image not found: {image_path}")
#
#         step1 = step1 or Step1Options()
#         step2 = step2 or Step2Options()
#         step3 = step3 or Step3Options()
#         step4 = step4 or Step4Options()
#         step5 = step5 or Step5Options()
#         step6 = step6 or Step6Options()
#
#         run_id = run_id or make_run_id()
#         run_dir = self.runs_root / run_id
#
#         rectify_img = run_dir / "rectify" / "rectified.jpg"
#         ocr_json = run_dir / "ocr" / "ocr.json"
#         normalize_json = run_dir / "normalize" / "normalize.json"
#         rag_match_json = run_dir / "rag_match" / "rag_match.json"
#
#         # ----------------------------------------------------
#         # Step 01: Rectify
#         # ----------------------------------------------------
#         cmd1 = [
#             sys.executable,
#             "-m",
#             "menu_assistant.worker.worker_app.pipeline.steps.step_01_rectify",
#             "--input",
#             str(image_path),
#             "--run_id",
#             run_id,
#             "--data_dir",
#             str(self.data_dir),
#             "--backend",
#             step1.backend,
#             "--device",
#             step1.device,
#             "--gamma",
#             str(step1.gamma),
#             "--clahe_clip",
#             str(step1.clahe_clip),
#             "--shadow_strength",
#             str(step1.shadow_strength),
#         ]
#         if step1.model_dir:
#             cmd1 += ["--model_dir", step1.model_dir]
#
#         run_cmd(cmd1, cwd=self.ai_root)
#
#         ensure_exists(rectify_img, "Step01 expected output missing (rectified image)")
#
#         # ----------------------------------------------------
#         # Step 02: OCR
#         # ----------------------------------------------------
#         cmd2 = [
#             sys.executable,
#             "-m",
#             "menu_assistant.worker.worker_app.pipeline.steps.step_02_ocr",
#             "--run_id",
#             run_id,
#             "--data_dir",
#             str(self.data_dir),
#             "--lang",
#             step2.lang,
#             "--det_limit_side_len",
#             str(step2.det_limit_side_len),
#             "--det_limit_type",
#             step2.det_limit_type,
#         ]
#
#         if step2.use_doc_unwarping:
#             cmd2 += ["--use_doc_unwarping"]
#         if step2.use_textline_orientation:
#             cmd2 += ["--use_textline_orientation"]
#         if step2.det_model_dir:
#             cmd2 += ["--det_model_dir", step2.det_model_dir]
#         if step2.rec_model_dir:
#             cmd2 += ["--rec_model_dir", step2.rec_model_dir]
#         if step2.cls_model_dir:
#             cmd2 += ["--cls_model_dir", step2.cls_model_dir]
#
#         if step2.use_preprocess:
#             cmd2 += ["--use_preprocess"]
#             if step2.preprocess_mode:
#                 cmd2 += ["--preprocess_mode", step2.preprocess_mode]
#
#         if step2.dump_raw:
#             cmd2 += ["--dump_raw"]
#
#         if step2.out:
#             cmd2 += ["--out", step2.out]
#         if step2.vis:
#             cmd2 += ["--vis", step2.vis]
#         # orchestrator.py (cmd2 구성 부분)
#         if step2.det_box_thresh is not None:
#             cmd2 += ["--det_box_thresh", str(step2.det_box_thresh)]
#         if step2.det_thresh is not None:
#             cmd2 += ["--det_thresh", str(step2.det_thresh)]
#         if step2.det_unclip_ratio is not None:
#             cmd2 += ["--det_unclip_ratio", str(step2.det_unclip_ratio)]
#
#         step2_env = os.environ.copy()
#         step2_env["FLAGS_use_mkldnn"] = "0"  # oneDNN(MKLDNN) off
#         step2_env["FLAGS_use_onednn"] = "0"  # 일부 버전에서 사용
#         step2_env["FLAGS_enable_pir_api"] = "0"  # PIR 경로 차단(버전별로 효과)
#         step2_env["FLAGS_enable_pir_in_executor"] = "0"
#
#         run_cmd(cmd2, env=step2_env, cwd=self.ai_root)
#
#         ocr_json_check = Path(step2.out) if step2.out else ocr_json
#         ensure_exists(ocr_json_check, "Step02 expected output missing (ocr json)")
#
#         # ----------------------------------------------------
#         # Step 03: Normalize
#         # ----------------------------------------------------
#         cmd3 = [
#             sys.executable,
#             "-m",
#             "menu_assistant.worker.worker_app.pipeline.steps.step_03_normalize",
#             "--runs-root",
#             str(self.runs_root),
#             "--run-id",
#             run_id,
#             "--min-len",
#             str(step3.min_len),
#             "--line-y-tol",
#             str(step3.line_y_tol),
#             "--merge-gap-px",
#             str(step3.merge_gap_px),
#             "--min-score",
#             str(step3.min_score),
#
#             # NEW: pass1 stabilization (always on)
#             "--merge-gap-ratio",
#             str(step3.merge_gap_ratio),
#         ]
#
#         # NEW: pass2 only when requested
#         if step3.aggressive_merge:
#             cmd3 += [
#                 "--enable-merge-pass2",
#                 "--pass2-gap-px",
#                 str(step3.pass2_gap_px),
#                 "--pass2-gap-ratio",
#                 str(step3.pass2_gap_ratio),
#             ]
#
#         run_cmd(cmd3, cwd=self.ai_root)
#
#         ensure_exists(normalize_json, "Step03 expected output missing (normalize json)")
#
#         # ----------------------------------------------------
#         # Optional: Step 03 Result Check
#         # ----------------------------------------------------
#         if do_check:
#             check_cmd = [
#                 sys.executable,
#                 "-m",
#                 "menu_assistant.worker.worker_app.utils.check_step_03_result",
#                 "--json",
#                 str(normalize_json),
#             ]
#             if show_structured:
#                 check_cmd += ["--show-structured"]
#             if check_keywords:
#                 check_cmd += ["--keywords"] + list(check_keywords)
#
#             run_cmd(check_cmd,cwd=self.ai_root)
#
#         # ----------------------------------------------------
#         # Step 04: RAG Match
#         # ----------------------------------------------------
#         if run_step4:
#             chroma_dir = _resolve_chroma_dir(self.data_dir, step4.chroma_dir)
#             step4_env = os.environ.copy()
#             step4_env["MENU_ASSISTANT_CHROMA_DIR"] = str(chroma_dir)
#             step4_env["MENU_ASSISTANT_COLLECTION"] = step4.collection
#
#             print("\n[RAG] using chroma_dir   =", step4_env["MENU_ASSISTANT_CHROMA_DIR"])
#             print("[RAG] using collection  =", step4_env["MENU_ASSISTANT_COLLECTION"])
#
#             cmd4 = [
#                 sys.executable,
#                 "-m",
#                 "menu_assistant.worker.worker_app.pipeline.steps.step_04_rag_match",
#                 "--run_id",
#                 run_id,
#                 "--data_dir",
#                 str(self.data_dir),
#
#                 "--top_k",
#                 str(step4.top_k),
#                 "--embed_ambiguous",
#                 str(step4.embed_ambiguous),
#                 "--jamo_threshold",
#                 str(step4.jamo_threshold),
#                 "--score_threshold",
#                 str(step4.score_threshold),
#                 "--save_top_n",
#                 str(step4.save_top_n),
#
#                 # (호환용: step_04는 받기만 함)
#                 "--rerank_top_k",
#                 str(step4.rerank_top_k),
#             ]
#
#             if step4.use_rerank:
#                 cmd4 += ["--use_rerank"]
#             else:
#                 cmd4 += ["--no_rerank"]
#
#             if step4.include_debug:
#                 cmd4 += ["--include_debug"]
#
#             run_cmd(cmd4, env=step4_env, cwd=self.ai_root)
#
#             ensure_exists(rag_match_json, "Step04 expected output missing (rag_match json)")
#
#         # ----------------------------------------------------
#         # Step 05: LLM Risk Score + Build final.json
#         # ----------------------------------------------------
#         final_json = run_dir / "final" / "final.json"
#
#         if run_step5:
#             cmd5 = [
#                 sys.executable, "-m",
#                 "menu_assistant.worker.worker_app.pipeline.steps.step_05_risk_score",
#                 "--run_id", run_id,
#                 "--data_dir", str(self.data_dir),
#                 "--max_retries", str(step5.max_retries),
#             ]
#             if step5.user_profile_json:
#                 cmd5 += ["--user_profile_json", step5.user_profile_json]
#             if step5.require_poly:
#                 cmd5 += ["--require_poly"]
#             else:
#                 cmd5 += ["--no_require_poly"]
#             if step5.include_debug:
#                 cmd5 += ["--include_debug"]
#
#             #  NEW: retry wrapper (keeps pipeline alive on transient 503/overload)
#             last_err: Optional[Exception] = None
#             for attempt in range(int(step5.max_retries) + 1):
#                 try:
#                     if attempt > 0:
#                         wait = float(step5.sleep_base) * (2 ** (attempt - 1))
#                         print(
#                             f"[STEP05] previous attempt failed. retrying in {wait:.1f}s... (attempt {attempt}/{step5.max_retries})")
#                         time.sleep(wait)
#
#                     run_cmd(cmd5, cwd=self.ai_root)
#                     last_err = None
#                     break
#
#                 except Exception as e:
#                     last_err = e
#                     # 다음 루프로 재시도. 마지막이면 raise.
#                     if attempt >= int(step5.max_retries):
#                         raise
#
#             # 이후 llm_input/llm_output 읽는 로직은 그대로
#
#             llm_input_path = run_dir / "llm" / "llm_input.json"
#             llm_output_path = run_dir / "llm" / "llm_output.json"
#
#             # llm_input.json 은 Step05가 항상 저장
#             ensure_exists(llm_input_path, "Step05 expected output missing (llm_input.json)")
#
#             llm_input_obj = json.loads(llm_input_path.read_text(encoding="utf-8"))
#             user_profile = llm_input_obj.get("user_profile") or {
#                 "allergy_tags": [],
#                 "avoid_foods": [],
#                 "religion": None,
#             }
#             llm_input_items = llm_input_obj.get("items") or []
#
#             #  핵심: items가 0개면 Step05가 llm_output.json을 만들지 않을 수 있음
#             if llm_output_path.exists():
#                 llm_output_obj = json.loads(llm_output_path.read_text(encoding="utf-8"))
#                 llm_output_items = llm_output_obj.get("items") or []
#             else:
#                 # Step05 로그: "No items to send to LLM." 케이스
#                 print("[STEP05] llm_output.json not found -> treating as empty output (no items).")
#                 llm_output_items = []
#
#             from menu_assistant.worker.worker_app.llm.services.finalizer import merge_llm_output_to_final
#
#             final_obj = merge_llm_output_to_final(
#                 run_id=run_id,
#                 user_profile=user_profile,
#                 llm_input_items=llm_input_items,
#                 llm_output_items=llm_output_items,
#             )
#
#             final_json.parent.mkdir(parents=True, exist_ok=True)
#             final_json.write_text(json.dumps(final_obj, ensure_ascii=False, indent=2), encoding="utf-8")
#             ensure_exists(final_json, "Step05 final output missing (final.json)")
#
#         # ----------------------------------------------------
#         #  Step 06: Translate (final.json -> final_translated.json)
#         # ----------------------------------------------------
#         final_translated_json = run_dir / "final" / "final_translated.json"
#         translate_json = run_dir / "translate" / "translate.json"
#
#         if run_step6:
#             ensure_exists(final_json, "Step06 requires Step05 output (final.json)")
#
#             cmd6 = [
#                 sys.executable,
#                 "-m",
#                 "menu_assistant.worker.worker_app.pipeline.steps.step_06_translate",
#                 "--run_id",
#                 run_id,
#                 "--data_dir",
#                 str(self.data_dir),
#
#                 "--model",
#                 step6.model,
#                 "--api_key_env",
#                 step6.api_key_env,
#                 "--temperature",
#                 str(step6.temperature),
#                 "--top_p",
#                 str(step6.top_p),
#                 "--top_k",
#                 str(step6.top_k),
#
#                 "--max_retries",
#                 str(step6.max_retries),
#                 "--sleep_base",
#                 str(step6.sleep_base),
#                 "--max_dotenv_up",
#                 str(step6.max_dotenv_up),
#             ]
#
#             if step6.dotenv_path:
#                 cmd6 += ["--dotenv_path", step6.dotenv_path]
#
#             run_cmd(cmd6, cwd=self.ai_root)
#
#             ensure_exists(translate_json, "Step06 expected output missing (translate.json)")
#             ensure_exists(final_translated_json, "Step06 expected output missing (final_translated.json)")
#
#         print("=== PIPELINE DONE (01~06) ===")
#         print(f"run_dir        : {run_dir}")
#         print(f"rectified.jpg  : {rectify_img}")
#         print(f"ocr.json       : {ocr_json_check}")
#         print(f"normalize.json : {normalize_json}")
#         if run_step4:
#             print(f"rag_match.json : {rag_match_json}")
#         if run_step5:
#             print(f"final.json     : {final_json}")
#         if run_step6:
#             print(f"translate.json : {translate_json}")
#             print(f"final_translated.json : {final_translated_json}")
#
#         return run_dir
#
#
# # ============================================================
# # CLI
# # ============================================================
# if __name__ == "__main__":
#     import argparse
#
#     p = argparse.ArgumentParser(description="Pipeline Orchestrator: step_01 -> step_02 -> step_03 -> step_04")
#
#     p.add_argument("--image", required=True, help="Input image path")
#     p.add_argument("--runs-root", default=str(_default_runs_root()), help="Runs root directory")
#     p.add_argument("--run-id", default=None, help="Optional run id. If omitted, auto-generated.")
#
#     # ---------------- Step1 passthrough ----------------
#     p.add_argument("--backend", default="auto", choices=["none", "doctr", "dewarpnet", "docunet", "auto"])
#     p.add_argument("--device", default="cpu")
#     p.add_argument("--model-dir", default="menu_assistant/worker/worker_app/vision/metrics/DewarpNet_master")
#     p.add_argument("--gamma", type=float, default=1.0)
#     p.add_argument("--clahe-clip", type=float, default=2.0)
#     p.add_argument("--shadow-strength", type=float, default=0.0)
#
#     # ---------------- Step2 passthrough ----------------
#     p.add_argument("--lang", default="korean")
#     p.add_argument("--det-limit-side-len", type=int, default=4000)
#     p.add_argument("--det-limit-type", default="max")
#     p.add_argument("--use-doc-unwarping", action="store_true")
#     p.add_argument("--use-textline-orientation", action="store_true")
#     p.add_argument("--det-model-dir", default=None)
#     p.add_argument("--rec-model-dir", default=None)
#     p.add_argument("--cls-model-dir", default=None)
#
#     p.add_argument("--det-box-thresh", type=float, default=0.5)
#     p.add_argument("--det-thresh", type=float, default=0.30)
#     p.add_argument("--det-unclip-ratio", type=float, default=2.0)
#
#     p.add_argument("--use-preprocess", action="store_true")
#     p.add_argument("--preprocess-mode", default=None)
#
#     p.add_argument("--dump-raw", action="store_true")
#     p.add_argument("--ocr-out", default=None, help="Override step2 --out path (default: <run>/ocr/ocr.json)")
#     p.add_argument("--ocr-vis", default=None, help="Override step2 --vis path (default: <run>/ocr/ocr_vis.jpg)")
#
#     # ---------------- Step3 passthrough ----------------
#     p.add_argument("--min-len", type=int, default=2)
#     p.add_argument("--line-y-tol", type=int, default=20)
#     p.add_argument("--merge-gap-px", type=int, default=25)
#     p.add_argument("--min-score", type=float, default=0.0)
#     p.add_argument("--aggressive-merge", action="store_true", help="Enable Step3 merge pass2 (more aggressive).")
#
#     # ---------------- Step4 passthrough ----------------
#     p.add_argument("--run-step4", action="store_true", help="Run step4 (default: on)")
#     p.add_argument("--no-step4", action="store_true", help="Skip step4")
#
#     p.add_argument("--top-k", type=int, default=5)
#     p.add_argument("--embed-ambiguous", type=float, default=0.90)
#     p.add_argument("--jamo-threshold", type=float, default=0.55)
#     p.add_argument("--score-threshold", type=float, default=0.55)
#     p.add_argument("--save-top-n", type=int, default=2)
#
#     # (호환용) Step4는 받기만 함
#     p.add_argument("--rerank-top-k", type=int, default=5)
#     p.add_argument("--use-rerank", action="store_true")
#     p.add_argument("--no-rerank", action="store_true")
#     p.add_argument("--rag-debug", action="store_true")
#
#     # ---------------- Step5 passthrough ----------------
#     p.add_argument("--run-step5", action="store_true", help="Run step5 (default: on)")
#     p.add_argument("--no-step5", action="store_true", help="Skip step5")
#     p.add_argument("--user-profile-json", default=None, help="Path to user profile JSON for step5")
#     p.add_argument("--step5-debug", action="store_true", help="Enable step5 debug outputs")
#     p.add_argument("--step5-max-retries", type=int, default=2)
#     p.add_argument("--step5-no-require-poly", action="store_true", help="Do not require poly (debug only)")
#
#     #  hard-fix routing (stability)
#     p.add_argument(
#         "--chroma-dir",
#         default=None,
#         help="Chroma persist directory. If omitted, uses <data_dir>/chroma or Windows fallback.",
#     )
#     p.add_argument("--collection", default="menu_index", help="Chroma collection name (default: menu_index)")
#
#     # ----------------  Step6 passthrough ----------------
#     p.add_argument("--run-step6", action="store_true", help="Run step6 (default: on)")
#     p.add_argument("--no-step6", action="store_true", help="Skip step6")
#
#     p.add_argument("--step6-model", default="gemini-2.5-flash")
#     p.add_argument("--step6-api-key-env", default="GEMINI_API_KEY")
#     p.add_argument("--step6-temperature", type=float, default=0.2)
#     p.add_argument("--step6-top-p", type=float, default=0.95)
#     p.add_argument("--step6-top-k", type=int, default=40)
#     p.add_argument("--step6-max-retries", type=int, default=2)
#     p.add_argument("--step6-sleep-base", type=float, default=0.7)
#     p.add_argument("--step6-dotenv-path", default=None, help="Explicit .env path (optional)")
#     p.add_argument("--step6-max-dotenv-up", type=int, default=8)
#
#     # ---------------- Check options ----------------
#     p.add_argument("--no-check", action="store_true", help="Skip step_03 result check")
#     p.add_argument("--check-keywords", nargs="*", default=None)
#     p.add_argument("--no-structured", action="store_true", help="Do not print structured fields in checker")
#
#     args = p.parse_args()
#
#     # ------------------------------------------------------------
#     # Resolve image path (Docker-friendly)
#     # ------------------------------------------------------------
#     image_base = _default_image_base()
#     resolved_image = _resolve_image_arg(args.image, image_base)
#     args.image = str(resolved_image)
#
#     args.runs_root = str(Path(args.runs_root).expanduser().resolve())
#
#     orch = PipelineOrchestrator(Path(args.runs_root))
#
#     step1 = Step1Options(
#         backend=args.backend,
#         device=args.device,
#         model_dir=args.model_dir,
#         gamma=args.gamma,
#         clahe_clip=args.clahe_clip,
#         shadow_strength=args.shadow_strength,
#     )
#
#     step2 = Step2Options(
#         lang=args.lang,
#         det_limit_side_len=args.det_limit_side_len,
#         det_limit_type=args.det_limit_type,
#         use_doc_unwarping=args.use_doc_unwarping,
#         use_textline_orientation=args.use_textline_orientation,
#         det_model_dir=args.det_model_dir,
#         rec_model_dir=args.rec_model_dir,
#         cls_model_dir=args.cls_model_dir,
#         use_preprocess=args.use_preprocess,
#         preprocess_mode=args.preprocess_mode,
#         dump_raw=args.dump_raw,
#         out=args.ocr_out,
#         vis=args.ocr_vis,
#         det_box_thresh=args.det_box_thresh,
#         det_thresh=args.det_thresh,
#         det_unclip_ratio=args.det_unclip_ratio,
#     )
#
#     step3 = Step3Options(
#         min_len=args.min_len,
#         line_y_tol=args.line_y_tol,
#         merge_gap_px=args.merge_gap_px,
#         min_score=args.min_score,
#
#         # NEW
#         aggressive_merge=args.aggressive_merge,
#         merge_gap_ratio=0.75,
#         pass2_gap_px=14,
#         pass2_gap_ratio=0.45,
#     )
#
#     use_rerank = True
#     if args.no_rerank:
#         use_rerank = False
#     if args.use_rerank:
#         use_rerank = True
#
#     step4 = Step4Options(
#         top_k=args.top_k,
#         embed_ambiguous=args.embed_ambiguous,
#         jamo_threshold=args.jamo_threshold,
#         score_threshold=args.score_threshold,
#         save_top_n=args.save_top_n,
#
#         rerank_top_k=args.rerank_top_k,
#         use_rerank=use_rerank,
#
#         include_debug=args.rag_debug,
#         chroma_dir=args.chroma_dir,
#         collection=args.collection,
#     )
#
#     run_step4 = True
#     if args.no_step4:
#         run_step4 = False
#     if args.run_step4:
#         run_step4 = True
#
#     step5 = Step5Options(
#         user_profile_json=args.user_profile_json,
#         include_debug=args.step5_debug,
#         max_retries=args.step5_max_retries,
#         require_poly=(not args.step5_no_require_poly),
#     )
#
#     run_step5 = True
#     if args.no_step5:
#         run_step5 = False
#     if args.run_step5:
#         run_step5 = True
#
#     #  Step6 wiring
#     step6 = Step6Options(
#         model=args.step6_model,
#         api_key_env=args.step6_api_key_env,
#         temperature=args.step6_temperature,
#         top_p=args.step6_top_p,
#         top_k=args.step6_top_k,
#         max_retries=args.step6_max_retries,
#         sleep_base=args.step6_sleep_base,
#         dotenv_path=args.step6_dotenv_path,
#         max_dotenv_up=args.step6_max_dotenv_up,
#     )
#
#     run_step6 = True
#     if args.no_step6:
#         run_step6 = False
#     if args.run_step6:
#         run_step6 = True
#
#     orch.run(
#         image_path=Path(args.image),
#         run_id=args.run_id,
#         step1=step1,
#         step2=step2,
#         step3=step3,
#         step4=step4,
#         step5=step5,
#         step6=step6,
#         do_check=(not args.no_check),
#         check_keywords=args.check_keywords,
#         show_structured=(not args.no_structured),
#         run_step4=run_step4,
#         run_step5=run_step5,
#         run_step6=run_step6,
#     )
