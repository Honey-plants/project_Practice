from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# ==============================
# CONFIG
# ==============================
COLLECTION_NAME = "menu_index"

BASE_DIR = Path(__file__).resolve().parents[3]  # menu_assistant/
DEFAULT_CHROMA_DIR = BASE_DIR / "data" / "chroma"
DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DEFAULT_TOP_K = 5
DEFAULT_SAVE_TOP_N = 2


# Decision thresholds (menu-only embedding)
#
# We keep the existing CLI contract:
#   - embed_ambiguous: lower bound for EMBED-based decision
#   - jamo_threshold: lower bound for JAMO-based decision
# and add confirmed tiers with separate defaults.
DEFAULT_EMBED_CONFIRMED = 0.95      # >= 0.95 => CONFIRMED_EMBED
DEFAULT_EMBED_AMBIGUOUS = 0.90      # >= 0.90 => AMBIGUOUS_EMBED

DEFAULT_JAMO_CONFIRMED = 0.95       # >= 0.95 => CONFIRMED_JAMO
DEFAULT_JAMO_AMBIGUOUS = 0.85       # >= 0.85 => AMBIGUOUS_JAMO

# Backward-compatible alias (older CLI param name)
DEFAULT_JAMO_THRESHOLD = DEFAULT_JAMO_AMBIGUOUS

DEFAULT_SCORE_THRESHOLD = 0.55      # < threshold => NOT_FOUND_BELOW_THRESHOLD
# Final score (for CLOSE vs NOT_FOUND)
DEFAULT_FINAL_W_EMBED = 0.65
DEFAULT_FINAL_W_JAMO = 0.35
DEFAULT_FINAL_CLOSE_THRESHOLD = 0.80

# Env overrides
ENV_CHROMA_DIR = "MENU_ASSISTANT_CHROMA_DIR"
ENV_COLLECTION = "MENU_ASSISTANT_COLLECTION"
ENV_EMBED_MODEL = "MENU_ASSISTANT_EMBED_MODEL"

_WS_RE = re.compile(r"\s+")


def _get_env_path(name: str) -> Optional[Path]:
    v = os.environ.get(name)
    if not v:
        return None
    try:
        return Path(v).expanduser().resolve()
    except Exception:
        return Path(v)


def _norm_space(s: str) -> str:
    s = (s or "").strip()
    return _WS_RE.sub(" ", s)


def _split_csv(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple, set)):
        out: List[str] = []
        for x in v:
            xs = _norm_space(str(x))
            if xs:
                out.append(xs)
        return out
    parts = [p.strip() for p in str(v).split(",")]
    return [p for p in parts if p]


def _to_similarity(distance: Optional[float]) -> float:
    if distance is None:
        return 0.0
    try:
        d = float(distance)
    except Exception:
        return 0.0
    return 1.0 - d


def _parse_metadata(md: Dict[str, Any]) -> Dict[str, Any]:
    # The build script should store these metadata keys.
    return {
        "menu": _norm_space(str(md.get("menu", ""))),
        "ingredients_ko": _split_csv(md.get("ingredients_ko", "")),
        "alg_tags": _split_csv(md.get("alg_tags", "")),
        "source": _norm_space(str(md.get("source", ""))),
    }


# ==============================
# JAMO SIMILARITY (typo robust)
# ==============================
_SBASE = 0xAC00
_LBASE = 0x1100
_VBASE = 0x1161
_TBASE = 0x11A7
_LCOUNT = 19
_VCOUNT = 21
_TCOUNT = 28
_NCOUNT = _VCOUNT * _TCOUNT
_SCOUNT = _LCOUNT * _NCOUNT
# retrieval.py 상단 (CONFIG 영역 근처)
JAMO_HARD_CUTOFF = 0.5


