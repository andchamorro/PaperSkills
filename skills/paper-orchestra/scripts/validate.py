#!/usr/bin/env python3
"""
validate.py - Validate PaperOrchestra desk inputs before pipeline execution.

Usage:
    python scripts/validate.py --desk desk/
    python scripts/validate.py --desk desk/ --strict
"""

import argparse
import sys
from pathlib import Path

REQUIRED_FILES = [
    ("inputs/idea.md", "Idea Summary (I)"),
    ("inputs/log.md", "Experimental Log (E)"),
    ("inputs/tmpl.md", "LaTeX Template (T)"),
    ("inputs/gl.md", "Conference Guidelines (G)"),
]

OPTIONAL_DIRS = [
    ("inputs/fig", "Pre-existing Figures (F)"),
    ("inputs/ref", "Pre-existing References (R)"),
]

MIN_CONTENT_LENGTH = {
    "inputs/idea.md": 200,
    "inputs/log.md": 300,
    "inputs/tmpl.md": 100,
    "inputs/gl.md": 50,
}


def check_file_exists(desk: Path, rel_path: str) -> tuple[bool, str]:
    """Check if a required file exists."""
    path = desk / rel_path
    if not path.exists():
        return False, f"Missing: {rel_path}"
    return True, f"Found: {rel_path}"


def check_file_content(desk: Path, rel_path: str, min_length: int) -> tuple[bool, str]:
    """Check if a file has meaningful content."""
    path = desk / rel_path
    if not path.exists():
        return False, f"Cannot check content: {rel_path} does not exist"

    content = path.read_text().strip()

    # Remove template markers and comments
    lines = [
        line
        for line in content.split("\n")
        if not line.strip().startswith("<!--") and not line.strip().startswith("%") and line.strip()
    ]

    actual_content = "\n".join(lines)

    if len(actual_content) < min_length:
        return (
            False,
            f"Insufficient content in {rel_path}: {len(actual_content)} chars (min: {min_length})",
        )

    return True, f"Content OK: {rel_path} ({len(actual_content)} chars)"


def check_template_structure(desk: Path) -> tuple[bool, str]:
    """Check that the LaTeX template has expected section commands."""
    path = desk / "inputs/tmpl.md"
    if not path.exists():
        return False, "Cannot validate template structure: tmpl.md missing"

    content = path.read_text()

    # Check for basic LaTeX structure
    required_patterns = [
        ("\\documentclass", "documentclass declaration"),
        ("\\begin{document}", "document begin"),
        ("\\end{document}", "document end"),
    ]

    missing = []
    for pattern, desc in required_patterns:
        if pattern not in content:
            missing.append(desc)

    if missing:
        return False, f"Template missing: {', '.join(missing)}"

    # Check for section commands
    section_count = content.count("\\section{")
    if section_count < 3:
        return (
            False,
            f"Template has only {section_count} sections (expected at least 3)",
        )

    return True, f"Template structure OK ({section_count} sections found)"


def check_log_has_data(desk: Path) -> tuple[bool, str]:
    """Check that the experimental log contains numeric data."""
    path = desk / "inputs/log.md"
    if not path.exists():
        return False, "Cannot validate log data: log.md missing"

    content = path.read_text()

    # Look for numeric patterns that indicate experimental data
    import re

    # Match percentages, decimals, or numbers in table-like context
    numeric_patterns = [
        r"\d+\.\d+",  # Decimal numbers
        r"\d+%",  # Percentages
        r"\|\s*\d+",  # Numbers in table cells
    ]

    has_data = any(re.search(pattern, content) for pattern in numeric_patterns)

    if not has_data:
        return False, "Experimental log appears to lack numeric data"

    return True, "Experimental log contains numeric data"


def validate_desk(desk: Path, strict: bool = False) -> tuple[bool, list[str]]:
    """
    Validate the desk directory.

    Returns:
        Tuple of (all_valid, list of messages)
    """
    messages = []
    errors = []

    # Check desk exists
    if not desk.exists():
        return False, [f"Error: Desk directory does not exist: {desk}"]

    if not desk.is_dir():
        return False, [f"Error: {desk} is not a directory"]

    # Check required files exist
    for rel_path, desc in REQUIRED_FILES:
        exists, msg = check_file_exists(desk, rel_path)
        messages.append(msg)
        if not exists:
            errors.append(f"Missing required file: {desc}")

    # Check optional directories
    for rel_path, _desc in OPTIONAL_DIRS:
        path = desk / rel_path
        if path.exists() and path.is_dir():
            file_count = len(list(path.iterdir()))
            messages.append(f"Found: {rel_path} ({file_count} files)")
        else:
            messages.append(f"Optional: {rel_path} not present")

    # If basic files are missing, stop here
    if errors:
        return (
            False,
            messages + [f"\n✗ Validation failed: {len(errors)} error(s)"] + errors,
        )

    # Content validation
    messages.append("\n--- Content Validation ---")

    for rel_path, min_len in MIN_CONTENT_LENGTH.items():
        valid, msg = check_file_content(desk, rel_path, min_len)
        messages.append(msg)
        if not valid and strict:
            errors.append(msg)

    # Template structure
    valid, msg = check_template_structure(desk)
    messages.append(msg)
    if not valid and strict:
        errors.append(msg)

    # Log data check
    valid, msg = check_log_has_data(desk)
    messages.append(msg)
    if not valid and strict:
        errors.append(msg)

    if errors:
        messages.append(f"\n✗ Validation failed: {len(errors)} error(s)")
        for e in errors:
            messages.append(f"  - {e}")
        return False, messages

    messages.append("\n✓ All validations passed")
    return True, messages


def main():
    parser = argparse.ArgumentParser(description="Validate PaperOrchestra desk inputs")
    parser.add_argument("--desk", type=str, required=True, help="Path to the desk directory")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (content checks become errors)",
    )
    parser.add_argument("--quiet", action="store_true", help="Only output errors")
    args = parser.parse_args()

    desk = Path(args.desk)
    valid, messages = validate_desk(desk, strict=args.strict)

    if not args.quiet or not valid:
        for msg in messages:
            print(msg)

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
