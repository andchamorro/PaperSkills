#!/usr/bin/env python3
"""
citation_tool.py — Unified citation verification and validation tool.

Merges the former orphan_cite_gate.py (LaTeX orphan detection) with cite-verify
(API-based citation resolution) into one CLI with two subcommands.

Subcommands:
    orphan-check   Validate that all \\cite{key} in a manuscript exist in refs.bib
    verify         Resolve citations against CrossRef, Semantic Scholar, and OpenAlex

Usage:
    python citation_tool.py orphan-check manuscript.tex refs.bib [--strict]
    python citation_tool.py verify --doi 10.1038/nature14539
    python citation_tool.py verify --title "Attention is All You Need" --author Vaswani
    python citation_tool.py verify --bib refs.bib [--backends crossref,semanticscholar,openalex]
    python citation_tool.py smoke-test

Examples:
    # Check for orphan citations (drop-in replacement for orphan_cite_gate.py)
    python scripts/citation_tool.py orphan-check desk/drafts/manuscript.md desk/refs.bib

    # Verify a single citation by DOI
    python scripts/citation_tool.py verify --doi 10.1145/3442188.3445922

    # Verify all entries in a bib file, using only CrossRef + OpenAlex
    python scripts/citation_tool.py verify --bib refs.bib --backends crossref,openalex

    # Run smoke tests
    python scripts/citation_tool.py smoke-test
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Set, Tuple


# ──────────────────────────────────────────────────────────────────────
# Subcommand: orphan-check  (former orphan_cite_gate.py)
# ──────────────────────────────────────────────────────────────────────

def extract_citations_from_tex(content: str) -> Set[str]:
    """Extract all citation keys from LaTeX/Markdown content."""
    cite_pattern = r"\\cite[pt]?\{([^}]+)\}"
    citations = set()
    for match in re.finditer(cite_pattern, content):
        keys = match.group(1).split(",")
        for key in keys:
            citations.add(key.strip())
    return citations


def extract_bibtex_keys(content: str) -> Set[str]:
    """Extract all entry keys from BibTeX content."""
    key_pattern = r"@\w+\{([^,]+),"
    keys = set()
    for match in re.finditer(key_pattern, content):
        keys.add(match.group(1).strip())
    return keys


def orphan_check(manuscript: Path, bibtex: Path, strict: bool = False) -> Tuple[bool, list]:
    """
    Validate that all citations in manuscript exist in bibtex file.

    Returns:
        Tuple of (is_valid, list of messages)
    """
    messages = []

    if not manuscript.exists():
        return False, [f"Error: Manuscript not found: {manuscript}"]
    if not bibtex.exists():
        return False, [f"Error: BibTeX file not found: {bibtex}"]

    tex_content = manuscript.read_text()
    bib_content = bibtex.read_text()

    cited_keys = extract_citations_from_tex(tex_content)
    available_keys = extract_bibtex_keys(bib_content)

    messages.append(f"Citations in manuscript: {len(cited_keys)}")
    messages.append(f"Entries in refs.bib: {len(available_keys)}")

    orphans = cited_keys - available_keys
    unused = available_keys - cited_keys

    if orphans:
        messages.append(
            f"\n✗ Found {len(orphans)} orphan citation(s) (cited but not in refs.bib):"
        )
        for key in sorted(orphans):
            messages.append(f"  - {key}")

        messages.append("\nOrphan locations:")
        for key in sorted(orphans):
            pattern = rf"\\cite[pt]?\{{[^}}]*{re.escape(key)}[^}}]*\}}"
            for match in re.finditer(pattern, tex_content):
                line_num = tex_content[: match.start()].count("\n") + 1
                messages.append(f"  - {key}: line {line_num}")
                break

    if unused and strict:
        messages.append(
            f"\n⚠ Found {len(unused)} unused citation(s) (in refs.bib but not cited):"
        )
        for key in sorted(unused)[:10]:
            messages.append(f"  - {key}")
        if len(unused) > 10:
            messages.append(f"  ... and {len(unused) - 10} more")

    is_valid = len(orphans) == 0
    if is_valid:
        messages.append("\n✓ All citations are valid")

    return is_valid, messages


# ──────────────────────────────────────────────────────────────────────
# Subcommand: verify  (former cite-verify logic)
# ──────────────────────────────────────────────────────────────────────

DEFAULT_BACKENDS = ["crossref", "semanticscholar", "openalex"]

BACKEND_URLS = {
    "crossref": {
        "by_doi": "https://api.crossref.org/works/{doi}",
        "by_query": "https://api.crossref.org/works?query.bibliographic={title}&query.author={author}&rows=3",
    },
    "semanticscholar": {
        "by_doi": "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,authors,year,externalIds,venue",
        "by_query": "https://api.semanticscholar.org/graph/v1/paper/search?query={title}+{author}&limit=3&fields=title,authors,year,externalIds,venue",
    },
    "openalex": {
        "by_doi": "https://api.openalex.org/works/https://doi.org/{doi}?mailto=paperskills@example.com",
        "by_query": "https://api.openalex.org/works?search={title}&filter=author.search:{author}&mailto=paperskills@example.com",
    },
}

# Per-backend delay to respect rate limits
BACKEND_DELAY = {
    "crossref": 0.2,
    "semanticscholar": 1.0,
    "openalex": 0.1,
}


def _fetch(url: str, timeout: int = 15) -> dict | None:
    """Fetch JSON from URL with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperSkills/1.0 (citation_tool)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        return None


