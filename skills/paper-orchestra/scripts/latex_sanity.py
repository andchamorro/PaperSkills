#!/usr/bin/env python3
"""
latex_sanity.py - Validate LaTeX manuscript for common errors.

Checks for:
- Unbalanced begin/end environments
- Missing required sections
- Figure/table reference consistency
- Basic compilation readiness

Usage:
    python scripts/latex_sanity.py desk/drafts/manuscript.md
    python scripts/latex_sanity.py manuscript.tex --strict
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def check_environment_balance(content: str) -> list[str]:
    """Check that all begin/end environments are balanced."""
    errors = []

    # Extract all begin and end commands
    begin_pattern = r"\\begin\{(\w+)\}"
    end_pattern = r"\\end\{(\w+)\}"

    begins = re.findall(begin_pattern, content)
    ends = re.findall(end_pattern, content)

    begin_counts = Counter(begins)
    end_counts = Counter(ends)

    all_envs = set(begin_counts.keys()) | set(end_counts.keys())

    for env in all_envs:
        b = begin_counts.get(env, 0)
        e = end_counts.get(env, 0)
        if b != e:
            if b > e:
                errors.append(f"Unbalanced: \\begin{{{env}}} ({b}) > \\end{{{env}}} ({e})")
            else:
                errors.append(f"Unbalanced: \\end{{{env}}} ({e}) > \\begin{{{env}}} ({b})")

    # Check for specific mismatches (figure vs figure*)
    figure_begin = len(re.findall(r"\\begin\{figure\}", content))
    figure_end = len(re.findall(r"\\end\{figure\}", content))
    figurestar_begin = len(re.findall(r"\\begin\{figure\*\}", content))
    figurestar_end = len(re.findall(r"\\end\{figure\*\}", content))

    if figure_begin != figure_end:
        errors.append(f"figure environment mismatch: {figure_begin} begins, {figure_end} ends")
    if figurestar_begin != figurestar_end:
        errors.append(
            f"figure* environment mismatch: {figurestar_begin} begins, {figurestar_end} ends"
        )

    return errors


def check_document_structure(content: str) -> list[str]:
    """Check for basic document structure."""
    errors = []

    # Check for documentclass
    if "\\documentclass" not in content:
        errors.append("Missing \\documentclass declaration")

    # Check for document environment
    if "\\begin{document}" not in content:
        errors.append("Missing \\begin{document}")
    if "\\end{document}" not in content:
        errors.append("Missing \\end{document}")

    # Check that document environment comes after preamble
    doc_begin = content.find("\\begin{document}")
    doc_class = content.find("\\documentclass")
    if doc_begin != -1 and doc_class != -1 and doc_begin < doc_class:
        errors.append("\\begin{document} appears before \\documentclass")

    return errors


def check_references(content: str) -> list[str]:
    """Check that all figure/table references have corresponding labels."""
    warnings = []

    # Extract all labels
    label_pattern = r"\\label\{([^}]+)\}"
    labels = set(re.findall(label_pattern, content))

    # Extract all refs
    ref_pattern = r"\\(?:c?ref|autoref|Cref)\{([^}]+)\}"
    refs = set(re.findall(ref_pattern, content))

    # Find undefined references
    undefined = refs - labels
    if undefined:
        for ref in sorted(undefined):
            warnings.append(f"Undefined reference: \\ref{{{ref}}}")

    # Find unused labels (less critical)
    labels - refs
    # Don't warn about unused labels by default

    return warnings


def check_common_typos(content: str) -> list[str]:
    """Check for common LaTeX typos."""
    warnings = []

    typos = [
        (
            r"\\usepackage\[capitalize\]\{cleverref\}",
            "\\usepackage[capitalize]{cleveref} (not cleverref)",
        ),
        (r"\\incudegraphics", "\\includegraphics (typo: incudegraphics)"),
        (r"\\being\{", "\\begin{ (typo: being)"),
        (r"\\ednote", "\\endnote (typo: ednote)"),
    ]

    for pattern, message in typos:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"Possible typo: {message}")

    return warnings


def check_figure_inclusions(content: str) -> list[str]:
    """Check that includegraphics paths are valid."""
    warnings = []

    # Extract all includegraphics
    pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"

    for match in re.finditer(pattern, content):
        path = match.group(1)

        # Check for common issues
        if " " in path and not path.startswith('"'):
            warnings.append(f"Space in path without quotes: {path}")

        if (
            not path.lower().endswith((".png", ".pdf", ".jpg", ".jpeg", ".eps"))
            and "." not in path.split("/")[-1]
        ):
            warnings.append(f"Missing file extension: {path}")

    return warnings


def validate_latex(filepath: Path, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Validate a LaTeX file.

    Returns:
        Tuple of (is_valid, list of messages)
    """
    messages = []
    errors = []
    warnings = []

    if not filepath.exists():
        return False, [f"Error: File not found: {filepath}"]

    content = filepath.read_text()

    # Run all checks
    errors.extend(check_document_structure(content))
    errors.extend(check_environment_balance(content))

    warnings.extend(check_references(content))
    warnings.extend(check_common_typos(content))
    warnings.extend(check_figure_inclusions(content))

    # Report
    if errors:
        messages.append(f"✗ Found {len(errors)} error(s):")
        for e in errors:
            messages.append(f"  - {e}")

    if warnings:
        messages.append(f"\n⚠ Found {len(warnings)} warning(s):")
        for w in warnings:
            messages.append(f"  - {w}")

    is_valid = len(errors) == 0 and (not strict or len(warnings) == 0)

    if is_valid:
        messages.append("\n✓ LaTeX validation passed")

    return is_valid, messages


def main():
    parser = argparse.ArgumentParser(description="Validate LaTeX manuscript for common errors")
    parser.add_argument("manuscript", type=str, help="Path to the manuscript file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--quiet", action="store_true", help="Only output errors")
    args = parser.parse_args()

    is_valid, messages = validate_latex(Path(args.manuscript), strict=args.strict)

    if not args.quiet or not is_valid:
        for msg in messages:
            print(msg)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