def _hangul_to_jamo(s: str) -> str:
    out = []
    for ch in s:
        code = ord(ch)
        if _SBASE <= code < (_SBASE + _SCOUNT):
            sindex = code - _SBASE
            l = _LBASE + (sindex // _NCOUNT)
            v = _VBASE + ((sindex % _NCOUNT) // _TCOUNT)
            t = _TBASE + (sindex % _TCOUNT)
            out.append(chr(l))
            out.append(chr(v))
            if t != _TBASE:
                out.append(chr(t))
        else:
            out.append(ch)
    return "".join(out)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            ins = cur[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(ins, dele, sub))
        prev = cur
    return prev[-1]


def jamo_similarity(a: str, b: str) -> float:
    a = _norm_space(a)
    b = _norm_space(b)
    if not a or not b:
        return 0.0
    ja = _hangul_to_jamo(a)
    jb = _hangul_to_jamo(b)
    dist = _levenshtein(ja, jb)
    denom = max(len(ja), len(jb), 1)
    return float(max(0.0, 1.0 - (dist / denom)))


@dataclass
class Candidate:
    id: str
    embed_score: float
    menu: str
    ingredients_ko: List[str]
    alg_tags: List[str]
    source: str = ""
    jamo_score: float = 0.0
    final_score: float = 0.0



class ChromaMenuRetriever:
    def __init__(
        self,
        chroma_dir: Path = DEFAULT_CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
        embed_model: str = DEFAULT_EMBED_MODEL,
    ):
        self.chroma_dir = _get_env_path(ENV_CHROMA_DIR) or Path(chroma_dir)
        self.collection_name = os.environ.get(ENV_COLLECTION) or collection_name
        self.embed_model = os.environ.get(ENV_EMBED_MODEL) or embed_model
        self._collection = None
        self._client = None

    def _init(self) -> None:
        if self._collection is not None:
            return
        if not self.chroma_dir.exists():
            raise RuntimeError(f"[RAG] chroma_dir does not exist: {self.chroma_dir}")

        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.embed_model)

        if hasattr(chromadb, "PersistentClient"):
            self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
        else:
            self._client = chromadb.Client(
                Settings(persist_directory=str(self.chroma_dir), anonymized_telemetry=False)
            )

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=emb_fn,
        )

        # Empty collection check
        try:
            cnt = self._collection.count()
        except Exception:
            got = self._collection.get(limit=1, include=["metadatas"])
            cnt = len(got.get("ids", []))
        if cnt == 0:
            raise RuntimeError(
                f"[RAG] collection is empty. chroma_dir={self.chroma_dir} collection={self.collection_name}"
            )

    @property
    def collection(self):
        self._init()
        return self._collection

    def query(self, menu_norm: str, top_k: int) -> Tuple[str, List[Candidate], Dict[str, Any]]:
        q = _norm_space(menu_norm)
        if not q:
            return q, [], {"reason": "empty_query"}

        raw = self.collection.query(
            query_texts=[q],
            n_results=int(top_k),
            include=["metadatas", "distances"],
        )

        ids = (raw.get("ids") or [[]])[0] if isinstance(raw.get("ids"), list) else []
        metadatas = (raw.get("metadatas") or [[]])[0] if isinstance(raw.get("metadatas"), list) else []
        distances = (raw.get("distances") or [[]])[0] if isinstance(raw.get("distances"), list) else []

        if not ids:
            ids = [f"idx_{i}" for i in range(len(metadatas))]

        out: List[Candidate] = []
        for _id, md, dist in zip(ids, metadatas, distances):
            meta = _parse_metadata(md or {})
            cand = Candidate(
                id=str(_id),
                embed_score=float(_to_similarity(dist)),
                menu=str(meta.get("menu", "")),
                ingredients_ko=meta.get("ingredients_ko") or [],
                alg_tags=meta.get("alg_tags") or [],
                source=str(meta.get("source", "")),
            )
            cand.jamo_score = jamo_similarity(q, cand.menu)
            # final_score는 match 단계에서 가중치/임계값을 바꿀 수 있으므로 기본 계산은 0으로 두고,
            # 여기서는 "기본 가중치"로만 채워둔다(디버그/정렬용).
            cand.final_score = (
                    DEFAULT_FINAL_W_EMBED * float(cand.embed_score)
                    + DEFAULT_FINAL_W_JAMO * float(cand.jamo_score)
            )
            out.append(cand)

        out.sort(key=lambda x: x.final_score, reverse=True)
        return q, out, {"mode": "embed", "top_k": int(top_k)}


