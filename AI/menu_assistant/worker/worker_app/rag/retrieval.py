from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

"""
retrieval.py

Design goals (current project policy):
- RAG focuses on menu-name matching only.
- CONFIRM (decide canonical menu) ONLY when EXACT match (including variants).
- Otherwise return raw_menu (if provided) or None, and let downstream LLM handle refinement.
- Chroma documents remain 'menu' only (A-plan). Variants are used as a lightweight post-filter
  (max jamo similarity + exact-on-variant).
"""

# ==============================
# CONFIG / ROUTING
# ==============================
COLLECTION_NAME = "menu_index"

BASE_DIR = Path(__file__).resolve().parents[3]  # .../menu_assistant/
DEFAULT_CHROMA_DIR = BASE_DIR / "data" / "chroma"
DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Runtime defaults (aligned to orchestrator/step_04 flags)
DEFAULT_TOP_K = 5
DEFAULT_SAVE_TOP_N = 2
DEFAULT_SCORE_THRESHOLD = 0.55

# Final score used for CLOSE vs NOT_FOUND gating (NOT for confirmation)
DEFAULT_FINAL_W_EMBED = 0.65
DEFAULT_FINAL_W_JAMO = 0.35
DEFAULT_FINAL_CLOSE_THRESHOLD = 0.80

# Hard cutoff requested previously: if best jamo < 0.5 => NOT_FOUND
JAMO_HARD_CUTOFF = 0.5

# Env overrides
ENV_CHROMA_DIR = "MENU_ASSISTANT_CHROMA_DIR"
ENV_COLLECTION = "MENU_ASSISTANT_COLLECTION"
ENV_EMBED_MODEL = "MENU_ASSISTANT_EMBED_MODEL"

_WS_RE = re.compile(r"\s+")


def _canon_status(status_raw: str) -> str:
    """Normalize detailed/raw statuses into a small canonical set.

    Canonical statuses used by downstream rules/UI:
      - exact
      - close
      - ambiguous
      - not_found

    Keep the original value in `status_raw` for debugging/analytics.
    """
    s = (status_raw or "").strip().lower()
    if "exact" in s:
        return "exact"
    if "close" in s:
        return "close"
    if "ambiguous" in s:
        return "ambiguous"
    if "not_found" in s:
        return "not_found"
    # Default to not_found to keep pipeline fail-open for LLM assist.
    return "not_found"


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
    """Best-effort CSV/list to list[str]."""
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
    """Chroma distance -> similarity in [0,1] for cosine distance (1 - distance)."""
    if distance is None:
        return 0.0
    try:
        d = float(distance)
    except Exception:
        return 0.0
    return 1.0 - d


def _parse_metadata(md: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "menu": _norm_space(str(md.get("menu", ""))),
        "variants": _split_csv(md.get("variants", "")),
        "ingredients_ko": _split_csv(md.get("ingredients_ko", "")),
        "alg_tags": _split_csv(md.get("alg_tags", "")),
        "source": _norm_space(str(md.get("source", ""))),
    }


# ==============================
# JAMO SIMILARITY (typo-robust)
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


def _hangul_to_jamo(s: str) -> str:
    out: List[str] = []
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


# ==============================
# DATA STRUCTURES
# ==============================
@dataclass
class Candidate:
    id: str
    embed_score: float
    menu: str
    ingredients_ko: List[str]
    alg_tags: List[str]
    source: str = ""
    variants: List[str] = field(default_factory=list)

    # Scoring outputs
    jamo_score: float = 0.0           # max jamo over [menu]+variants
    best_variant: Optional[str] = None
    final_score: float = 0.0          # w_embed*embed + w_jamo*jamo


# ==============================
# CHROMA RETRIEVER
# ==============================
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
            # Legacy fallback
            self._client = chromadb.Client(
                Settings(persist_directory=str(self.chroma_dir), anonymized_telemetry=False)
            )

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=emb_fn,
        )

        # Empty collection check (fail fast)
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
        for idx, md in enumerate(metadatas):
            try:
                cid = str(ids[idx]) if idx < len(ids) else f"idx_{idx}"
                dist = float(distances[idx]) if idx < len(distances) else None
                sim = _to_similarity(dist)

                meta = _parse_metadata(md or {})
                menu = meta["menu"]
                variants = meta["variants"]

                # best jamo over menu + variants
                best_variant = None
                best_j = jamo_similarity(q, menu) if menu else 0.0
                best_variant = menu if menu else None
                for v in (variants or []):
                    j = jamo_similarity(q, v)
                    if j > best_j:
                        best_j = j
                        best_variant = v

                out.append(
                    Candidate(
                        id=cid,
                        embed_score=float(sim),
                        menu=menu,
                        ingredients_ko=meta["ingredients_ko"],
                        alg_tags=meta["alg_tags"],
                        source=meta.get("source") or "",
                        variants=variants or [],
                        jamo_score=float(best_j),
                        best_variant=best_variant,
                    )
                )
            except Exception:
                continue

        return q, out, {"reason": "ok", "top_k": int(top_k), "count": len(out)}


_DEFAULT_RETRIEVER: Optional[ChromaMenuRetriever] = None


def get_retriever() -> ChromaMenuRetriever:
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        _DEFAULT_RETRIEVER = ChromaMenuRetriever()
    return _DEFAULT_RETRIEVER


