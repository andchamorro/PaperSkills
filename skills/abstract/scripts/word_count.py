#!/usr/bin/env python3
"""Count words in a text file and validate against a target word count.

Usage:
    python word_count.py <file> [--target 250] [--tolerance 20]

Exit codes:
    0  — word count is within tolerance of target (or no target specified)
    1  — word count is outside tolerance
    2  — file could not be read
"""

import argparse
import sys
from pathlib import Path


def count_words(text: str) -> int:
    """Return the number of whitespace-delimited words in *text*."""
    return len(text.split())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Count words in a text file and validate against a target.",
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the text file to analyse.",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        help="Target word count (e.g. 250). If omitted, only the count is printed.",
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
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        return 2

    try:
        text = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = filepath.read_text(encoding="latin-1")
            print(
                "WARNING: File was not valid UTF-8; read with Latin-1 fallback.",
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"ERROR: Unable to read file: {exc}", file=sys.stderr)
            return 2

    # --- Count ---------------------------------------------------------------
    wc = count_words(text)

    if args.target is None:
        print(f"Word count: {wc}")
        return 0

    lower = args.target - args.tolerance
    upper = args.target + args.tolerance
    within = lower <= wc <= upper

    status = "PASS" if within else "FAIL"
    print(
        f"Word count: {wc} | Target: {args.target} ± {args.tolerance} "
        f"(range {lower}–{upper}) | {status}"
    )

    return 0 if within else 1


if __name__ == "__main__":
    raise SystemExit(main())
