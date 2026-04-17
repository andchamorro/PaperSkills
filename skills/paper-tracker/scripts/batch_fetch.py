#!/usr/bin/env python3
"""Batch fetch paper metadata with async concurrency control.

Uses asyncio.Semaphore to limit concurrent API requests (PapervizAgent pattern
from paperviz_processor.py:185-240). Fetches metadata from OpenAlex, with
Semantic Scholar and CrossRef as fallbacks.

Usage:
    python scripts/batch_fetch.py --input papers.json --max-concurrent 10
    python scripts/batch_fetch.py --input papers.json --max-concurrent 5 --output enriched.json

Input JSON format:
    [{"doi": "10.1234/...", "title": "..."}, ...]

Output:
    JSON array with enriched metadata to stdout (or --output file).
"""

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


OA_BASE = "https://api.openalex.org"
SS_BASE = "https://api.semanticscholar.org/graph/v1/paper"
MAILTO = "paperskills@example.com"


def fetch_url_sync(url: str, timeout: int = 15) -> dict | None:
    """Synchronous URL fetch with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperSkills/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


async def fetch_paper_metadata(
    paper: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Fetch metadata for a single paper with semaphore control.

    Tries OpenAlex first, falls back to Semantic Scholar, then CrossRef.
    """
    async with semaphore:
        doi = paper.get("doi", "")
        title = paper.get("title", "")
        result = {**paper, "enriched": False, "source": None}

        # Try OpenAlex by DOI
        if doi:
            url = f"{OA_BASE}/works/https://doi.org/{urllib.parse.quote(doi, safe='')}?mailto={MAILTO}"
            data = await asyncio.to_thread(fetch_url_sync, url)
            if data and "title" in data:
                result.update({
                    "enriched": True,
                    "source": "openalex",
                    "title": data.get("display_name") or title,
                    "authors": [
                        a.get("author", {}).get("display_name", "")
                        for a in data.get("authorships", [])[:5]
                    ],
                    "publication_date": data.get("publication_date"),
                    "venue": (data.get("primary_location") or {}).get("source", {}).get("display_name"),
                    "citation_count": data.get("cited_by_count", 0),
                    "is_oa": data.get("open_access", {}).get("is_oa", False),
                    "abstract": data.get("abstract") or paper.get("abstract"),
                    "openalex_id": data.get("id"),
                })
                return result

        # Fallback: Semantic Scholar by DOI or title
        if doi:
            ss_url = f"{SS_BASE}/DOI:{urllib.parse.quote(doi, safe='')}?fields=title,authors,year,venue,citationCount,abstract"
        elif title:
            ss_url = f"{SS_BASE}/search?query={urllib.parse.quote(title)}&limit=1&fields=title,authors,year,venue,citationCount,abstract"
        else:
            return result

        data = await asyncio.to_thread(fetch_url_sync, ss_url)
        if data:
            # Handle search response vs direct lookup
            if "data" in data and data["data"]:
                data = data["data"][0]

            if "title" in data:
                authors = data.get("authors", [])
                result.update({
                    "enriched": True,
                    "source": "semantic_scholar",
                    "title": data.get("title") or title,
                    "authors": [a.get("name", "") for a in authors[:5]],
                    "year": data.get("year"),
                    "venue": data.get("venue"),
                    "citation_count": data.get("citationCount", 0),
                    "abstract": data.get("abstract") or paper.get("abstract"),
                })
                return result

        # Last resort: CrossRef by DOI
        if doi:
            cr_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
            data = await asyncio.to_thread(fetch_url_sync, cr_url)
            if data and "message" in data:
                msg = data["message"]
                result.update({
                    "enriched": True,
                    "source": "crossref",
                    "title": msg.get("title", [title])[0] if msg.get("title") else title,
                    "authors": [
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in msg.get("author", [])[:5]
                    ],
                    "venue": msg.get("container-title", [""])[0] if msg.get("container-title") else None,
                    "citation_count": msg.get("is-referenced-by-count", 0),
                })
                return result

        return result


async def batch_fetch(
    papers: list[dict],
    max_concurrent: int = 10,
) -> list[dict]:
    """Batch fetch metadata for multiple papers with concurrency control.

    Uses asyncio.Semaphore to limit concurrent API requests, following the
    PapervizAgent pattern (paperviz_processor.py:194-198).
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [
        asyncio.create_task(fetch_paper_metadata(paper, semaphore))
        for paper in papers
    ]

    results = []
    for future in asyncio.as_completed(tasks):
        result = await future
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch fetch paper metadata with concurrency control")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--max-concurrent", type=int, default=10, help="Max concurrent API requests")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            papers = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

    if not isinstance(papers, list):
        print(json.dumps({"error": "Input must be a JSON array"}), file=sys.stderr)
        sys.exit(1)

    results = asyncio.run(batch_fetch(papers, args.max_concurrent))

    enriched_count = sum(1 for r in results if r.get("enriched"))
    summary = {
        "total": len(results),
        "enriched": enriched_count,
        "failed": len(results) - enriched_count,
        "papers": results,
    }

    output = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(results)} papers to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
