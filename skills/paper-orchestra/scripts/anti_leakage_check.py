#!/usr/bin/env python3
"""
anti_leakage_check.py - Check manuscript for leaked author information.

This script scans the generated manuscript for potential author identity leaks:
- Author names and emails from common patterns
- Institutional affiliations
- Acknowledgement sections with identifiable information
- URLs that might reveal authorship

Usage:
    python scripts/anti_leakage_check.py desk/drafts/manuscript.md
    python scripts/anti_leakage_check.py desk/final/manuscript.md --strict
"""

import argparse
import re
import sys
from pathlib import Path

# Patterns that suggest author identity leakage
LEAK_PATTERNS = [
    # Email patterns
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "email address"),
    # Common affiliation markers
    (r"\\author\{[^}]+\}", "author declaration"),
    (r"\\affil\{[^}]+\}", "affiliation declaration"),
    (r"\\institute\{[^}]+\}", "institute declaration"),
    (r"\\thanks\{[^}]+\}", "thanks/footnote with potential author info"),
    # Acknowledgement patterns with specific info
    (
        r"acknowledge[s]?\s+(?:the\s+)?(?:support|funding|grant)",
        "acknowledgement with funding info",
    ),
    (r"grant\s+(?:number|no\.?|#)\s*[A-Z0-9-]+", "grant number"),
    # GitHub/personal URLs
    (r"github\.com/[a-zA-Z0-9_-]+(?!/[a-zA-Z0-9_-]+)", "personal GitHub URL"),
    (r"(?:twitter|x)\.com/[a-zA-Z0-9_]+", "Twitter/X handle"),
    (r"linkedin\.com/in/[a-zA-Z0-9_-]+", "LinkedIn profile"),
    # "Corresponding author" patterns
    (r"corresponding\s+author", "corresponding author marker"),
    (r"\*.*(?:equal|contribution)", "contribution marker"),
    # Common university patterns (might need refinement)
    (r"University\s+of\s+[A-Z][a-z]+", "university name"),
    (r"[A-Z][a-z]+\s+University", "university name"),
    (r"[A-Z]+\s+Lab(?:oratory)?", "lab name"),
]

# Patterns that are acceptable (whitelisted)
WHITELIST_PATTERNS = [
    r"Anonymous\s+Author",
    r"anonymous\s+submission",
    r"Under\s+review",
    r"Submitted\s+to",
    r"author\{Anonymous\}",
]

# Strict mode patterns (more aggressive checking)
STRICT_PATTERNS = [
    (r"\b[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)", "self-citation pattern (Name et al.)"),
    (r"our\s+previous\s+work", "self-reference to previous work"),
    (r"we\s+previously\s+(?:showed|demonstrated|proposed)", "self-reference"),
    (r"in\s+\[[^\]]+\],\s+we", "self-citation with first person"),
]


def is_whitelisted(text: str, match: re.Match) -> bool:
    """Check if a match is whitelisted (acceptable)."""
    # Get context around the match
    start = max(0, match.start() - 50)
    end = min(len(text), match.end() + 50)
    context = text[start:end]

    return any(re.search(pattern, context, re.IGNORECASE) for pattern in WHITELIST_PATTERNS)


def check_for_leaks(content: str, strict: bool = False) -> list[tuple[str, str, int, str]]:
    """
    Scan content for potential author identity leaks.

    Returns:
        List of tuples: (pattern_type, matched_text, line_number, context)
    """
    leaks = []
    content.split("\n")

    patterns = LEAK_PATTERNS.copy()
    if strict:
        patterns.extend(STRICT_PATTERNS)

    for pattern, description in patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            if is_whitelisted(content, match):
                continue

            # Find line number
            line_num = content[: match.start()].count("\n") + 1

            # Get context
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            context = content[line_start:line_end].strip()

            leaks.append((description, match.group(), line_num, context))

    return leaks


def check_manuscript(filepath: Path, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Check a manuscript file for leaks.

    Returns:
        Tuple of (is_clean, list of warning messages)
    """
    if not filepath.exists():
        return False, [f"Error: File not found: {filepath}"]

    content = filepath.read_text()
    leaks = check_for_leaks(content, strict=strict)

    if not leaks:
        return True, ["✓ No potential author identity leaks detected"]

    messages = [f"⚠ Found {len(leaks)} potential leak(s):\n"]

    for i, (desc, matched, line_num, context) in enumerate(leaks, 1):
        messages.append(f"{i}. [{desc}] Line {line_num}")
        messages.append(f"   Matched: {matched}")
        messages.append(f"   Context: {context[:80]}...")
        messages.append("")

    messages.append("Review these matches and remove any identifying information.")
    messages.append("Use 'Anonymous Author(s)' for author fields.")

    return False, messages


def main():
    parser = argparse.ArgumentParser(description="Check manuscript for leaked author information")
    parser.add_argument("manuscript", type=str, help="Path to the manuscript file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict checking (more aggressive patterns)",
    )
    parser.add_argument("--quiet", action="store_true", help="Only output if leaks are found")
    parser.add_argument(
        "--fail-on-leak",
        action="store_true",
        help="Exit with error code if leaks are found",
    )
    args = parser.parse_args()

    filepath = Path(args.manuscript)
    is_clean, messages = check_manuscript(filepath, strict=args.strict)

    if not args.quiet or not is_clean:
        for msg in messages:
            print(msg)

    if args.fail_on_leak and not is_clean:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
