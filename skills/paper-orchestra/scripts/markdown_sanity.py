#!/usr/bin/env python3
"""
markdown_sanity.py - Validate a Markdown manuscript for common structural errors.

Checks:
- YAML front-matter parses (basic key: value heuristic)
- At least 3 top-level (`#` / `##`) section headings
- Figure image paths referenced with `![...](path)` resolve on disk when
  relative (skipped for URLs)
- Pandoc cross-references (`[@fig:id]`, `[@tbl:id]`) have matching labels
- Warn on stray LaTeX environments that pandoc may not round-trip cleanly
  (opt-in via --strict)

Usage:
    python scripts/markdown_sanity.py desk/drafts/manuscript.md
    python scripts/markdown_sanity.py desk/final/manuscript.md --strict
"""

import argparse
import re
import sys
from pathlib import Path


def strip_front_matter(content: str) -> tuple[str, str]:
    """Return (front_matter_text, body)."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return "", content
    return m.group(1), content[m.end() :]


def check_front_matter(fm: str) -> list[str]:
    warnings = []
    if not fm.strip():
        return warnings
    for line in fm.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith(("  ", "-", "\t")):
            continue
        if ":" not in line:
            warnings.append(f"Front-matter line missing ':' — {line!r}")
    return warnings


def check_sections(body: str) -> list[str]:
    errors = []
    # Strip fenced code blocks so '#' inside code isn't counted
    scrubbed = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    headings = re.findall(r"(?m)^#{1,2}\s+\S", scrubbed)
    if len(headings) < 3:
        errors.append(f"Only {len(headings)} top-level Markdown section(s) found (expected ≥ 3)")
    return errors


def check_figure_paths(body: str, manuscript_path: Path) -> list[str]:
    warnings = []
    pattern = r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)"
    base = manuscript_path.parent
    for match in re.finditer(pattern, body):
        path = match.group(1)
        if path.startswith(("http://", "https://", "data:")):
            continue
        candidate = (base / path).resolve()
        if not candidate.exists():
            # Also try relative to desk root (parent of drafts/, final/, refin/)
            alt = (base.parent / path).resolve()
            if not alt.exists():
                warnings.append(f"Figure path not found on disk: {path}")
    return warnings


def check_crossrefs(body: str) -> list[str]:
    warnings = []
    label_pattern = r"\{#(fig|tbl|sec|eq):([a-zA-Z0-9_-]+)\}"
    ref_pattern = r"\[@(fig|tbl|sec|eq):([a-zA-Z0-9_-]+)(?:[;,\s][^\]]*)?\]"

    labels = {(k, v) for k, v in re.findall(label_pattern, body)}
    refs = {(k, v) for k, v in re.findall(ref_pattern, body)}
    missing = refs - labels
    for kind, name in sorted(missing):
        warnings.append(f"Cross-reference [@{kind}:{name}] has no matching {{#{kind}:{name}}}")
    return warnings


def check_stray_latex(body: str) -> list[str]:
    warnings = []
    if re.search(r"\\documentclass\b", body):
        warnings.append(
            "Found \\documentclass in Markdown body — this belongs in tmpl.tex, not manuscript.md"
        )
    if re.search(r"\\begin\{document\}", body):
        warnings.append("Found \\begin{document} in Markdown body — remove, pandoc handles it")
    return warnings


def validate(path: Path, strict: bool = False) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, [f"Error: File not found: {path}"]

    content = path.read_text()
    fm, body = strip_front_matter(content)

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_sections(body))
    warnings.extend(check_front_matter(fm))
    warnings.extend(check_figure_paths(body, path))
    warnings.extend(check_crossrefs(body))
    warnings.extend(check_stray_latex(body))

    messages: list[str] = []
    if errors:
        messages.append(f"✗ Found {len(errors)} error(s):")
        for e in errors:
            messages.append(f"  - {e}")
    if warnings:
        messages.append(f"⚠ Found {len(warnings)} warning(s):")
        for w in warnings:
            messages.append(f"  - {w}")

    is_valid = not errors and (not strict or not warnings)
    if is_valid:
        messages.append("✓ Markdown manuscript validation passed")
    return is_valid, messages


def main():
    parser = argparse.ArgumentParser(description="Validate a Markdown manuscript")
    parser.add_argument("manuscript", type=str, help="Path to manuscript.md")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--quiet", action="store_true", help="Only print on failure")
    args = parser.parse_args()

    ok, messages = validate(Path(args.manuscript), strict=args.strict)
    if not args.quiet or not ok:
        for m in messages:
            print(m)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
