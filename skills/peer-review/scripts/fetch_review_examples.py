#!/usr/bin/env python3
"""Fetch similar peer review examples from Semantic Scholar.

Searches for highly-cited review papers in the same field as the manuscript
to provide few-shot examples for the evaluator agent.

Usage:
    python scripts/fetch_review_examples.py --field "computer science" --keywords "NLP fairness"
    python scripts/fetch_review_examples.py --field "law" --keywords "criminal law plea bargaining" --limit 5

Output:
    JSON array of review examples to stdout.
"""

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SS_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,authors,year,venue,citationCount,abstract,tldr"
DELAY_SECONDS = 1.1


def search_semantic_scholar(query: str, limit: int = 20) -> list:
    """Search Semantic Scholar and return results."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": FIELDS,
    })
    url = f"{SS_BASE}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperSkills/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", [])
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Warning: Semantic Scholar query failed: {e}", file=sys.stderr)
        return []


def score_paper(paper: dict, field: str) -> float:
    """Score a paper by relevance to field and citation count."""
    citations = paper.get("citationCount", 0)
    title_lower = (paper.get("title") or "").lower()
    abstract_lower = (paper.get("abstract") or "").lower()
    field_lower = field.lower()

    # Relevance bonus for review-related keywords
    review_keywords = ["review", "evaluation", "assessment", "peer review", "criteria"]
    relevance = sum(1 for kw in review_keywords if kw in title_lower or kw in abstract_lower)

    # Field relevance
    field_relevance = 2 if field_lower in title_lower or field_lower in abstract_lower else 1

    return (relevance + field_relevance) * math.log(citations + 1)


def fetch_review_examples(field: str, keywords: str, limit: int = 5) -> list:
    """Fetch and rank review examples."""
    queries = [
        f'"{field}" peer review criteria',
        f'"{keywords}" review evaluation',
        f'"{field}" manuscript assessment quality',
    ]

    all_papers = []
    seen_ids = set()

    for query in queries:
        results = search_semantic_scholar(query, limit=20)
        for paper in results:
            pid = paper.get("paperId")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_papers.append(paper)
        time.sleep(DELAY_SECONDS)

    # Score and rank
    scored = [(score_paper(p, field), p) for p in all_papers]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Format top results
    examples = []
    for _, paper in scored[:limit]:
        authors = paper.get("authors", [])
        author_str = authors[0].get("name", "Unknown") if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."

        tldr = paper.get("tldr")
        summary = tldr.get("text", "") if isinstance(tldr, dict) else ""
        if not summary:
            abstract = paper.get("abstract") or ""
            summary = abstract[:300] + "..." if len(abstract) > 300 else abstract

        examples.append({
            "id": paper.get("paperId"),
            "title": paper.get("title"),
            "authors": author_str,
            "venue": paper.get("venue", "Unknown"),
            "year": paper.get("year"),
            "citations": paper.get("citationCount", 0),
            "summary": summary,
        })

    return examples


def main():
    parser = argparse.ArgumentParser(description="Fetch peer review examples from Semantic Scholar")
    parser.add_argument("--field", required=True, help="Primary discipline")
    parser.add_argument("--keywords", required=True, help="Manuscript keywords")
    parser.add_argument("--limit", type=int, default=5, help="Number of examples to return")
    args = parser.parse_args()

    examples = fetch_review_examples(args.field, args.keywords, args.limit)

    if not examples:
        print(json.dumps({"error": "No review examples found", "examples": []}))
        sys.exit(0)

    print(json.dumps(examples, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
