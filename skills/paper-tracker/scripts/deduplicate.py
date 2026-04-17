#!/usr/bin/env python3
"""Deduplicate a JSON array of paper objects by DOI or fuzzy title match.

Usage:
    cat papers.json | python deduplicate.py [--threshold 0.8]

Input:  JSON array on stdin. Each object should have at least "title" and
        optionally "doi".
Output: JSON array of deduplicated papers on stdout.
Errors: Descriptive messages on stderr.
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher


def normalize_doi(doi: str) -> str:
    """Normalize a DOI to lowercase, stripping common URL prefixes."""
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def normalize_title(title: str) -> str:
    """Lowercase and strip punctuation/whitespace for comparison."""
    if not title:
        return ""
    title = title.strip().lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def titles_match(a: str, b: str, threshold: float) -> bool:
    """Return True if two titles exceed the similarity threshold."""
    norm_a = normalize_title(a)
    norm_b = normalize_title(b)
    if not norm_a or not norm_b:
        return False
    return SequenceMatcher(None, norm_a, norm_b).ratio() >= threshold


def deduplicate(papers: list, threshold: float) -> list:
    """Deduplicate papers by DOI first, then fuzzy title matching."""
    seen_dois: dict[str, int] = {}
    unique: list = []

    # Pass 1: deduplicate by DOI
    for paper in papers:
        doi = normalize_doi(paper.get("doi", "") or "")
        if doi:
            if doi in seen_dois:
                continue
            seen_dois[doi] = len(unique)
        unique.append(paper)

    # Pass 2: fuzzy title matching among papers that survived Pass 1
    final: list = []
    used: set[int] = set()

    for i, paper in enumerate(unique):
        if i in used:
            continue
        title_i = paper.get("title", "") or ""
        for j in range(i + 1, len(unique)):
            if j in used:
                continue
            title_j = unique[j].get("title", "") or ""
            if titles_match(title_i, title_j, threshold):
                used.add(j)
        final.append(paper)

    return final


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deduplicate papers by DOI or fuzzy title matching.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Title similarity threshold (0.0-1.0, default: 0.8).",
    )
    args = parser.parse_args()

    if args.threshold < 0.0 or args.threshold > 1.0:
        print(
            "ERROR: --threshold must be between 0.0 and 1.0.",
            file=sys.stderr,
        )
        sys.exit(1)

    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No input received on stdin.", file=sys.stderr)
        sys.exit(1)

    try:
        papers = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON on stdin: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(papers, list):
        print(
            "ERROR: Expected a JSON array of paper objects.",
            file=sys.stderr,
        )
        sys.exit(1)

    result = deduplicate(papers, args.threshold)

    removed = len(papers) - len(result)
    print(
        f"INFO: {len(papers)} papers in, {len(result)} unique, {removed} duplicates removed.",
        file=sys.stderr,
    )

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
