#!/usr/bin/env python3
"""Compute network statistics from citation graph nodes and edges.

Usage:
    python scripts/network_stats.py --nodes nodes.json --edges edges.json
    python scripts/network_stats.py --network network.json
    python scripts/network_stats.py --help

Input (--nodes + --edges):
    nodes.json: [{"id": "...", "title": "...", "year": 2023, "citationCount": 50, ...}]
    edges.json: [{"source": "id1", "target": "id2", "type": "cites", ...}]

Input (--network):
    network.json: {"nodes": [...], "edges": [...]}

Output: JSON on stdout with {total_nodes, total_edges, key_papers, bridges, clusters}.
Errors: Descriptive messages on stderr; exits with code 1 on failure.
"""

import argparse
import json
import sys
from collections import defaultdict


def _load_json(path: str) -> dict | list:
    """Load and parse a JSON file. Exit with descriptive error on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[network_stats] ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(
            f"[network_stats] ERROR: Invalid JSON in {path}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


def _build_adjacency(
    nodes: list[dict],
    edges: list[dict],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build outgoing and incoming adjacency sets from edge list."""
    outgoing = defaultdict(set)  # source -> {targets}
    incoming = defaultdict(set)  # target -> {sources}
    node_ids = {n["id"] for n in nodes}
    skipped = 0
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if src not in node_ids or tgt not in node_ids:
            skipped += 1
            continue
        outgoing[src].add(tgt)
        incoming[tgt].add(src)
    if skipped > 0:
        print(
            f"[network_stats] Warning: Skipped {skipped} edge(s) referencing unknown nodes.",
            file=sys.stderr,
        )
    return outgoing, incoming


def compute_degree_centrality(
    nodes: list[dict],
    outgoing: dict[str, set[str]],
    incoming: dict[str, set[str]],
) -> dict[str, float]:
    """Compute normalized degree centrality for each node.

    Degree centrality = (in_degree + out_degree) / (N - 1)
    """
    n = len(nodes)
    if n <= 1:
        return {node["id"]: 0.0 for node in nodes}
    centrality = {}
    for node in nodes:
        nid = node["id"]
        degree = len(outgoing.get(nid, set())) + len(incoming.get(nid, set()))
        centrality[nid] = degree / (n - 1)
    return centrality


