#!/usr/bin/env python3
"""Validate a citation network HTML report for completeness and vis.js correctness.

Checks that the generated HTML includes all seed papers, valid vis.js setup,
readable layout configuration, and correct node/edge data.

Usage:
    python scripts/validate_network.py --report reports/2026-04-17-citation-network-transformers.html
    python scripts/validate_network.py --report report.html --seeds "paperId1,paperId2"

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
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return False, "File is empty"
        return True, content
    except FileNotFoundError:
        return False, f"File not found: {path}"
    except UnicodeDecodeError:
        return False, "File is not valid UTF-8"


def validate_network(html: str, seed_ids: list[str] | None = None) -> dict:
    """Validate the citation network HTML report."""
    checks = []

    # Check 1: vis.js CDN present
    has_visjs = "vis-network" in html or "vis.Network" in html
    checks.append({
        "check": "vis.js CDN loaded",
        "passed": has_visjs,
        "issue": None if has_visjs else "vis-network script tag not found",
    })

    # Check 2: vis.DataSet nodes and edges
    has_nodes = "vis.DataSet" in html and "nodes" in html
    has_edges = "vis.DataSet" in html and "edges" in html
    checks.append({
        "check": "vis.DataSet for nodes and edges",
        "passed": has_nodes and has_edges,
        "issue": None if (has_nodes and has_edges) else "Missing vis.DataSet initialization for nodes/edges",
    })

    # Check 3: Network container div
    has_container = 'id="network-graph"' in html or 'id="network"' in html
    checks.append({
        "check": "Network container div present",
        "passed": has_container,
        "issue": None if has_container else "No network graph container div found",
    })

    # Check 4: Node count > 0
    node_matches = re.findall(r'\{[^}]*id:\s*["\']([^"\']+)["\']', html)
    has_nodes_data = len(node_matches) > 0
    checks.append({
        "check": "Node data present (>0 nodes)",
        "passed": has_nodes_data,
        "issue": None if has_nodes_data else "No node data found in vis.DataSet",
    })

    # Check 5: Edge data present
    edge_matches = re.findall(r'\{[^}]*from:\s*["\']([^"\']+)["\']', html)
    has_edges_data = len(edge_matches) > 0
    checks.append({
        "check": "Edge data present (>0 edges)",
        "passed": has_edges_data,
        "issue": None if has_edges_data else "No edge data found in vis.DataSet",
    })

    # Check 6: Seed papers included (if seed IDs provided)
    if seed_ids:
        missing_seeds = [sid for sid in seed_ids if sid not in html]
        all_seeds = len(missing_seeds) == 0
        checks.append({
            "check": "All seed papers included",
            "passed": all_seeds,
            "issue": None if all_seeds else f"Missing seed papers: {missing_seeds}",
        })

    # Check 7: Physics/layout configuration
    has_physics = "physics" in html or "barnesHut" in html or "forceAtlas" in html
    checks.append({
        "check": "Physics/layout configuration present",
        "passed": has_physics,
        "issue": None if has_physics else "No physics configuration for network layout",
    })

    # Check 8: Crimson Pro font (design system)
    has_font = "Crimson Pro" in html
    checks.append({
        "check": "Crimson Pro font loaded",
        "passed": has_font,
        "issue": None if has_font else "Crimson Pro font not loaded (design system requirement)",
    })

    # Check 9: No Tailwind CDN
    has_tailwind = "tailwindcss" in html.lower()
    checks.append({
        "check": "No Tailwind CDN",
        "passed": not has_tailwind,
        "issue": "Tailwind CDN found — must use custom CSS" if has_tailwind else None,
    })

    # Check 10: Click handler for detail panel
    has_click = "network.on" in html and "click" in html
    checks.append({
        "check": "Click handler for node details",
        "passed": has_click,
        "issue": None if has_click else "No click event handler for node detail panel",
    })

    # Check 11: Key papers table
    has_table = "<table" in html.lower() and ("key" in html.lower() or "核心" in html)
    checks.append({
        "check": "Key papers table present",
        "passed": has_table,
        "issue": None if has_table else "No key papers table found",
    })

    # Check 12: Disconnected components indication
    # Look for mentions of clusters or disconnected
    has_clusters = "cluster" in html.lower() or "集群" in html
    checks.append({
        "check": "Cluster/component information present",
        "passed": has_clusters,
        "issue": None if has_clusters else "No cluster or component information found",
    })

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    return {
        "passed": passed,
        "total": total,
        "all_passed": passed == total,
        "node_count": len(node_matches),
        "edge_count": len(edge_matches),
        "checks": checks,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate citation network HTML report")
    parser.add_argument("--report", required=True, help="Path to HTML report")
    parser.add_argument("--seeds", help="Comma-separated seed paper IDs (optional)")
    args = parser.parse_args()

    ok, result = check_file_readable(args.report)
    if not ok:
        print(json.dumps({"error": result}))
        sys.exit(1)

    seed_ids = args.seeds.split(",") if args.seeds else None
    validation = validate_network(result, seed_ids)
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    sys.exit(0 if validation["all_passed"] else 1)


if __name__ == "__main__":
    main()
