from __future__ import annotations

import argparse
import re
from pathlib import Path


def chunks(paths: list[Path]) -> list[tuple[str, str]]:
    results = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, part in enumerate(re.split(r"\n\s*\n", text)):
            clean = part.strip()
            if clean:
                results.append((f"{path}:{i}", clean))
    return results


def retrieve(query: str, docs: list[tuple[str, str]], top_k: int) -> list[tuple[str, str, int]]:
    terms = {t.lower() for t in re.findall(r"[A-Za-z0-9_+-]+", query)}
    scored = []
    for ref, text in docs:
        hay = text.lower()
        score = sum(hay.count(term) for term in terms)
        if score:
            scored.append((ref, text, score))
    return sorted(scored, key=lambda x: x[2], reverse=True)[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--docs", nargs="+", default=["docs/paper_reproduction_notes.md", "docs/functional_group_classification_and_matching.md"])
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    docs = chunks([Path(p) for p in args.docs])
    for ref, text, score in retrieve(args.query, docs, args.top_k):
        print(f"[score={score}] {ref}\n{text}\n")


if __name__ == "__main__":
    main()

