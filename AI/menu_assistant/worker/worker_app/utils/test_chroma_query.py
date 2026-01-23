from pathlib import Path
import argparse

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


def get_client(chroma_dir: Path):
    # 버전 호환: PersistentClient 우선
    if hasattr(chromadb, "PersistentClient"):
        return chromadb.PersistentClient(path=str(chroma_dir))
    return chromadb.Client(Settings(persist_directory=str(chroma_dir), anonymized_telemetry=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chroma_dir",
        default=r"C:\Users\201\Desktop\PGHfolder\Final_project\AI\menu_assistant\data\chroma",
        help="Chroma persist directory",
    )
    parser.add_argument("--collection", default="menu_index")
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument(
        "--model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Embedding model (must match build)",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="Query text (repeatable). Example: --query 대구탕 --query 냉모밀",
    )
    args = parser.parse_args()

    chroma_dir = Path(args.chroma_dir)
    print(f"[CHROMA_DIR] {chroma_dir}")
    print(f"[COLLECTION] {args.collection}")
    print(f"[EMBED_MODEL] {args.model}")
    print("-" * 80)

    if not chroma_dir.exists():
        print("[ERROR] chroma_dir does not exist. Did you build the index?")
        return

    client = get_client(chroma_dir)

    # embedding function (index build와 동일해야 함)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=args.model)

    col = client.get_or_create_collection(name=args.collection, embedding_function=emb_fn)

    # 1) count 확인
    try:
        cnt = col.count()
    except Exception:
        got = col.get(limit=5, include=["metadatas"])
        cnt = len(got.get("ids", []))

    print(f"[COUNT] {cnt}")
    if cnt == 0:
        print("[DIAG] Collection is empty. Build did not persist into this directory/collection.")
        print("       Re-run build_chroma_index.py and ensure it writes to THIS chroma_dir.")
        return

    # 2) 샘플 확인
    sample = col.get(limit=3, include=["metadatas"])
    metas = sample.get("metadatas") or []
    print("[SAMPLE] ids:", sample.get("ids"))
    print("[SAMPLE] menus:", [m.get("menu") for m in metas])
    print("-" * 80)

    # 3) 쿼리 기본값(아무것도 안 주면 테스트용)
    queries = args.query or ["만두", "대구탕", "메밀전병", "칼국수"]
    print(f"[QUERIES] {queries}")
    print("-" * 80)

    for q in queries:
        raw = col.query(
            query_texts=[q],
            n_results=args.top_k,
            include=["metadatas", "distances"],  # ⚠ ids는 include에 넣지 않음(버전 호환)
        )

        ids = (raw.get("ids") or [[]])[0]
        dists = (raw.get("distances") or [[]])[0]
        mds = (raw.get("metadatas") or [[]])[0]

        print(f"QUERY: '{q}'")
        if not ids:
            print("  -> NO RESULTS")
            print()
            continue

        for i, (_id, dist, md) in enumerate(zip(ids, dists, mds), start=1):
            # cosine distance 가정: similarity = 1 - dist
            sim = 1.0 - float(dist) if dist is not None else 0.0
            menu = (md or {}).get("menu", "")
            print(f"  {i}. id={_id} | sim={sim:.3f} | menu={menu}")

        print()

    print("[OK] query test finished.")


if __name__ == "__main__":
    main()

#python menu_assistant/worker/worker_app/utils/test_chroma_query.py