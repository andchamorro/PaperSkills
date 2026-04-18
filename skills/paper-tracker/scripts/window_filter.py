#!/usr/bin/env python3
"""Filter a JSON array of paper objects by a date window.

Usage:
    cat papers.json | python window_filter.py --from 2026-01-01 --to 2026-03-15 [--date-field publication_date]

Input:  JSON array on stdin. Each object should have a date field (default:
        "publication_date").
Output: JSON array of papers within the window on stdout.
Errors: Descriptive messages on stderr.
"""

import argparse
import json
import sys
from datetime import date, datetime

DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y/%m/%d",
    "%Y-%m",
    "%Y",
]

FALLBACK_FIELDS = [
    "publication_date",
    "created_date",
    "indexed_date",
    "date",
    "year",
]


def parse_date(value: str) -> date | None:
    """Try multiple date formats and return a date object or None."""
    if not value:
        return None
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def extract_date(paper: dict, primary_field: str) -> tuple[date | None, str]:
    """Extract a date from the paper, trying the primary field then fallbacks.

    Returns (date_value, field_name_used).
    """
    # Try primary field first
    val = paper.get(primary_field)
    if val is not None:
        d = parse_date(str(val))
        if d is not None:
            return d, primary_field

    # Try fallback fields
    for field in FALLBACK_FIELDS:
        if field == primary_field:
            continue
        val = paper.get(field)
        if val is not None:
            d = parse_date(str(val))
            if d is not None:
                return d, field

    return None, ""


def filter_by_window(
    papers: list,
    start: date,
    end: date,
    date_field: str,
) -> tuple[list, int, int]:
    """Filter papers to those within [start, end].

    Returns (filtered_papers, skipped_no_date, used_fallback_count).
    """
    filtered: list = []
    skipped_no_date = 0
    used_fallback = 0

    for paper in papers:
        d, field_used = extract_date(paper, date_field)
        if d is None:
            skipped_no_date += 1
            print(
                f"WARNING: Skipping paper with no parseable date: "
                f"{paper.get('title', '<untitled>')!r}",
                file=sys.stderr,
            )
            continue
        if field_used != date_field:
            used_fallback += 1
            paper["_date_fallback"] = field_used
        if start <= d <= end:
            filtered.append(paper)

    return filtered, skipped_no_date, used_fallback


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter papers by date window.",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        required=True,
        help="Start date (YYYY-MM-DD), inclusive.",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        required=True,
        help="End date (YYYY-MM-DD), inclusive.",
    )
    parser.add_argument(
        "--date-field",
        default="publication_date",
        help="JSON field containing the date (default: publication_date).",
    )
    args = parser.parse_args()

    try:
        start = datetime.strptime(args.date_from, "%Y-%m-%d").date()
    except ValueError:
        print(
            f"ERROR: Invalid --from date: {args.date_from!r}. Use YYYY-MM-DD.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        end = datetime.strptime(args.date_to, "%Y-%m-%d").date()
    except ValueError:
        print(
            f"ERROR: Invalid --to date: {args.date_to!r}. Use YYYY-MM-DD.",
            file=sys.stderr,
        )
        sys.exit(1)

    if start > end:
        print(
            f"ERROR: --from ({start}) is after --to ({end}).",
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

    filtered, skipped, fallbacks = filter_by_window(
        papers,
        start,
        end,
        args.date_field,
    )

    print(
        f"INFO: {len(papers)} papers in, {len(filtered)} within window "
        f"[{start} .. {end}], {skipped} skipped (no date), "
        f"{fallbacks} used fallback date field.",
        file=sys.stderr,
    )

    json.dump(filtered, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