# ==============================
# MATCH POLICY
# ==============================
def match_menu_norm(
    menu_norm: str,
    *,
    raw_menu: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
    save_top_n: int = DEFAULT_SAVE_TOP_N,
    embed_ambiguous: float = 0.90,  # NOTE: kept for CLI compatibility (currently unused by policy)
    jamo_threshold: float = 0.55,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    final_w_embed: float = DEFAULT_FINAL_W_EMBED,
    final_w_jamo: float = DEFAULT_FINAL_W_JAMO,
    final_close_threshold: float = DEFAULT_FINAL_CLOSE_THRESHOLD,
    include_debug: bool = False,
) -> Dict[str, Any]:
    """Menu-name-only matching."""
    retriever = get_retriever()
    used_query, cands, dbg = retriever.query(menu_norm=menu_norm, top_k=int(top_k))

    if not used_query:
        status_raw = "NOT_FOUND_EMPTY_QUERY"
        return {
            "status": _canon_status(status_raw),
            "status_raw": status_raw,
            "used_query": None,
            "decided_menu": raw_menu if raw_menu else None,
            "decision_method": "EMPTY_QUERY",
            "best_match": None,
            "candidates": [],
            "signals": {},
            "debug": dbg if include_debug else None,
        }

    if not cands:
        status_raw = "NOT_FOUND_NO_CANDIDATES"
        return {
            "status": _canon_status(status_raw),
            "status_raw": status_raw,
            "used_query": used_query,
            "decided_menu": raw_menu if raw_menu else None,
            "decision_method": "NO_CANDIDATES",
            "best_match": None,
            "candidates": [],
            "signals": {},
            "debug": dbg if include_debug else None,
        }

    # Recompute final_score with passed weights
    for c in cands:
        c.final_score = float(final_w_embed) * float(c.embed_score) + float(final_w_jamo) * float(c.jamo_score)
    cands.sort(key=lambda x: x.final_score, reverse=True)

    top1 = cands[0]                       # best final score
    top1_embed = max(cands, key=lambda x: x.embed_score)
    best_jamo = max(cands, key=lambda x: x.jamo_score)

    # Hard cutoff: if even best jamo is too low, treat as NOT_FOUND
    if float(best_jamo.jamo_score) < JAMO_HARD_CUTOFF:
        status_raw = "NOT_FOUND_BELOW_THRESHOLD"
        return {
            "status": _canon_status(status_raw),
            "status_raw": status_raw,
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
                "thresholds": {"jamo_hard_cutoff": float(JAMO_HARD_CUTOFF)},
            },
            "debug": dbg if include_debug else None,
        }

    qn = _norm_space(used_query)
    top1_menu_norm = _norm_space(top1.menu)
    variant_norms = {_norm_space(v) for v in ([top1.menu] + (top1.variants or []))}

    # Initialize gating booleans so debug is always safe
    embed_ok = True
    jamo_ok = True
    close_ok = True

    if qn and qn in variant_norms:
        status_raw = "EXACT"
        decided_menu = top1.menu
        decision_method = "EXACT_VARIANT_MATCH" if qn != top1_menu_norm else "EXACT"
    else:
        embed_ok = float(top1_embed.embed_score) >= float(score_threshold)
        jamo_ok = float(best_jamo.jamo_score) >= float(jamo_threshold)
        close_ok = float(top1.final_score) >= float(final_close_threshold)

        if embed_ok and jamo_ok and close_ok:
            status_raw = "CLOSE"
            decided_menu = raw_menu if raw_menu else None
            decision_method = "CLOSE_BY_FINAL_SCORE"
        else:
            status_raw = "NOT_FOUND_BELOW_THRESHOLD"
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
            "source": c.source,
            "best_variant": c.best_variant,
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
        "best_variant": top1.best_variant,
    }

    signals = {
        "top1_final_menu": top1.menu,
        "top1_final": float(top1.final_score),
        "top1_embed_menu": top1_embed.menu,
        "top1_embed": float(top1_embed.embed_score),
        "best_jamo_menu": best_jamo.menu,
        "best_jamo": float(best_jamo.jamo_score),
        "best_variant": top1.best_variant,
        "best_variant_jamo": float(top1.jamo_score),
        "thresholds": {
            "embed_min": float(score_threshold),
            "jamo_min": float(jamo_threshold),
            "final_close": float(final_close_threshold),
            "final_w_embed": float(final_w_embed),
            "final_w_jamo": float(final_w_jamo),
            "jamo_hard_cutoff": float(JAMO_HARD_CUTOFF),
        },
        "compat": {
            "embed_ambiguous": float(embed_ambiguous),  # accepted but not used
        },
    }

    debug_out = None
    if include_debug:
        debug_out = dict(dbg or {})
        debug_out.update(
            {
                "policy": "EXACT_ONLY_CONFIRM",
                "query_norm": qn,
                "top1_menu_norm": top1_menu_norm,
                "embed_ok": bool(embed_ok),
                "jamo_ok": bool(jamo_ok),
                "close_ok": bool(close_ok),
            }
        )

    return {
        "status": _canon_status(status_raw),
        "status_raw": status_raw,
        "used_query": used_query,
        "decided_menu": decided_menu,
        "decision_method": decision_method,
        "best_match": best_out,
        "candidates": cand_out,
        "signals": signals,
        "debug": debug_out,
    }