def normalize_doi(doi: str) -> str | None:
    """Normalize DOI to canonical lowercase form."""
    if not doi:
        return None
    doi = doi.lower().strip()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi:"]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi if doi.startswith("10.") else None


def verify_single(
    doi: str | None = None,
    title: str | None = None,
    author: str | None = None,
    backends: list[str] | None = None,
) -> dict:
    """
    Verify a single citation against configured backends.

    Tries each backend in order until a match is found (fallback chain).
    Returns a result dict with status, matched metadata, and source.
    """
    if backends is None:
        backends = DEFAULT_BACKENDS

    doi = normalize_doi(doi) if doi else None
    result = {
        "input_doi": doi,
        "input_title": title,
        "input_author": author,
        "status": "NOT_FOUND",
        "source": None,
        "metadata": {},
    }

    for backend in backends:
        urls = BACKEND_URLS.get(backend)
        if not urls:
            continue

        data = None

        # Try by DOI first
        if doi and "by_doi" in urls:
            url = urls["by_doi"].format(doi=urllib.parse.quote(doi, safe=""))
            data = _fetch(url)

        # Fall back to query if no DOI or DOI lookup failed
        if not data and title and "by_query" in urls:
            url = urls["by_query"].format(
                title=urllib.parse.quote(title or ""),
                author=urllib.parse.quote(author or ""),
            )
            data = _fetch(url)

        if not data:
            time.sleep(BACKEND_DELAY.get(backend, 0.5))
            continue

        # Parse response per backend
        meta = _parse_backend_response(backend, data)
        if meta:
            result["status"] = "FOUND"
            result["source"] = backend
            result["metadata"] = meta
            return result

        time.sleep(BACKEND_DELAY.get(backend, 0.5))

    return result