def compute_betweenness_centrality(
    nodes: list[dict],
    outgoing: dict[str, set[str]],
    incoming: dict[str, set[str]],
) -> dict[str, float]:
    """Compute approximate betweenness centrality using BFS shortest paths.

    For large networks (>200 nodes), sample a subset of source nodes
    to keep computation tractable.
    """
    node_ids = [n["id"] for n in nodes]
    n = len(node_ids)
    if n <= 2:
        return {nid: 0.0 for nid in node_ids}

    # Build undirected adjacency for shortest-path computation
    adj = defaultdict(set)
    for nid in node_ids:
        for tgt in outgoing.get(nid, set()):
            adj[nid].add(tgt)
            adj[tgt].add(nid)
        for src in incoming.get(nid, set()):
            adj[nid].add(src)
            adj[src].add(nid)

    betweenness = defaultdict(float)

    # Sample sources for large graphs
    max_sources = min(n, 200)
    # Sort by degree descending to prioritize high-degree nodes in sampling
    sorted_nodes = sorted(
        node_ids,
        key=lambda x: len(adj.get(x, set())),
        reverse=True,
    )
    sources = sorted_nodes[:max_sources]

    for s in sources:
        # BFS from source s
        stack = []
        predecessors = defaultdict(list)
        sigma = defaultdict(int)  # number of shortest paths
        sigma[s] = 1
        dist = {s: 0}
        queue = [s]
        qi = 0
        while qi < len(queue):
            v = queue[qi]
            qi += 1
            stack.append(v)
            for w in adj.get(v, set()):
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist.get(w) == dist[v] + 1:
                    sigma[w] += sigma[v]
                    predecessors[w].append(v)

        delta = defaultdict(float)
        while stack:
            w = stack.pop()
            for v in predecessors[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                betweenness[w] += delta[w]

    # Normalize
    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    # Adjust for sampling
    if max_sources < n:
        scale *= n / max_sources
    return {nid: betweenness.get(nid, 0.0) * scale for nid in node_ids}


def detect_clusters_temporal(nodes: list[dict]) -> list[dict]:
    """Cluster papers by publication era."""
    import datetime

    current_year = datetime.datetime.now().year
    buckets = {
        "foundational": [],
        "established": [],
        "recent": [],
        "frontier": [],
    }
    for node in nodes:
        year = node.get("year")
        if year is None:
            buckets["established"].append(node["id"])
        elif year <= current_year - 10:
            buckets["foundational"].append(node["id"])
        elif year <= current_year - 3:
            buckets["established"].append(node["id"])
        elif year <= current_year - 1:
            buckets["recent"].append(node["id"])
        else:
            buckets["frontier"].append(node["id"])

    clusters = []
    descriptions = {
        "foundational": "Highly cited papers published >10 years ago — field foundations.",
        "established": "Papers from 3-10 years ago — core body of work.",
        "recent": "Papers from the last 1-3 years — active research front.",
        "frontier": "Papers from the current or past year — emerging work.",
    }
    for name, paper_ids in buckets.items():
        if paper_ids:
            clusters.append(
                {
                    "name": name,
                    "papers": paper_ids,
                    "description": descriptions[name],
                }
            )
    return clusters


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute citation network statistics (centrality, bridges, clusters).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/network_stats.py --nodes nodes.json --edges edges.json\n"
            "  python scripts/network_stats.py --network combined.json\n"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--network",
        type=str,
        help='Single JSON file with {"nodes": [...], "edges": [...]}.',
    )
    group.add_argument(
        "--nodes",
        type=str,
        help="JSON file containing the node list.",
    )
    parser.add_argument(
        "--edges",
        type=str,
        help="JSON file containing the edge list (required with --nodes).",
    )
    args = parser.parse_args()

    if args.network:
        data = _load_json(args.network)
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
    else:
        if not args.edges:
            print(
                "[network_stats] ERROR: --edges is required when using --nodes.",
                file=sys.stderr,
            )
            sys.exit(1)
        nodes = _load_json(args.nodes)
        edges = _load_json(args.edges)

    if not nodes:
        print("[network_stats] ERROR: Node list is empty.", file=sys.stderr)
        sys.exit(1)

    # Validate node structure
    for i, node in enumerate(nodes):
        if "id" not in node:
            print(
                f'[network_stats] ERROR: Node at index {i} missing "id" field.',
                file=sys.stderr,
            )
            sys.exit(1)

    print(
        f"[network_stats] Processing {len(nodes)} nodes, {len(edges)} edges...",
        file=sys.stderr,
    )

    outgoing, incoming = _build_adjacency(nodes, edges)
    degree = compute_degree_centrality(nodes, outgoing, incoming)
    betweenness = compute_betweenness_centrality(nodes, outgoing, incoming)

    # Key papers: top 10 by degree centrality
    sorted_by_degree = sorted(degree.items(), key=lambda x: x[1], reverse=True)
    key_papers = []
    node_map = {n["id"]: n for n in nodes}
    for nid, dc in sorted_by_degree[:10]:
        n = node_map[nid]
        key_papers.append(
            {
                "id": nid,
                "title": n.get("title", ""),
                "year": n.get("year"),
                "citationCount": n.get("citationCount", 0),
                "degreeCentrality": round(dc, 4),
                "betweennessCentrality": round(betweenness.get(nid, 0.0), 4),
            }
        )

    # Bridge papers: top by betweenness centrality (excluding top-3 degree nodes)
    top_degree_ids = {nid for nid, _ in sorted_by_degree[:3]}
    sorted_by_betweenness = sorted(
        betweenness.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    bridges = []
    for nid, bc in sorted_by_betweenness:
        if nid in top_degree_ids:
            continue
        if bc <= 0:
            break
        n = node_map[nid]
        bridges.append(
            {
                "id": nid,
                "title": n.get("title", ""),
                "year": n.get("year"),
                "betweennessCentrality": round(bc, 4),
            }
        )
        if len(bridges) >= 10:
            break

    # Temporal clusters
    clusters = detect_clusters_temporal(nodes)

    result = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "key_papers": key_papers,
        "bridges": bridges,
        "clusters": clusters,
        "degree_centrality": {nid: round(v, 4) for nid, v in sorted_by_degree},
        "betweenness_centrality": {
            nid: round(v, 4) for nid, v in sorted_by_betweenness if v > 0
        },
    }

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()  # trailing newline
    print(
        f"[network_stats] OK — {len(nodes)} nodes, {len(edges)} edges, "
        f"{len(key_papers)} key papers, {len(bridges)} bridges, "
        f"{len(clusters)} temporal clusters.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
