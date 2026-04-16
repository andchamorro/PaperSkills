#!/usr/bin/env python3
"""
orphan_cite_gate.py - Validate that all citations in manuscript exist in refs.bib.

Usage:
    python scripts/orphan_cite_gate.py desk/drafts/manuscript.md desk/refs.bib
    python scripts/orphan_cite_gate.py manuscript.tex refs.bib --strict
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple


def extract_citations_from_tex(content: str) -> Set[str]:
    """Extract all citation keys from LaTeX content."""
    # Match \cite{key}, \citep{key}, \citet{key}, \cite{key1,key2}
    cite_pattern = r"\\cite[pt]?\{([^}]+)\}"

    citations = set()
    for match in re.finditer(cite_pattern, content):
        # Handle comma-separated citations
        keys = match.group(1).split(",")
        for key in keys:
            citations.add(key.strip())

    return citations


def extract_bibtex_keys(content: str) -> Set[str]:
    """Extract all entry keys from BibTeX content."""
    # Match @type{key, or @type{key,
    key_pattern = r"@\w+\{([^,]+),"

    keys = set()
    for match in re.finditer(key_pattern, content):
        keys.add(match.group(1).strip())

    return keys


def validate_citations(manuscript: Path, bibtex: Path) -> Tuple[bool, List[str]]:
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

    # Find orphan citations (cited but not in bib)
    orphans = cited_keys - available_keys

    # Find unused citations (in bib but not cited)
    unused = available_keys - cited_keys

    if orphans:
        messages.append(
            f"\n✗ Found {len(orphans)} orphan citation(s) (cited but not in refs.bib):"
        )
        for key in sorted(orphans):
            messages.append(f"  - {key}")

        # Find where each orphan is used
        messages.append("\nOrphan locations:")
        for key in sorted(orphans):
            pattern = rf"\\cite[pt]?\{{[^}}]*{re.escape(key)}[^}}]*\}}"
            for match in re.finditer(pattern, tex_content):
                # Find line number
                line_num = tex_content[: match.start()].count("\n") + 1
                messages.append(f"  - {key}: line {line_num}")
                break

    if unused:
        messages.append(
            f"\n⚠ Found {len(unused)} unused citation(s) (in refs.bib but not cited):"
        )
        for key in sorted(unused)[:10]:  # Show first 10
            messages.append(f"  - {key}")
        if len(unused) > 10:
            messages.append(f"  ... and {len(unused) - 10} more")

    is_valid = len(orphans) == 0

    if is_valid:
        messages.append("\n✓ All citations are valid")

    return is_valid, messages


def main():
    parser = argparse.ArgumentParser(
        description="Validate citations against BibTeX file"
    )
    parser.add_argument(
        "manuscript", type=str, help="Path to the manuscript file (.tex or .md)"
    )
    parser.add_argument("bibtex", type=str, help="Path to the BibTeX file (.bib)")
    parser.add_argument(
        "--strict", action="store_true", help="Also warn about unused citations"
    )
    parser.add_argument("--quiet", action="store_true", help="Only output errors")
    args = parser.parse_args()

    is_valid, messages = validate_citations(Path(args.manuscript), Path(args.bibtex))

    if not args.quiet or not is_valid:
        for msg in messages:
            print(msg)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
