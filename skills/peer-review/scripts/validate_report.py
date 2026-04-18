#!/usr/bin/env python3
"""Validate a peer review HTML report for completeness and consistency.

Performs structural checks on the generated HTML report to ensure all required
sections are present and data is consistent with the evaluator output.

Usage:
    python scripts/validate_report.py --report reports/2026-04-17-peer-review-example.html
    python scripts/validate_report.py --report report.html --evaluator evaluator_output.json

Output:
    JSON with check results to stdout. Exit code 0 if all pass, 1 if any fail.
"""

import argparse
import json
import re
import sys


def check_file_readable(path: str) -> tuple[bool, str]:
    """Check if the file exists and is readable."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return False, "File is empty"
        return True, content
    except FileNotFoundError:
        return False, f"File not found: {path}"
    except UnicodeDecodeError:
        return False, "File is not valid UTF-8"


def validate_report(html: str, evaluator_json: dict | None = None) -> dict:
    """Validate the HTML report and return check results."""
    checks = []

    # Check 1: Chart.js CDN present
    has_chartjs = "chart.js" in html.lower() or "Chart(" in html
    checks.append(
        {
            "check": "Chart.js CDN",
            "passed": has_chartjs,
            "issue": None if has_chartjs else "Chart.js script tag not found in report",
        }
    )

    # Check 2: Crimson Pro font
    has_font = "Crimson Pro" in html or "crimson-pro" in html.lower()
    checks.append(
        {
            "check": "Crimson Pro Font",
            "passed": has_font,
            "issue": None if has_font else "Crimson Pro font reference not found",
        }
    )

    # Check 3: No Tailwind CDN
    has_tailwind = "tailwindcss" in html.lower() or "tailwind.min" in html.lower()
    checks.append(
        {
            "check": "No Tailwind CDN",
            "passed": not has_tailwind,
            "issue": "Tailwind CDN found — must use custom CSS variables" if has_tailwind else None,
        }
    )

    # Check 4: All 8 K-criteria mentioned
    criteria = ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"]
    found_criteria = [k for k in criteria if k in html]
    all_criteria = len(found_criteria) == 8
    checks.append(
        {
            "check": "All 8 K-criteria present",
            "passed": all_criteria,
            "issue": (
                None if all_criteria else f"Missing criteria: {set(criteria) - set(found_criteria)}"
            ),
        }
    )

    # Check 5: Radar chart data array
    radar_match = re.search(r"data:\s*\[([^\]]+)\]", html)
    if radar_match:
        try:
            values = [float(v.strip()) for v in radar_match.group(1).split(",") if v.strip()]
            has_8_values = len(values) == 8
            in_range = all(1 <= v <= 5 for v in values)
            checks.append(
                {
                    "check": "Radar chart data (8 values, range 1-5)",
                    "passed": has_8_values and in_range,
                    "issue": (
                        None
                        if (has_8_values and in_range)
                        else f"Found {len(values)} values, range check: {in_range}"
                    ),
                }
            )
        except ValueError:
            checks.append(
                {
                    "check": "Radar chart data (8 values, range 1-5)",
                    "passed": False,
                    "issue": "Could not parse radar chart data values",
                }
            )
    else:
        checks.append(
            {
                "check": "Radar chart data (8 values, range 1-5)",
                "passed": False,
                "issue": "No Chart.js data array found in report",
            }
        )

    # Check 6: Recommendation badge
    rec_keywords = [
        "ACCEPT",
        "MINOR REVISIONS",
        "MAJOR REVISIONS",
        "REJECT",
        "接受",
        "小修",
        "大修",
        "拒绝",
    ]
    has_recommendation = any(kw in html.upper() for kw in [k.upper() for k in rec_keywords])
    checks.append(
        {
            "check": "Recommendation badge present",
            "passed": has_recommendation,
            "issue": None if has_recommendation else "No recommendation badge found",
        }
    )

    # Check 7: Language consistency
    lang_match = re.search(r'<html[^>]*lang="(\w+)"', html)
    lang = lang_match.group(1) if lang_match else "unknown"
    checks.append(
        {
            "check": "HTML lang attribute set",
            "passed": lang in ("en", "zh"),
            "issue": None if lang in ("en", "zh") else f"lang='{lang}' — expected 'en' or 'zh'",
        }
    )

    # Check 8: Missing references table
    has_table = "<table" in html.lower() and ("missing" in html.lower() or "参考" in html)
    checks.append(
        {
            "check": "Missing references table present",
            "passed": has_table,
            "issue": None if has_table else "No missing references table found",
        }
    )

    # Check 9: Validate against evaluator JSON if provided
    if evaluator_json:
        eval_title = evaluator_json.get("structural_analysis", {}).get("title", "")
        if eval_title and eval_title in html:
            checks.append(
                {
                    "check": "Title matches evaluator data",
                    "passed": True,
                    "issue": None,
                }
            )
        elif eval_title:
            checks.append(
                {
                    "check": "Title matches evaluator data",
                    "passed": False,
                    "issue": f"Evaluator title '{eval_title}' not found in report",
                }
            )

    # Summary
    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    return {
        "passed": passed,
        "total": total,
        "all_passed": passed == total,
        "checks": checks,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate peer review HTML report")
    parser.add_argument("--report", required=True, help="Path to HTML report")
    parser.add_argument("--evaluator", help="Path to evaluator JSON output (optional)")
    args = parser.parse_args()

    ok, result = check_file_readable(args.report)
    if not ok:
        print(json.dumps({"error": result}))
        sys.exit(1)

    evaluator_json = None
    if args.evaluator:
        try:
            with open(args.evaluator, encoding="utf-8") as f:
                evaluator_json = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load evaluator JSON: {e}", file=sys.stderr)

    validation = validate_report(result, evaluator_json)
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    sys.exit(0 if validation["all_passed"] else 1)


if __name__ == "__main__":
    main()