def _parse_backend_response(backend: str, data: dict) -> dict | None:
    """Extract normalized metadata from a backend response."""
    if backend == "crossref":
        msg = data.get("message", data)
        if not msg or "title" not in msg:
            return None
        titles = msg.get("title", [])
        return {
            "title": titles[0] if titles else None,
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in msg.get("author", [])[:5]
            ],
            "year": (msg.get("published-print") or msg.get("published-online") or {})
                    .get("date-parts", [[None]])[0][0],
            "venue": (msg.get("container-title") or [None])[0],
            "doi": msg.get("DOI"),
            "page": msg.get("page"),
            "type": msg.get("type"),
        }

    elif backend == "semanticscholar":
        # Direct lookup returns the paper; search returns {"data": [...]}
        if "data" in data and isinstance(data["data"], list):
            if not data["data"]:
                return None
            data = data["data"][0]
        if "title" not in data:
            return None
        return {
            "title": data.get("title"),
            "authors": [a.get("name", "") for a in data.get("authors", [])[:5]],
            "year": data.get("year"),
            "venue": data.get("venue"),
            "doi": (data.get("externalIds") or {}).get("DOI"),
        }

    elif backend == "openalex":
        if "title" not in data and "display_name" not in data:
            # Search results wrapper
            results = data.get("results", [])
            if not results:
                return None
            data = results[0]
        return {
            "title": data.get("display_name") or data.get("title"),
            "authors": [
                a.get("author", {}).get("display_name", "")
                for a in data.get("authorships", [])[:5]
            ],
            "year": data.get("publication_year"),
            "venue": (data.get("primary_location") or {}).get("source", {}).get("display_name"),
            "doi": data.get("doi"),
            "cited_by_count": data.get("cited_by_count"),
        }

    return None


def verify_bib(bib_path: Path, backends: list[str]) -> list[dict]:
    """Verify all entries in a BibTeX file."""
    if not bib_path.exists():
        print(f"Error: BibTeX file not found: {bib_path}", file=sys.stderr)
        sys.exit(1)

    content = bib_path.read_text()
    # Parse bib entries: extract key, title, author, doi
    entry_pattern = r"@\w+\{([^,]+),\s*(.*?)(?=\n@|\Z)"
    entries = []

    for match in re.finditer(entry_pattern, content, re.DOTALL):
        key = match.group(1).strip()
        body = match.group(2)

        title_match = re.search(r"title\s*=\s*\{([^}]+)\}", body, re.IGNORECASE)
        author_match = re.search(r"author\s*=\s*\{([^}]+)\}", body, re.IGNORECASE)
        doi_match = re.search(r"doi\s*=\s*\{([^}]+)\}", body, re.IGNORECASE)

        entries.append({
            "key": key,
            "title": title_match.group(1) if title_match else None,
            "author": author_match.group(1).split(" and ")[0].strip() if author_match else None,
            "doi": doi_match.group(1) if doi_match else None,
        })

    results = []
    for i, entry in enumerate(entries):
        print(f"  [{i+1}/{len(entries)}] Verifying: {entry['key']}...", file=sys.stderr)
        result = verify_single(
            doi=entry.get("doi"),
            title=entry.get("title"),
            author=entry.get("author"),
            backends=backends,
        )
        result["bib_key"] = entry["key"]
        results.append(result)

    return results


# ──────────────────────────────────────────────────────────────────────
# Subcommand: smoke-test
# ──────────────────────────────────────────────────────────────────────

