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
            out.append(cand)

        out.sort(key=lambda x: x.embed_score, reverse=True)
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
    top_k: int = DEFAULT_TOP_K,
    save_top_n: int = DEFAULT_SAVE_TOP_N,
    embed_ambiguous: float = DEFAULT_EMBED_AMBIGUOUS,
    embed_confirmed: float = DEFAULT_EMBED_CONFIRMED,
    jamo_threshold: float = DEFAULT_JAMO_THRESHOLD,
    jamo_confirmed: float = DEFAULT_JAMO_CONFIRMED,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    include_debug: bool = False,
) -> Dict[str, Any]:
    """Menu-only matching.

    Statuses (more granular):
      - EXACT: normalized exact match (menu_norm == top1.menu)
      - CONFIRMED_EMBED: top1 embed_score >= embed_confirmed (and not EXACT)
      - AMBIGUOUS_EMBED: top1 embed_score >= embed_ambiguous (and not EXACT/CONFIRMED_EMBED)
      - CONFIRMED_JAMO: best jamo among top_k >= jamo_confirmed (and not decided by EXACT/EMBED)
      - AMBIGUOUS_JAMO: best jamo among top_k >= jamo_threshold (and not decided by EXACT/EMBED)
      - NOT_FOUND_EMPTY_QUERY: empty menu_norm after normalization
      - NOT_FOUND_NO_CANDIDATES: chroma returned nothing
      - NOT_FOUND_BELOW_THRESHOLD: top1 embed_score < score_threshold and no jamo decision
    """

    retriever = get_retriever()
    used_query, cands, dbg = retriever.query(menu_norm=menu_norm, top_k=int(top_k))

    if not used_query:
        return {
            "status": "NOT_FOUND_EMPTY_QUERY",
            "used_query": None,
            "decided_menu": None,
            "best_match": None,
            "candidates": [],
            "debug": dbg if include_debug else None,
        }

    if not cands:
        return {
            "status": "NOT_FOUND_NO_CANDIDATES",
            "used_query": used_query,
            "decided_menu": None,
            "best_match": None,
            "candidates": [],
            "debug": dbg if include_debug else None,
        }

    top1 = cands[0]

    # Precompute best jamo among candidates
    best_j = max(cands, key=lambda x: x.jamo_score)

    # Decision policy (priority): EXACT > EMBED_CONFIRMED > EMBED_AMBIGUOUS > JAMO_CONFIRMED > JAMO_AMBIGUOUS > FAIL
    qn = _norm_space(used_query)
    tn = _norm_space(top1.menu)
    if qn and tn and qn == tn:
        status = "EXACT"
        decided = top1
        decision_method = "EXACT"
        reason = "exact_match"
    elif float(top1.embed_score) >= float(embed_confirmed):
        status = "CONFIRMED_EMBED"
        decided = top1
        decision_method = "EMBED"
        reason = "embed>=embed_confirmed"
    elif float(top1.embed_score) >= float(embed_ambiguous):
        status = "AMBIGUOUS_EMBED"
        decided = top1
        decision_method = "EMBED"
        reason = "embed>=embed_ambiguous"
    elif float(best_j.jamo_score) >= float(jamo_confirmed):
        status = "CONFIRMED_JAMO"
        decided = best_j
        decision_method = "JAMO"
        reason = "jamo>=jamo_confirmed"
    elif float(best_j.jamo_score) >= float(jamo_threshold):
        status = "AMBIGUOUS_JAMO"
        decided = best_j
        decision_method = "JAMO"
        reason = "jamo>=jamo_threshold"
    else:
        status = "NOT_FOUND_BELOW_THRESHOLD"
        decided = None
        decision_method = "NONE"
        reason = "no_decision"

    save_n = max(1, int(save_top_n))
    cand_out = [asdict(c) for c in cands[:save_n]]
    best_out = asdict(decided) if decided is not None else None

    debug_out = None
    if include_debug:
        debug_out = dict(dbg or {})
        best_j = max(cands, key=lambda x: x.jamo_score)
        debug_out.update(
            {
                "reason": reason,
                "thresholds": {
                    "embed_confirmed": float(embed_confirmed),
                    "embed_ambiguous": float(embed_ambiguous),
                    "jamo_confirmed": float(jamo_confirmed),
                    "jamo_threshold": float(jamo_threshold),
                    "score_threshold": float(score_threshold),
                },
                "top1": {
                    "menu": top1.menu,
                    "embed": float(top1.embed_score),
                    "jamo": float(top1.jamo_score),
                },
                "best_jamo": {
                    "menu": best_j.menu,
                    "embed": float(best_j.embed_score),
                    "jamo": float(best_j.jamo_score),
                },
                "saved_candidates": int(save_n),
            }
        )

    signals = {
        "top1_menu": top1.menu,
        "top1_embed": float(top1.embed_score),
        "best_jamo_menu": best_j.menu,
        "best_jamo_score": float(best_j.jamo_score),
        "thresholds": {
            "embed_confirmed": float(embed_confirmed),
            "embed_ambiguous": float(embed_ambiguous),
            "jamo_confirmed": float(jamo_confirmed),
            "jamo_ambiguous": float(jamo_threshold),
            "score_threshold": float(score_threshold),
        },
    }

    return {
        "status": status,
        "used_query": used_query,
        "decided_menu": (decided.menu if decided else None),
        "decision_method": decision_method,
        "best_match": best_out,
        "candidates": cand_out,
        "signals": signals,
        "debug": debug_out,
    }
