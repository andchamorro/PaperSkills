#!/usr/bin/env python3
"""Find published abstracts similar to a manuscript via Semantic Scholar.

Searches for highly-cited papers in the same field and extracts their abstracts
to use as few-shot examples for abstract generation.

Usage:
    python scripts/find_similar_abstracts.py --field "computer science" --keywords "NLP fairness bias"
    python scripts/find_similar_abstracts.py --field "medicine" --keywords "oncology immunotherapy" --limit 5

Output:
    JSON array of abstract examples to stdout.
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
FIELDS = "title,authors,year,venue,citationCount,abstract"
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


def find_similar_abstracts(field: str, keywords: str, limit: int = 5) -> list:
    """Find and return similar published abstracts."""
    queries = [
        f"{field} {keywords}",
        keywords,
    ]

    all_papers = []
    seen_ids = set()

    for query in queries:
        results = search_semantic_scholar(query, limit=30)
        for paper in results:
            pid = paper.get("paperId")
            abstract = paper.get("abstract")
            # Only include papers that have abstracts
            if pid and pid not in seen_ids and abstract:
                seen_ids.add(pid)
                all_papers.append(paper)
        time.sleep(DELAY_SECONDS)

    # Score by citations and recency
    scored = []
    for paper in all_papers:
        citations = paper.get("citationCount", 0)
        year = paper.get("year", 2020)
        recency_bonus = max(0, (year - 2018) * 0.3)
        score = math.log(citations + 1) + recency_bonus
        scored.append((score, paper))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Format results
    examples = []
    for _, paper in scored[:limit]:
        authors = paper.get("authors", [])
        author_str = authors[0].get("name", "Unknown") if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."

        abstract = paper.get("abstract", "")
        word_count = len(abstract.split())

        examples.append({
            "id": paper.get("paperId"),
            "title": paper.get("title"),
            "authors": author_str,
            "venue": paper.get("venue", "Unknown"),
            "year": paper.get("year"),
            "citations": paper.get("citationCount", 0),
            "abstract": abstract,
            "word_count": word_count,
            "format": "structured" if any(
                kw in abstract.lower()
                for kw in ["background:", "objective:", "methods:", "results:", "conclusion:"]
            ) else "unstructured",
        })

    return examples


def main():
    parser = argparse.ArgumentParser(description="Find similar abstracts from Semantic Scholar")
    parser.add_argument("--field", required=True, help="Primary discipline")
    parser.add_argument("--keywords", required=True, help="Manuscript keywords")
    parser.add_argument("--limit", type=int, default=5, help="Number of examples to return")
    args = parser.parse_args()

    examples = find_similar_abstracts(args.field, args.keywords, args.limit)

    if not examples:
        print(json.dumps({"warning": "No similar abstracts found", "examples": []}))
        sys.exit(0)

    print(json.dumps(examples, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
