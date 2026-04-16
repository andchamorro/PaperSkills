#!/usr/bin/env python3
"""
snapshot.py - Create provenance snapshot with file hashes.

Captures SHA-256 hashes of all inputs and outputs for reproducibility tracking.

Usage:
    python scripts/snapshot.py --desk desk/
    python scripts/snapshot.py --desk desk/ --output desk/provenance.json
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def hash_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_directory(dirpath: Path) -> Dict[str, str]:
    """Compute hashes for all files in a directory."""
    hashes = {}
    if dirpath.exists() and dirpath.is_dir():
        for filepath in sorted(dirpath.rglob("*")):
            if filepath.is_file():
                rel_path = filepath.relative_to(dirpath)
                hashes[str(rel_path)] = hash_file(filepath)
    return hashes


def create_provenance(desk: Path) -> Dict:
    """
    Create a provenance snapshot of the desk.

    Returns:
        Dictionary with all file hashes and metadata
    """
    provenance = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "desk_path": str(desk.absolute()),
        "inputs": {},
        "outputs": {},
    }

    # Input files
    input_files = [
        "inputs/idea.md",
        "inputs/log.md",
        "inputs/tmpl.md",
        "inputs/gl.md",
    ]

    for rel_path in input_files:
        filepath = desk / rel_path
        if filepath.exists():
            provenance["inputs"][rel_path] = hash_file(filepath)
        else:
            provenance["inputs"][rel_path] = None

    # Input directories
    for dirname in ["inputs/fig", "inputs/ref"]:
        dirpath = desk / dirname
        if dirpath.exists() and dirpath.is_dir():
            provenance["inputs"][dirname] = hash_directory(dirpath)

    # Outline
    outline_path = desk / "ol.json"
    if outline_path.exists():
        provenance["outputs"]["outline"] = hash_file(outline_path)

    # Generated figures
    fig_dir = desk / "fig"
    if fig_dir.exists():
        provenance["outputs"]["figures"] = hash_directory(fig_dir)

    # References
    refs_path = desk / "refs.bib"
    if refs_path.exists():
        provenance["outputs"]["refs.bib"] = hash_file(refs_path)

    # Drafts
    drafts_dir = desk / "drafts"
    if drafts_dir.exists():
        provenance["outputs"]["drafts"] = hash_directory(drafts_dir)

    # Refinement iterations
    refin_dir = desk / "refin"
    if refin_dir.exists():
        provenance["outputs"]["refinement"] = hash_directory(refin_dir)

    # Final manuscript
    final_dir = desk / "final"
    if final_dir.exists():
        provenance["outputs"]["final"] = hash_directory(final_dir)

    # Worklog
    worklog_path = desk / "refin" / "worklog.json"
    if worklog_path.exists():
        provenance["outputs"]["worklog"] = hash_file(worklog_path)

    return provenance


def verify_provenance(desk: Path, provenance: Dict) -> Dict:
    """
    Verify current files against a provenance snapshot.

    Returns:
        Dictionary with verification results
    """
    results = {
        "verified": True,
        "timestamp_checked": datetime.now(timezone.utc).isoformat(),
        "original_timestamp": provenance.get("timestamp"),
        "mismatches": [],
        "missing": [],
        "new_files": [],
    }

    # Check input files
    for rel_path, expected_hash in provenance.get("inputs", {}).items():
        if expected_hash is None:
            continue
        if isinstance(expected_hash, dict):
            # It's a directory hash
            continue

        filepath = desk / rel_path
        if not filepath.exists():
            results["missing"].append(rel_path)
            results["verified"] = False
        else:
            actual_hash = hash_file(filepath)
            if actual_hash != expected_hash:
                results["mismatches"].append(
                    {
                        "path": rel_path,
                        "expected": expected_hash[:16] + "...",
                        "actual": actual_hash[:16] + "...",
                    }
                )
                results["verified"] = False

    return results


def main():
    parser = argparse.ArgumentParser(description="Create or verify provenance snapshot")
    parser.add_argument(
        "--desk", type=str, required=True, help="Path to the desk directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for provenance.json (default: desk/provenance.json)",
    )
    parser.add_argument(
        "--verify",
        type=str,
        default=None,
        help="Path to existing provenance.json to verify against",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )
    args = parser.parse_args()

    desk = Path(args.desk)

    if not desk.exists():
        print(f"Error: Desk directory does not exist: {desk}")
        return 1

    if args.verify:
        # Verification mode
        verify_path = Path(args.verify)
        if not verify_path.exists():
            print(f"Error: Provenance file not found: {verify_path}")
            return 1

        with open(verify_path) as f:
            provenance = json.load(f)

        results = verify_provenance(desk, provenance)

        if args.pretty:
            print(json.dumps(results, indent=2))
        else:
            if results["verified"]:
                print("✓ All files match provenance snapshot")
            else:
                print("✗ Verification failed:")
                for m in results["mismatches"]:
                    print(f"  - Modified: {m['path']}")
                for m in results["missing"]:
                    print(f"  - Missing: {m}")

        return 0 if results["verified"] else 1

    # Snapshot mode
    provenance = create_provenance(desk)

    output_path = Path(args.output) if args.output else desk / "provenance.json"

    with open(output_path, "w") as f:
        if args.pretty:
            json.dump(provenance, f, indent=2)
        else:
            json.dump(provenance, f)

    print(f"✓ Provenance snapshot saved to: {output_path}")

    # Summary
    input_count = len([k for k, v in provenance["inputs"].items() if v])
    output_sections = len(provenance["outputs"])
    print(f"  - {input_count} input files hashed")
    print(f"  - {output_sections} output sections captured")

    return 0


if __name__ == "__main__":
    exit(main())
