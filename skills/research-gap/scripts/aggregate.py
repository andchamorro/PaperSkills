#!/usr/bin/env python3
"""
Aggregate trend data from OpenAlex for a research topic.
Outputs JSON, formatted text, or a mini HTML table.

Usage:
    python scripts/aggregate.py "LLM fairness"
    python scripts/aggregate.py "federated learning" --format text
    python scripts/aggregate.py "climate finance" --format html
    python scripts/aggregate.py "AI ethics" --per-page 50

Exit codes:
    0: success
    1: no input or API failure
"""

import argparse
import html as html_module
import json
import sys
import time
import urllib.parse
import urllib.request


def fetch_json(url: str, retries: int = 3) -> dict | None:
    """Fetch JSON from URL with exponential backoff on failure."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = int(e.headers.get("Retry-After", 2**attempt))
                print(
                    f"WARN: Rate limited (429). Waiting {wait}s before retry {attempt + 1}/{retries}.",
                    file=sys.stderr,
                )
                time.sleep(wait)
            elif attempt < retries - 1:
                print(
                    f"WARN: HTTP {e.code} for {url}. Retrying in {2**attempt}s...",
                    file=sys.stderr,
                )
                time.sleep(2**attempt)
            else:
                print(
                    f"ERROR: Failed after {retries} attempts for {url}: HTTP {e.code} {e.reason}",
                    file=sys.stderr,
                )
                return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                print(f"ERROR: Failed to fetch {url}: {e}", file=sys.stderr)
                return None
    return None


def get_trend_data(
    topic: str,
    per_page: int = 25,
    mailto: str = "paperskills@example.com",
) -> dict:
    """Gather trend data from OpenAlex for a topic."""
    encoded_topic = urllib.parse.quote(topic)
    results = {}
    errors = []

    # Yearly publication counts
    url = f"https://api.openalex.org/works?search={encoded_topic}&group_by=publication_year&mailto={mailto}"
    data = fetch_json(url)
    if data and "group_by" in data:
        results["yearly_counts"] = {
            g["key"]: g["count"] for g in data["group_by"] if g["key"]
        }
    else:
        errors.append("yearly_counts: failed to fetch publication trend data")

    # Recent top-cited papers (2022-2026)
    url = (
        f"https://api.openalex.org/works?search={encoded_topic}"
        f"&filter=publication_year:2022-2026&per_page={per_page}"
        f"&sort=cited_by_count:desc&mailto={mailto}"
    )
    data = fetch_json(url)
    if data and "results" in data:
        results["recent_top"] = [
            {
                "title": r.get("title", ""),
                "year": r.get("publication_year"),
                "citations": r.get("cited_by_count", 0),
                "venue": (r.get("primary_location") or {})
                .get("source", {})
                .get("display_name", ""),
            }
            for r in data["results"][:20]
        ]
    else:
        errors.append("recent_top: failed to fetch recent papers")

    # Classic top-cited papers (2010-2015)
    url = (
        f"https://api.openalex.org/works?search={encoded_topic}"
        f"&filter=publication_year:2010-2015&per_page={per_page}"
        f"&sort=cited_by_count:desc&mailto={mailto}"
    )
    data = fetch_json(url)
    if data and "results" in data:
        results["classic_top"] = [
            {
                "title": r.get("title", ""),
                "year": r.get("publication_year"),
                "citations": r.get("cited_by_count", 0),
                "venue": (r.get("primary_location") or {})
                .get("source", {})
                .get("display_name", ""),
            }
            for r in data["results"][:20]
        ]
    else:
        errors.append("classic_top: failed to fetch classic papers")

    # Related concepts
    url = f"https://api.openalex.org/concepts?search={encoded_topic}&mailto={mailto}"
    data = fetch_json(url)
    if data and "results" in data:
        results["concepts"] = [
            {
                "name": c.get("display_name", ""),
                "works_count": c.get("works_count", 0),
                "level": c.get("level", 0),
                "description": c.get("description", ""),
            }
            for c in data["results"][:10]
        ]
    else:
        errors.append("concepts: failed to fetch related concepts")

    if errors:
        results["_errors"] = errors

    return results


def format_text(data: dict, topic: str) -> str:
    """Format trend data as human-readable text."""
    lines = [f"OpenAlex Trend Data: {topic}", "=" * 60]

    if "_errors" in data:
        lines.append("\nWarnings:")
        for err in data["_errors"]:
            lines.append(f"  ! {err}")

    if "yearly_counts" in data:
        lines.append("\nPapers per Year:")
        for year in sorted(data["yearly_counts"].keys(), reverse=True)[:15]:
            count = data["yearly_counts"][year]
            bar = "#" * min(count // 10, 50)
            lines.append(f"  {year}: {count:>6}  {bar}")

    if "recent_top" in data:
        lines.append("\nTop 10 Recent Papers (2022-2026):")
        for i, p in enumerate(data["recent_top"][:10], 1):
            title = p["title"][:70] + ("..." if len(p["title"]) > 70 else "")
            lines.append(f"  {i:>2}. {title} ({p['year']}) — {p['citations']} cites")

    if "classic_top" in data:
        lines.append("\nTop 10 Classic Papers (2010-2015):")
        for i, p in enumerate(data["classic_top"][:10], 1):
            title = p["title"][:70] + ("..." if len(p["title"]) > 70 else "")
            lines.append(f"  {i:>2}. {title} ({p['year']}) — {p['citations']} cites")

    if "concepts" in data:
        lines.append("\nRelated Concepts:")
        for c in data["concepts"]:
            lines.append(
                f"  - {c['name']} (level {c['level']}): {c['works_count']} papers"
            )

    return "\n".join(lines)


def format_html(data: dict, topic: str) -> str:
    """Format trend data as a standalone HTML table for quick inspection."""
    esc = html_module.escape
    lines = [
        "<!DOCTYPE html>",
        f'<html lang="en"><head><meta charset="UTF-8"><title>Trend: {esc(topic)}</title>',
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#333}",
        "table{border-collapse:collapse;width:100%;margin:1rem 0}",
        "th,td{border:1px solid #ddd;padding:0.5rem;text-align:left;font-size:0.875rem}",
        "th{background:#f5f5f5}",
        "h1{font-size:1.25rem}h2{font-size:1rem;margin-top:1.5rem}",
        ".bar{background:#2c5282;height:14px;display:inline-block;border-radius:2px}",
        "</style></head><body>",
        f"<h1>Trend Data: {esc(topic)}</h1>",
    ]

    if "yearly_counts" in data:
        lines.append(
            "<h2>Papers per Year</h2><table><tr><th>Year</th><th>Count</th><th>Trend</th></tr>"
        )
        max_count = max(data["yearly_counts"].values()) if data["yearly_counts"] else 1
        for year in sorted(data["yearly_counts"].keys(), reverse=True)[:15]:
            count = data["yearly_counts"][year]
            width = int(200 * count / max_count) if max_count else 0
            lines.append(
                f"<tr><td>{year}</td><td>{count}</td>"
                f'<td><span class="bar" style="width:{width}px"></span></td></tr>'
            )
        lines.append("</table>")

    for section_key, section_title in [
        ("recent_top", "Top Recent Papers (2022-2026)"),
        ("classic_top", "Top Classic Papers (2010-2015)"),
    ]:
        if section_key in data:
            lines.append(
                f"<h2>{section_title}</h2>"
                "<table><tr><th>#</th><th>Title</th><th>Year</th><th>Cites</th><th>Venue</th></tr>"
            )
            for i, p in enumerate(data[section_key][:10], 1):
                lines.append(
                    f"<tr><td>{i}</td><td>{esc(p['title'][:80])}</td>"
                    f"<td>{p['year']}</td><td>{p['citations']}</td>"
                    f"<td>{esc(p.get('venue', ''))}</td></tr>"
                )
            lines.append("</table>")

    if "concepts" in data:
        lines.append(
            "<h2>Related Concepts</h2>"
            "<table><tr><th>Concept</th><th>Level</th><th>Works</th></tr>"
        )
        for c in data["concepts"]:
            lines.append(
                f"<tr><td>{esc(c['name'])}</td><td>{c['level']}</td>"
                f"<td>{c['works_count']}</td></tr>"
            )
        lines.append("</table>")

    if "_errors" in data:
        lines.append("<h2>Warnings</h2><ul>")
        for err in data["_errors"]:
            lines.append(f"<li>{esc(err)}</li>")
        lines.append("</ul>")

    lines.append("</body></html>")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate OpenAlex trend data for a research topic."
    )
    parser.add_argument("topic", help="Research topic to analyze")
    parser.add_argument(
        "--format",
        choices=["json", "text", "html"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=25,
        help="Results per page for paper queries (default: 25, max: 200)",
    )
    parser.add_argument(
        "--mailto",
        default="paperskills@example.com",
        help="Email for OpenAlex polite pool",
    )
    args = parser.parse_args()

    if args.per_page < 1 or args.per_page > 200:
        print(
            "ERROR: --per-page must be between 1 and 200.",
            file=sys.stderr,
        )
        sys.exit(1)

    data = get_trend_data(args.topic, per_page=args.per_page, mailto=args.mailto)

    if not data or (len(data) == 1 and "_errors" in data):
        print(
            "ERROR: No data retrieved from OpenAlex. "
            "Check topic spelling, try broadening the search, "
            "or verify network connectivity.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.format == "text":
        print(format_text(data, args.topic))
    elif args.format == "html":
        print(format_html(data, args.topic))
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