_DEFAULT_RETRIEVER: Optional[ChromaMenuRetriever] = None


def get_retriever() -> ChromaMenuRetriever:
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        _DEFAULT_RETRIEVER = ChromaMenuRetriever()
    return _DEFAULT_RETRIEVER


def match_menu_norm(
    menu_norm: str,
    *,
    raw_menu: Optional[str] = None,  # NEW: step_04에서 넘기면 EXACT가 아닐 때 raw 반환 가능
    top_k: int = DEFAULT_TOP_K,
    save_top_n: int = DEFAULT_SAVE_TOP_N,
    embed_ambiguous: float = DEFAULT_EMBED_AMBIGUOUS,   # 하한(게이팅) 용도로만 사용
    jamo_threshold: float = DEFAULT_JAMO_THRESHOLD,     # 하한(게이팅) 용도로만 사용
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,   # embed 최소 하한
    final_w_embed: float = DEFAULT_FINAL_W_EMBED,       # NEW
    final_w_jamo: float = DEFAULT_FINAL_W_JAMO,         # NEW
    final_close_threshold: float = DEFAULT_FINAL_CLOSE_THRESHOLD,  # NEW
    include_debug: bool = False,
) -> Dict[str, Any]:
    """Menu-name-only matching.

    Policy:
      - EXACT: only when normalized query == normalized canonical menu name
      - CLOSE: candidates exist and pass gating + final_score >= close threshold
      - NOT_FOUND: otherwise

    Return:
      - decided_menu:
          * EXACT: canonical menu
          * else: raw_menu (if provided), otherwise None  (backward compatible)
    """

    retriever = get_retriever()
    used_query, cands, dbg = retriever.query(menu_norm=menu_norm, top_k=int(top_k))

    if not used_query:
        return {
            "status": "NOT_FOUND_EMPTY_QUERY",
            "used_query": None,
            "decided_menu": raw_menu if raw_menu else None,
            "decision_method": "EMPTY_QUERY",
            "best_match": None,
            "candidates": [],
            "signals": {},
            "debug": dbg if include_debug else None,
        }

    if not cands:
        return {
            "status": "NOT_FOUND_NO_CANDIDATES",
            "used_query": used_query,
            "decided_menu": raw_menu if raw_menu else None,
            "decision_method": "NO_CANDIDATES",
            "best_match": None,
            "candidates": [],
            "signals": {},
            "debug": dbg if include_debug else None,
        }

    # Recompute final_score with passed weights (caller can tune without rebuilding)
    for c in cands:
        c.final_score = float(final_w_embed) * float(c.embed_score) + float(final_w_jamo) * float(c.jamo_score)

    # sort by final_score desc (robust "close" scoring)
    cands.sort(key=lambda x: x.final_score, reverse=True)

    # Best by embed (top1) and best by jamo (for hard cutoff and signals)
    top1_embed = max(cands, key=lambda x: x.embed_score)
    best_jamo = max(cands, key=lambda x: x.jamo_score)
    top1 = cands[0]  # best final_score

    # >>> HARD CUTOFF: jamo < 0.5 => NOT_FOUND (사용자 요구) <<<
    if float(best_jamo.jamo_score) < JAMO_HARD_CUTOFF:
        return {
            "status": "NOT_FOUND_BELOW_THRESHOLD",
            "used_query": used_query,
            "decided_menu": raw_menu if raw_menu else None,
            "decision_method": "JAMO_HARD_CUTOFF",
            "best_match": None,
            "candidates": [
                {
                    "id": c.id,
                    "menu": c.menu,
                    "embed_score": float(c.embed_score),
                    "jamo_score": float(c.jamo_score),
                    "final_score": float(c.final_score),
                }
                for c in cands[: max(1, int(save_top_n))]
            ],
            "signals": {
                "best_jamo_menu": best_jamo.menu,
                "best_jamo_score": float(best_jamo.jamo_score),
                "thresholds": {
                    "jamo_hard_cutoff": float(JAMO_HARD_CUTOFF),
                },
            },
            "debug": dbg if include_debug else None,
        }

    # EXACT 판단: 정규화된 used_query == 정규화된 canonical menu
    qn = _norm_space(used_query)
    tn = _norm_space(top1.menu)

    if qn and tn and qn == tn:
        status = "EXACT"
        decided_menu = top1.menu
        decision_method = "EXACT"
    else:
        # Gating: embed/jamo 하한 + final close threshold
        # - embed 하한은 top1_embed 기준으로 체크 (임베딩 품질 하한)
        # - jamo_threshold는 best_jamo 기준으로 체크 (문자/오타 견고성 하한)
        # - close는 top1(final) 기준으로 체크
        embed_ok = float(top1_embed.embed_score) >= float(score_threshold)
        jamo_ok = float(best_jamo.jamo_score) >= float(jamo_threshold)
        close_ok = float(top1.final_score) >= float(final_close_threshold)

        if embed_ok and jamo_ok and close_ok:
            status = "CLOSE"
            decided_menu = raw_menu if raw_menu else None  # 확정 금지, raw 반환(옵션)
            decision_method = "CLOSE_BY_FINAL_SCORE"
        else:
            status = "NOT_FOUND_BELOW_THRESHOLD"
            decided_menu = raw_menu if raw_menu else None
            decision_method = "GATED_OUT"

    save_n = max(1, int(save_top_n))
    cand_out = [
        {
            "id": c.id,
            "menu": c.menu,
            "embed_score": float(c.embed_score),
            "jamo_score": float(c.jamo_score),
            "final_score": float(c.final_score),
            "ingredients_ko": c.ingredients_ko,
            "alg_tags": c.alg_tags,
            "source": c.source,
        }
        for c in cands[:save_n]
    ]

    best_out = {
        "id": top1.id,
        "menu": top1.menu,
        "embed_score": float(top1.embed_score),
        "jamo_score": float(top1.jamo_score),
        "final_score": float(top1.final_score),
        "ingredients_ko": top1.ingredients_ko,
        "alg_tags": top1.alg_tags,
        "source": top1.source,
    }

    signals = {
        "top1_final_menu": top1.menu,
        "top1_final": float(top1.final_score),
        "top1_embed_menu": top1_embed.menu,
        "top1_embed": float(top1_embed.embed_score),
        "best_jamo_menu": best_jamo.menu,
        "best_jamo": float(best_jamo.jamo_score),
        "thresholds": {
            "embed_min": float(score_threshold),
            "jamo_min": float(jamo_threshold),
            "final_close": float(final_close_threshold),
            "final_w_embed": float(final_w_embed),
            "final_w_jamo": float(final_w_jamo),
            "jamo_hard_cutoff": float(JAMO_HARD_CUTOFF),
        },
    }

    debug_out = None
    if include_debug:
        debug_out = dict(dbg or {})
        debug_out.update(
            {
                "policy": "EXACT_ONLY_CONFIRM",
                "embed_ok": embed_ok if qn != tn else True,
                "jamo_ok": jamo_ok if qn != tn else True,
                "close_ok": close_ok if qn != tn else True,
                "query_norm": qn,
                "top1_norm": tn,
            }
        )

    return {
        "status": status,
        "used_query": used_query,
        "decided_menu": decided_menu,
        "decision_method": decision_method,
        "best_match": best_out,
        "candidates": cand_out,
        "signals": signals,
        "debug": debug_out,
    }
