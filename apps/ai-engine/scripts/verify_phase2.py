"""Phase 2 verification — run on Postgres + pgvector.

    DATABASE_URL=postgresql+psycopg://... python -m scripts.verify_phase2

Seeds, embeds the catalog, and checks semantic retrieval. Real embedding models return
CLOSELY-RELATED axes (often several from the same domain), so correctness is judged by whether
the expected axis appears in the TOP-K (not strictly rank-1). The ranked hits are printed so you
can eyeball quality. Exit 0 = pass.
"""
from __future__ import annotations

import sys

from app.knowledge.db import IS_POSTGRES

TOP_K = 3


def main() -> int:
    if not IS_POSTGRES:
        print("SKIP: set DATABASE_URL to Postgres+pgvector and re-run.")
        return 0

    from scripts.seed_db import seed_all
    from scripts.embed_knowledge import embed_all
    from app.knowledge.retrieval import retrieve

    print("seed:", seed_all())
    print("embed:", embed_all())

    # expected axis should appear within the TOP-K hits (semantic neighbours are fine)
    cases = {
        "NF-kB cytokine CRP inflammation burden": "A1",
        "estrogen progesterone female hormone fibroid": "A31",
        "gut microbiome dysbiosis butyrate short chain fatty acids": "A17",
        "thyroid TSH T3 metabolism": "A33",
    }
    ok = True
    print(f"\nRetrieval check (expected axis must be in TOP-{TOP_K}):")
    for query, expect in cases.items():
        hits = retrieve(query, kind="axis", k=TOP_K)
        codes = [h["ref_code"] for h in hits]
        passed = expect in codes
        ok = ok and passed
        ranked = ", ".join(f"{h['ref_code']}({h['score']})" for h in hits)
        print(f"  [{'PASS' if passed else 'FAIL'}] want {expect:<4} in top{TOP_K} -> [{ranked}]")
    print("\nPHASE 2 RAG:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
