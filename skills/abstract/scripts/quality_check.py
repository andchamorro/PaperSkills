#!/usr/bin/env python3
"""Run quality checks on a generated abstract.

Checks performed:
  1. First-person pronoun usage (I, we, my, our, etc.)
  2. Citation patterns ([1], (Author, Year), etc.)
  3. Word count against target
  4. Structural headings match the declared format

Usage:
    python quality_check.py <abstract_file> [--format imrad|thematic] [--target 250] [--tolerance 20]

Output:
    JSON object: {"passed": bool, "word_count": int, "issues": [...]}

Exit codes:
    0  — all checks passed
    1  — one or more checks failed
    2  — file could not be read
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIRST_PERSON_PATTERN = re.compile(
    r"\b(I|we|my|our|us|me|myself|ourselves)\b",
    re.IGNORECASE,
)

CITATION_PATTERNS = [
    # Numbered citations: [1], [1,2], [1-3]
    re.compile(r"\[\d[\d,\-\s]*\]"),
    # Author-year: (Author, 2023) or (Author et al., 2023)
    re.compile(r"\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}\)"),
]

IMRAD_HEADINGS = {"background", "objective", "methods", "results", "conclusion"}
THEMATIC_HEADINGS = {"context", "thesis", "approach", "argument", "contribution"}


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_first_person(text: str) -> list[dict]:
    """Flag lines containing first-person pronouns."""
    issues: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in FIRST_PERSON_PATTERN.finditer(line):
            issues.append(
                {
                    "check": "first_person",
                    "line": lineno,
                    "detail": (
                        f"First-person pronoun '{match.group()}' found: "
                        f"...{line[max(0, match.start() - 20) : match.end() + 20].strip()}..."
                    ),
                }
            )
    return issues


def check_citations(text: str) -> list[dict]:
    """Flag lines containing citation patterns."""
    issues: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in CITATION_PATTERNS:
            for match in pattern.finditer(line):
                issues.append(
                    {
                        "check": "citation",
                        "line": lineno,
                        "detail": (f"Citation pattern found: '{match.group()}'"),
                    }
                )
    return issues


def check_word_count(
    text: str,
    target: int | None,
    tolerance: int,
) -> tuple[int, list[dict]]:
    """Check word count against target. Return (count, issues)."""
    wc = len(text.split())
    issues: list[dict] = []
    if target is not None:
        lower = target - tolerance
        upper = target + tolerance
        if not (lower <= wc <= upper):
            issues.append(
                {
                    "check": "word_count",
                    "line": 0,
                    "detail": (
                        f"Word count {wc} is outside target range "
                        f"{lower}–{upper} (target {target} ± {tolerance})."
                    ),
                }
            )
    return wc, issues


def check_structure(text: str, fmt: str | None) -> list[dict]:
    """Verify that expected section headings are present for the declared format."""
    if fmt is None:
        return []

    expected = IMRAD_HEADINGS if fmt == "imrad" else THEMATIC_HEADINGS
    text_lower = text.lower()

    missing = [h for h in sorted(expected) if h not in text_lower]
    issues: list[dict] = []
    if missing:
        issues.append(
            {
                "check": "structure",
                "line": 0,
                "detail": (
                    f"Missing expected headings for '{fmt}' format: "
                    f"{', '.join(missing)}."
                ),
            }
        )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run quality checks on a generated abstract.",
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the abstract text file.",
    )
    parser.add_argument(
        "--format",
        choices=["imrad", "thematic"],
        default=None,
        dest="fmt",
        help="Expected abstract format (imrad or thematic). "
        "If omitted, structural heading checks are skipped.",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=250,
        help="Target word count (default: 250).",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=20,
        help="Acceptable deviation from target in words (default: 20).",
    )

    args = parser.parse_args(argv)

    # --- Read file -----------------------------------------------------------
    filepath = Path(args.file)
    if not filepath.exists():
        result = {
            "passed": False,
            "word_count": 0,
            "issues": [
                {
                    "check": "file",
                    "line": 0,
                    "detail": f"File not found: {filepath}",
                }
            ],
        }
        print(json.dumps(result, indent=2))
        return 2

    try:
        text = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = filepath.read_text(encoding="latin-1")
        except Exception as exc:
            result = {
                "passed": False,
                "word_count": 0,
                "issues": [
                    {
                        "check": "file",
                        "line": 0,
                        "detail": f"Unable to read file: {exc}",
                    }
                ],
            }
            print(json.dumps(result, indent=2))
            return 2

    if not text.strip():
        result = {
            "passed": False,
            "word_count": 0,
            "issues": [
                {
                    "check": "file",
                    "line": 0,
                    "detail": "File is empty.",
                }
            ],
        }
        print(json.dumps(result, indent=2))
        return 2

    # --- Run checks ----------------------------------------------------------
    all_issues: list[dict] = []

    all_issues.extend(check_first_person(text))
    all_issues.extend(check_citations(text))

    wc, wc_issues = check_word_count(text, args.target, args.tolerance)
    all_issues.extend(wc_issues)

    all_issues.extend(check_structure(text, args.fmt))

    passed = len(all_issues) == 0

    result = {
        "passed": passed,
        "word_count": wc,
        "issues": all_issues,
    }

    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
