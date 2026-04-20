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

Usage:
    python scripts/export_latex.py --desk desk/
    python scripts/export_latex.py --desk desk/ --pdf
    python scripts/export_latex.py --input desk/final/manuscript.md \
                                   --output desk/final/manuscript.tex
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def export(
    md_path: Path,
    tex_path: Path,
    template: Path | None,
    bib: Path | None,
    pdf: bool,
) -> int:
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

    cmd = [
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
    if template and template.exists():
        cmd.extend(["--template", str(template)])
        print(f"  Using LaTeX template: {template}")
    else:
        print("  Using pandoc default LaTeX template (no desk/inputs/tmpl.tex present)")
    if bib and bib.exists():
        cmd.extend(["--citeproc", "--bibliography", str(bib)])

    print("  Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("✗ pandoc export failed:", file=sys.stderr)
        sys.stderr.write(result.stderr)
        return result.returncode
    print(f"✓ Wrote LaTeX: {tex_path}")

    if not pdf:
        return 0

    pdf_path = tex_path.with_suffix(".pdf")
    pdf_cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(pdf_path),
        "--pdf-engine=xelatex",
    ]
    if template and template.exists():
        pdf_cmd.extend(["--template", str(template)])
    if bib and bib.exists():
        pdf_cmd.extend(["--citeproc", "--bibliography", str(bib)])

    if shutil.which("xelatex") is None and shutil.which("pdflatex") is None:
        print(
            "⚠ No LaTeX engine (xelatex/pdflatex) found. Skipping PDF build.\n"
            "  The .tex export is still available at: " + str(tex_path),
            file=sys.stderr,
        )
        return 3

    print("  Running:", " ".join(pdf_cmd))
    pdf_result = subprocess.run(pdf_cmd, capture_output=True, text=True)
    if pdf_result.returncode != 0:
        print("✗ pandoc PDF build failed:", file=sys.stderr)
        sys.stderr.write(pdf_result.stderr)
        return pdf_result.returncode
    print(f"✓ Wrote PDF:   {pdf_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Export Markdown manuscript to LaTeX via pandoc")
    parser.add_argument("--desk", type=str, help="Desk directory (looks for final/manuscript.md)")
    parser.add_argument("--input", type=str, help="Explicit input Markdown path")
    parser.add_argument("--output", type=str, help="Explicit output .tex path")
    parser.add_argument("--template", type=str, help="Explicit pandoc LaTeX template path")
    parser.add_argument("--bib", type=str, help="Explicit BibTeX path (defaults to desk/refs.bib)")
    parser.add_argument("--pdf", action="store_true", help="Also build a PDF via pandoc")
    args = parser.parse_args()

    if args.input:
        md = Path(args.input)
        tex = Path(args.output) if args.output else md.with_suffix(".tex")
        template = Path(args.template) if args.template else None
        bib = Path(args.bib) if args.bib else None
    else:
        if not args.desk:
            print("Error: provide --desk or --input", file=sys.stderr)
            sys.exit(2)
        desk = Path(args.desk)
        md = Path(args.input) if args.input else desk / "final" / "manuscript.md"
        tex = Path(args.output) if args.output else desk / "final" / "manuscript.tex"
        template = Path(args.template) if args.template else desk / "inputs" / "tmpl.tex"
        bib = Path(args.bib) if args.bib else desk / "refs.bib"

    sys.exit(export(md, tex, template, bib, args.pdf))


if __name__ == "__main__":
    main()