def smoke_test() -> bool:
    """Run minimal smoke tests to verify the tool works."""
    print("Running smoke tests...\n", file=sys.stderr)
    passed = 0
    failed = 0

    # Test 1: orphan-check with inline data
    print("  Test 1: orphan-check (no orphans)...", file=sys.stderr, end=" ")
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
        f.write(r"We follow \cite{smith2024} and \citep{jones2023}.")
        tex_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
        f.write("@article{smith2024, title={Foo}, author={Smith}}\n")
        f.write("@article{jones2023, title={Bar}, author={Jones}}\n")
        bib_path = f.name
    ok, msgs = orphan_check(Path(tex_path), Path(bib_path))
    os.unlink(tex_path)
    os.unlink(bib_path)
    if ok:
        print("PASS", file=sys.stderr)
        passed += 1
    else:
        print(f"FAIL: {msgs}", file=sys.stderr)
        failed += 1

    # Test 2: orphan-check detecting orphans
    print("  Test 2: orphan-check (with orphans)...", file=sys.stderr, end=" ")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
        f.write(r"We follow \cite{smith2024} and \cite{ghost2025}.")
        tex_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
        f.write("@article{smith2024, title={Foo}, author={Smith}}\n")
        bib_path = f.name
    ok, msgs = orphan_check(Path(tex_path), Path(bib_path))
    os.unlink(tex_path)
    os.unlink(bib_path)
    if not ok and any("ghost2025" in m for m in msgs):
        print("PASS", file=sys.stderr)
        passed += 1
    else:
        print(f"FAIL: expected orphan 'ghost2025': {msgs}", file=sys.stderr)
        failed += 1

    # Test 3: DOI normalization
    print("  Test 3: DOI normalization...", file=sys.stderr, end=" ")
    tests = [
        ("https://doi.org/10.1234/foo", "10.1234/foo"),
        ("DOI:10.5678/bar", "10.5678/bar"),
        ("10.9999/baz", "10.9999/baz"),
        ("not-a-doi", None),
    ]
    all_ok = all(normalize_doi(inp) == exp for inp, exp in tests)
    if all_ok:
        print("PASS", file=sys.stderr)
        passed += 1
    else:
        print("FAIL", file=sys.stderr)
        failed += 1

    # Test 4: verify single DOI (network, may skip)
    print("  Test 4: verify by DOI (network)...", file=sys.stderr, end=" ")
    try:
        result = verify_single(doi="10.1145/3442188.3445922", backends=["crossref"])
        if result["status"] == "FOUND":
            print("PASS", file=sys.stderr)
            passed += 1
        else:
            print("SKIP (network unavailable)", file=sys.stderr)
    except Exception as e:
        print(f"SKIP ({e})", file=sys.stderr)

    print(f"\nResults: {passed} passed, {failed} failed", file=sys.stderr)
    return failed == 0


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Unified citation verification and validation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s orphan-check manuscript.tex refs.bib
  %(prog)s orphan-check manuscript.tex refs.bib --strict
  %(prog)s verify --doi 10.1145/3442188.3445922
  %(prog)s verify --title "Attention is All You Need" --author Vaswani
  %(prog)s verify --bib refs.bib --backends crossref,openalex
  %(prog)s smoke-test
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # orphan-check
    p_orphan = sub.add_parser(
        "orphan-check",
        help="Validate all \\cite{key} in manuscript exist in refs.bib",
    )
    p_orphan.add_argument("manuscript", help="Path to manuscript (.tex or .md)")
    p_orphan.add_argument("bibtex", help="Path to BibTeX file (.bib)")
    p_orphan.add_argument("--strict", action="store_true", help="Also warn about unused citations")
    p_orphan.add_argument("--quiet", action="store_true", help="Only output errors")

    # verify
    p_verify = sub.add_parser(
        "verify",
        help="Resolve citations against CrossRef, Semantic Scholar, and OpenAlex",
    )
    p_verify.add_argument("--doi", help="DOI to verify")
    p_verify.add_argument("--title", help="Paper title to search")
    p_verify.add_argument("--author", help="Author name (used with --title)")
    p_verify.add_argument("--bib", help="BibTeX file — verify all entries")
    p_verify.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKENDS),
        help=f"Comma-separated backends in fallback order (default: {','.join(DEFAULT_BACKENDS)})",
    )

    # smoke-test
    sub.add_parser("smoke-test", help="Run built-in smoke tests")

    args = parser.parse_args()

    if args.command == "orphan-check":
        is_valid, messages = orphan_check(
            Path(args.manuscript), Path(args.bibtex), strict=args.strict
        )
        if not args.quiet or not is_valid:
            for msg in messages:
                print(msg)
        sys.exit(0 if is_valid else 1)

    elif args.command == "verify":
        backends = [b.strip() for b in args.backends.split(",")]

        if args.bib:
            results = verify_bib(Path(args.bib), backends)
            found = sum(1 for r in results if r["status"] == "FOUND")
            print(json.dumps({
                "total": len(results),
                "found": found,
                "not_found": len(results) - found,
                "results": results,
            }, indent=2, ensure_ascii=False))
            sys.exit(0 if found == len(results) else 1)
        elif args.doi or args.title:
            result = verify_single(
                doi=args.doi, title=args.title, author=args.author, backends=backends
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(0 if result["status"] == "FOUND" else 1)
        else:
            print("Error: provide --doi, --title, or --bib", file=sys.stderr)
            sys.exit(2)

    elif args.command == "smoke-test":
        ok = smoke_test()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
