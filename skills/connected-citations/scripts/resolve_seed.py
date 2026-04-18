#!/usr/bin/env python3
"""Resolve a DOI or paper title to Semantic Scholar paper metadata.

Usage:
    python scripts/resolve_seed.py --doi "10.1038/s41586-023-06221-2"
    python scripts/resolve_seed.py --title "Attention is All You Need"
    python scripts/resolve_seed.py --help

Output: JSON object on stdout with {paperId, title, authors, year, citationCount}.
Errors: Descriptive messages on stderr; exits with code 1 on failure.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "paperId,title,authors,year,citationCount,externalIds"
REQUEST_INTERVAL = 1.0  # seconds between requests (rate limiting)
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0


def _make_request(url: str, retries: int = MAX_RETRIES) -> dict:
    """Make an HTTP GET request with retry and exponential backoff.

    Returns parsed JSON on success. Prints descriptive errors to stderr
    and exits on unrecoverable failure.
    """
    wait = REQUEST_INTERVAL
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "citation-network-skill/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                print(
                    f"[resolve_seed] Rate limited (attempt {attempt}/{retries}). "
                    f"Waiting {wait:.0f}s...",
                    file=sys.stderr,
                )
                time.sleep(wait)
                wait *= BACKOFF_FACTOR
                continue
            elif exc.code == 404:
                return None  # Not found — caller handles fallback
            else:
                print(
                    f"[resolve_seed] HTTP {exc.code} from Semantic Scholar: {exc.reason}",
                    file=sys.stderr,
                )
                if attempt == retries:
                    sys.exit(1)
                time.sleep(wait)
                wait *= BACKOFF_FACTOR
        except urllib.error.URLError as exc:
            print(
                f"[resolve_seed] Network error (attempt {attempt}/{retries}): {exc.reason}",
                file=sys.stderr,
            )
            if attempt == retries:
                sys.exit(1)
            time.sleep(wait)
            wait *= BACKOFF_FACTOR
    return None


def _normalize_doi(doi: str) -> str:
    """Strip URL prefixes and whitespace from a DOI string."""
    doi = doi.strip()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi.org/", "DOI:"]:
        if doi.lower().startswith(prefix.lower()):
            doi = doi[len(prefix) :]
    return doi.strip()


def _format_result(paper: dict) -> dict:
    """Extract a clean result dict from Semantic Scholar paper data."""
    authors = [a.get("name", "") for a in paper.get("authors", [])]
    return {
        "paperId": paper.get("paperId", ""),
        "title": paper.get("title", ""),
        "authors": authors,
        "year": paper.get("year"),
        "citationCount": paper.get("citationCount", 0),
        "externalIds": paper.get("externalIds", {}),
    }


def resolve_by_doi(doi: str) -> dict | None:
    """Resolve a paper by DOI via Semantic Scholar."""
    doi = _normalize_doi(doi)
    url = f"{BASE_URL}/paper/DOI:{urllib.parse.quote(doi, safe='')}?fields={FIELDS}"
    print(f"[resolve_seed] Looking up DOI: {doi}", file=sys.stderr)
    data = _make_request(url)
    if data and data.get("paperId"):
        return _format_result(data)
    print(
        f"[resolve_seed] DOI '{doi}' not found in Semantic Scholar.",
        file=sys.stderr,
    )
    return None


def resolve_by_title(title: str) -> dict | None:
    """Resolve a paper by title search via Semantic Scholar."""
    encoded = urllib.parse.quote(title, safe="")
    url = f"{BASE_URL}/paper/search?query={encoded}&limit=3&fields={FIELDS}"
    print(f"[resolve_seed] Searching title: {title}", file=sys.stderr)
    data = _make_request(url)
    if not data or not data.get("data"):
        print(
            f"[resolve_seed] No results for title '{title}' in Semantic Scholar.",
            file=sys.stderr,
        )
        return None
    # Return the first result; print top matches for transparency
    results = data["data"]
    print(
        f"[resolve_seed] Found {len(results)} candidate(s). Using best match.",
        file=sys.stderr,
    )
    for i, r in enumerate(results[:3]):
        print(
            f"  [{i + 1}] {r.get('title', '?')} ({r.get('year', '?')})",
            file=sys.stderr,
        )
    return _format_result(results[0])


def _looks_like_doi(value: str) -> bool:
    """Heuristic: does the string look like a DOI?"""
    return bool(
        re.match(r"^(https?://doi\.org/|doi\.org/|DOI:)?10\.\d{4,}/", value.strip())
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve a DOI or paper title to Semantic Scholar metadata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python scripts/resolve_seed.py --doi "10.1038/s41586-023-06221-2"\n'
            '  python scripts/resolve_seed.py --title "Attention is All You Need"\n'
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doi", type=str, help="DOI of the paper to resolve.")
    group.add_argument("--title", type=str, help="Title of the paper to search for.")
    args = parser.parse_args()

    result = None

    if args.doi:
        result = resolve_by_doi(args.doi)
        # Fallback: if DOI lookup fails, try title-like search with the DOI string
        if result is None:
            print(
                "[resolve_seed] Falling back to title search with DOI string...",
                file=sys.stderr,
            )
            time.sleep(REQUEST_INTERVAL)
            result = resolve_by_title(args.doi)
    elif args.title:
        result = resolve_by_title(args.title)
        # Fallback: if the title looks like a DOI, try DOI lookup
        if result is None and _looks_like_doi(args.title):
            print(
                "[resolve_seed] Title looks like a DOI. Trying DOI lookup...",
                file=sys.stderr,
            )
            time.sleep(REQUEST_INTERVAL)
            result = resolve_by_doi(args.title)

    if result is None:
        print(
            "[resolve_seed] ERROR: Could not resolve paper. "
            "Verify the DOI or title and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()  # trailing newline
    print(
        f"[resolve_seed] OK — resolved '{result['title']}' ({result['year']})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
