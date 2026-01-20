# menu_assistant/worker/worker_app/rag/retrieval.py
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
DEFAULT_EMBED_AMBIGUOUS = 0.90          # 90% 이상이면 ambiguous
DEFAULT_JAMO_THRESHOLD = 0.85           # 오타 허용 결정 임계치(운영에서 조정)
DEFAULT_SCORE_THRESHOLD = 0.55          # 완전 실패 컷(필요 시)
DEFAULT_SAVE_TOP_N = 2                  # json 저장 시 후보 상위 N개만 (원하면 1로)

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
    # 인덱스 메타 키는 build에서 유지되어야 함
    return {
        "menu": _norm_space(str(md.get("menu", ""))),
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
    jamo_score: float = 0.0  # query vs menu


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
    embed_ambiguous: float = DEFAULT_EMBED_AMBIGUOUS,
    jamo_threshold: float = DEFAULT_JAMO_THRESHOLD,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    save_top_n: int = DEFAULT_SAVE_TOP_N,
    include_debug: bool = False,
) -> Dict[str, Any]:
    """
    결정 규칙:
    1) exact(menu_norm == top1.menu) -> EXACT
    2) else if top1.embed_score >= 0.90 -> AMBIGUOUS
    3) else if max_jamo(top_k) >= jamo_threshold -> AMBIGUOUS (menu는 jamo 최고 후보로 결정)
    4) else if top1.embed_score < score_threshold -> NOT_FOUND
    """
    retriever = get_retriever()
    used_query, cands, dbg = retriever.query(menu_norm=menu_norm, top_k=int(top_k))

    if not cands:
        return {
            "status": "NOT_FOUND",
            "used_query": None,
            "decided_menu": None,
            "best_match": None,
            "candidates": [],
            "debug": dbg if include_debug else None,
        }

    top1 = cands[0]
    q = used_query

    # exact 판단: "menu_norm vs menu"만 비교
    if _norm_space(q) and _norm_space(q) == _norm_space(top1.menu):
        status = "EXACT"
        decided = top1
        reason = "exact_match"
    else:
        # jamo 최고 후보
        best_j = max(cands, key=lambda x: x.jamo_score)
        if float(top1.embed_score) >= float(embed_ambiguous):
            status = "AMBIGUOUS"
            decided = top1
            reason = "embed>=0.90"
        elif float(best_j.jamo_score) >= float(jamo_threshold):
            status = "AMBIGUOUS"
            decided = best_j
            reason = "jamo_threshold"
        elif float(top1.embed_score) < float(score_threshold):
            status = "NOT_FOUND"
            decided = None
            reason = "below_score_threshold"
        else:
            status = "AMBIGUOUS"
            decided = top1
            reason = "fallback_top1"

    # candidates 저장 (상위 N개만)
    save_n = max(1, int(save_top_n))
    cand_out = [asdict(c) for c in cands[:save_n]]

    best_out = asdict(decided) if decided is not None else None

    debug_out = None
    if include_debug:
        debug_out = dict(dbg or {})
        debug_out.update(
            {
                "reason": reason,
                "embed_ambiguous": float(embed_ambiguous),
                "jamo_threshold": float(jamo_threshold),
                "score_threshold": float(score_threshold),
                "top1_embed": float(top1.embed_score),
                "top1_menu": top1.menu,
                "top1_jamo": float(top1.jamo_score),
                "best_jamo_menu": max(cands, key=lambda x: x.jamo_score).menu,
                "best_jamo_score": float(max(cands, key=lambda x: x.jamo_score).jamo_score),
            }
        )

    return {
        "status": status,
        "used_query": used_query,
        "decided_menu": (decided.menu if decided else None),
        "best_match": best_out,
        "candidates": cand_out,
        "debug": debug_out,
    }
