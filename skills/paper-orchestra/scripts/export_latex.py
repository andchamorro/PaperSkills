#!/usr/bin/env python3
"""
export_latex.py — Export the canonical Markdown manuscript to LaTeX (and optionally PDF)
using pandoc.

The canonical manuscript is `desk/final/manuscript.md`. This script produces
`desk/final/manuscript.tex` (and, with --pdf, `desk/final/manuscript.pdf`).

If `desk/inputs/tmpl.tex` exists, it is used as the pandoc LaTeX template.
Otherwise pandoc's built-in default LaTeX template is used.

Fails gracefully:
- If pandoc is not installed: prints a clear message, exits 2, leaves Markdown
  outputs untouched.
- If pandoc exists but --pdf was requested and no LaTeX engine is present:
  prints a clear message, exits 3, the `.tex` output is still produced.

Security design
---------------
- All subprocess calls use an explicit argument list (never a shell string).
- shell=False is set explicitly on every subprocess.run() call to prevent
  command injection — even if a future refactor inadvertently passes a string.
- All file paths are validated via _validate_path() to ensure they resolve
  strictly within an allowed base directory, preventing path-traversal attacks.
- Only the fixed executable "pandoc" is ever launched; no user-supplied
  executable is accepted.

Usage:
    python scripts/export_latex.py --desk desk/
    python scripts/export_latex.py --desk desk/ --pdf
    python scripts/export_latex.py --input desk/final/manuscript.md \\
                                   --output desk/final/manuscript.tex
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".md", ".tex", ".pdf", ".bib"})


def _validate_path(path: Path, base: Path, label: str = "path") -> Path:
    """Resolve *path* and assert it is strictly inside *base*.

    Raises ValueError if the resolved path escapes *base* (path-traversal
    protection) or if it has an unexpected file extension.
    """
    resolved = path.resolve()
    base_resolved = base.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"Security: {label} '{path}' resolves to '{resolved}' which is "
            f"outside the allowed base directory '{base_resolved}'."
        ) from exc
    if resolved.suffix not in _ALLOWED_EXTENSIONS and resolved.suffix != "":
        raise ValueError(
            f"Security: {label} '{path}' has disallowed extension '{resolved.suffix}'. "
            f"Allowed: {sorted(_ALLOWED_EXTENSIONS)}"
        )
    return resolved


def _pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


# ---------------------------------------------------------------------------
# Core export logic
# ---------------------------------------------------------------------------


def export(
    md_path: Path,
    tex_path: Path,
    template: Path | None,
    bib: Path | None,
    pdf: bool,
    base: Path | None = None,
) -> int:
    """Convert *md_path* to LaTeX (and optionally PDF) via pandoc.

    Parameters
    ----------
    md_path:  Resolved path to the input Markdown manuscript.
    tex_path: Desired output .tex path.
    template: Optional pandoc LaTeX template path.
    bib:      Optional BibTeX file path.
    pdf:      If True, also build a PDF via pandoc --pdf-engine=xelatex.
    base:     Base directory used for path-traversal validation.
              Defaults to md_path.parent when not provided.
    """
    # ---- path validation ---------------------------------------------------
    if base is None:
        base = md_path.parent
    # Validate every external path to prevent traversal attacks.
    md_path = _validate_path(md_path, base, label="--input")
    tex_path = _validate_path(tex_path, base, label="--output")
    if template is not None:
        template = _validate_path(template, base, label="--template")
    if bib is not None:
        bib = _validate_path(bib, base, label="--bib")

    # ---- availability checks -----------------------------------------------
    if not _pandoc_available():
        print(
            "pandoc not found on PATH.\n"
            "  Markdown output preserved at: " + str(md_path) + "\n"
            "  Install pandoc (https://pandoc.org) to produce a LaTeX export, "
            "or skip this step — the Markdown manuscript is canonical.",
            file=sys.stderr,
        )
        return 2

    if not md_path.exists():
        print(f"Error: manuscript not found: {md_path}", file=sys.stderr)
        return 1

    tex_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- build pandoc md → tex command ------------------------------------
    # Security: arguments are always passed as a list; shell=False is explicit.
    cmd: list[str] = [
        "pandoc",
        str(md_path),
        "-f",
        "markdown",
        "-t",
        "latex",
        "--standalone",
        "-o",
        str(tex_path),
    ]
    if template is not None and template.exists():
        cmd.extend(["--template", str(template)])
        print(f"  Using LaTeX template: {template}")
    else:
        print("  Using pandoc default LaTeX template (no desk/inputs/tmpl.tex present)")
    if bib is not None and bib.exists():
        cmd.extend(["--citeproc", "--bibliography", str(bib)])

    print("  Running:", " ".join(cmd))
    result = subprocess.run(  # noqa: S603 — list args, shell=False, no user exec
        cmd,
        capture_output=True,
        text=True,
        shell=False,  # explicit: prevent injection even if cmd becomes a str
    )
    if result.returncode != 0:
        print("✗ pandoc export failed:", file=sys.stderr)
        sys.stderr.write(result.stderr)
        return result.returncode
    print(f"✓ Wrote LaTeX: {tex_path}")

    if not pdf:
        return 0

    # ---- build pandoc md → pdf command ------------------------------------
    pdf_path = tex_path.with_suffix(".pdf")
    pdf_cmd: list[str] = [
        "pandoc",
        str(md_path),
        "-o",
        str(pdf_path),
        "--pdf-engine=xelatex",
    ]
    if template is not None and template.exists():
        pdf_cmd.extend(["--template", str(template)])
    if bib is not None and bib.exists():
        pdf_cmd.extend(["--citeproc", "--bibliography", str(bib)])

    if shutil.which("xelatex") is None and shutil.which("pdflatex") is None:
        print(
            "⚠ No LaTeX engine (xelatex/pdflatex) found. Skipping PDF build.\n"
            "  The .tex export is still available at: " + str(tex_path),
            file=sys.stderr,
        )
        return 3

    print("  Running:", " ".join(pdf_cmd))
    pdf_result = subprocess.run(  # noqa: S603 — list args, shell=False, no user exec
        pdf_cmd,
        capture_output=True,
        text=True,
        shell=False,  # explicit: prevent injection even if pdf_cmd becomes a str
    )
    if pdf_result.returncode != 0:
        print("✗ pandoc PDF build failed:", file=sys.stderr)
        sys.stderr.write(pdf_result.stderr)
        return pdf_result.returncode
    print(f"✓ Wrote PDF:   {pdf_path}")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Markdown manuscript to LaTeX via pandoc")
    parser.add_argument("--desk", type=str, help="Desk directory (looks for final/manuscript.md)")
    parser.add_argument("--input", type=str, help="Explicit input Markdown path")
    parser.add_argument("--output", type=str, help="Explicit output .tex path")
    parser.add_argument("--template", type=str, help="Explicit pandoc LaTeX template path")
    parser.add_argument("--bib", type=str, help="Explicit BibTeX path (defaults to desk/refs.bib)")
    parser.add_argument("--pdf", action="store_true", help="Also build a PDF via pandoc")
    args = parser.parse_args()

    if args.input:
        md = Path(args.input).resolve()
        tex = Path(args.output).resolve() if args.output else md.with_suffix(".tex")
        template = Path(args.template).resolve() if args.template else None
        bib = Path(args.bib).resolve() if args.bib else None
        base = md.parent
    else:
        if not args.desk:
            print("Error: provide --desk or --input", file=sys.stderr)
            sys.exit(2)
        desk = Path(args.desk).resolve()
        md = desk / "final" / "manuscript.md"
        tex = desk / "final" / "manuscript.tex"
        template = desk / "inputs" / "tmpl.tex"
        bib = desk / "refs.bib"
        base = desk

    sys.exit(export(md, tex, template, bib, args.pdf, base=base))


if __name__ == "__main__":
    main()
