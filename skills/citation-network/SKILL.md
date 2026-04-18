---
description: >
  Build and visualize multi-level citation networks from seed papers (DOIs or titles).
  Resolves seeds via Semantic Scholar, crawls references and citations to 2 levels,
  computes centrality metrics, and generates an interactive HTML report with vis.js
  network graph, timeline view, and cluster analysis.
  Use when the user wants to map a research landscape, find seminal/bridge papers,
  discover citation clusters, or visualize how papers connect across a field.
  Do NOT use for simple literature search or reading summaries — use lit-search instead.
  Do NOT use for verifying a single citation or formatting references — use cite-verify instead.
  Do NOT use for systematic review or PRISMA workflows — use systematic-review instead.
---

Build a citation network from "$ARGUMENTS".

Input formats accepted:
- One or more DOIs: `"10.1038/s41586-023-06221-2"`
- Paper titles: `"Attention is All You Need"`
- Mixed: `"10.1038/... + transformer architecture survey"`

## ARCHITECTURE

```
Main Session — coordination
  │
  ├── STEP 1: Resolve seed papers
  ├── STEP 2: Subagent → build citation network (2-level max)
  ├── STEP 3: Compute network insights
  ├── STEP 4: Report subagent → interactive HTML visualization
  └── STEP 5: Critic → validate HTML report (max 2 rounds)
```

## STEP 1 — Resolve Seed Papers

1. Parse `$ARGUMENTS` to extract individual DOIs and/or titles.
2. For each input, run the seed resolver script:
   ```
   python scripts/resolve_seed.py --doi "{doi}"
   python scripts/resolve_seed.py --title "{title}"
   ```
3. If the script fails, attempt manual resolution via WebFetch using the endpoints in `references/api-reference.md`.
4. For each resolved paper, fetch full data with references and citations:
   ```
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/{paperId}?fields=paperId,title,authors,year,venue,citationCount,externalIds,references.paperId,references.title,references.authors,references.year,references.citationCount,references.externalIds,citations.paperId,citations.title,citations.authors,citations.year,citations.citationCount,citations.externalIds
   ```
5. Wait ≥1 second between Semantic Scholar API calls.
6. Collect all seed paper data into a JSON array for STEP 2.

## STEP 2 — Build Network (subagent)

1. Launch a subagent with the prompt from `references/network-builder-prompt.md`.
2. Pass the seed paper JSON from STEP 1 as `{seed_paper_data}`.
3. The subagent will crawl references and citations, LIMIT to 2 levels from any seed.
4. The subagent returns a JSON object with `nodes`, `edges`, `clusters`, `key_papers`, `foundational_works`, and `recent_frontier`.
5. Save the returned JSON to a temporary file for STEP 3.

## STEP 3 — Compute Network Insights

1. Save the subagent's `nodes` and `edges` arrays to temporary JSON files.
2. Run the network statistics script:
   ```
   python scripts/network_stats.py --nodes nodes.json --edges edges.json
   ```
3. The script outputs JSON with `key_papers`, `bridges`, `clusters`, `degree_centrality`, and `betweenness_centrality`.
4. Merge script output with the subagent's cluster and frontier data.
5. Compile final insights:
   - **Seminal papers**: highest citation count, referenced by most seeds.
   - **Bridge papers**: high betweenness centrality, connect different clusters.
   - **Rising stars**: low total citations but published in last 2 years with growing citation rate.
   - **Research front**: newest papers citing the seeds.

## STEP 4 — HTML Visualization (report subagent)

1. Read the design system from `skills/shared/report-template.md` and follow it EXACTLY.
2. Do NOT use Tailwind CDN. Use the custom CSS variables, Crimson Pro font, and academic book aesthetic defined in the design system.
3. Generate the file at: `reports/{YYYY-MM-DD}-citation-network-{topic-slug}.html`
4. The HTML report MUST include all sections below.

### 4a. vis.js Network Graph

Use this HTML skeleton for the network graph section:

```html
<!-- vis.js CDN -->
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

<div id="network-graph" style="width: 100%; height: 600px; border: 1px solid var(--color-border);"></div>

<script>
  const nodes = new vis.DataSet([
    // {id: "paperId", label: "Short Title", size: citationCount_scaled, shape: "dot|star",
    //  color: {background: "cluster_color"}, title: "Full Title (Year)\nAuthors\nCitations: N"}
  ]);
  const edges = new vis.DataSet([
    // {from: "source_id", to: "target_id", arrows: "to"}
  ]);
  const container = document.getElementById("network-graph");
  const data = {nodes: nodes, edges: edges};
  const options = {
    physics: {barnesHut: {gravitationalConstant: -3000, springLength: 150}},
    interaction: {hover: true, tooltipDelay: 100},
    nodes: {font: {size: 12, face: "Crimson Pro, serif"}},
    edges: {color: {opacity: 0.4}, smooth: {type: "continuous"}}
  };
  const network = new vis.Network(container, data, options);

  // Click handler: show details panel
  network.on("click", function(params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const node = nodes.get(nodeId);
      document.getElementById("detail-panel").innerHTML =
        "<h3>" + node.fullTitle + "</h3>" +
        "<p>" + node.authors + " (" + node.year + ")</p>" +
        "<p>Citations: " + node.citations + "</p>" +
        "<p>Role: " + node.role + "</p>";
    }
  });
</script>
<div id="detail-panel" class="card"></div>
```

**Node rendering rules:**
- Scale node `size` from 10 (min citations) to 50 (max citations), logarithmic.
- Seed papers: `shape: "star"`, highlighted color.
- Key papers: `shape: "dot"`, large size.
- Bridge papers: `shape: "diamond"`.
- Peripheral papers: `shape: "dot"`, small, muted color.
- Color nodes by cluster membership.

### 4b. Timeline View

- Horizontal axis: publication year.
- Papers as dots positioned by year, connected by citation arrows.
- Colored by cluster (same palette as network graph).

### 4c. Key Papers Table

```html
<table>
  <thead>
    <tr><th>#</th><th>Title</th><th>Authors</th><th>Year</th><th>Citations</th><th>Role</th><th>Cluster</th></tr>
  </thead>
  <tbody>
    <!-- Populate from key_papers + bridges -->
  </tbody>
</table>
```

### 4d. Cluster Summary Cards

- One card per cluster with name, description, paper count, and top 3 papers.

### 4e. Statistics Bar

- Total papers in network.
- Date range (earliest year — latest year).
- Most prolific authors (top 5).
- Most common venues (top 5).

### 4f. Deliver Report

1. After writing the file, pass the file path to STEP 5 for validation.

## STEP 5 — Critic Validation (max 2 rounds)

Validate the HTML report for completeness and vis.js correctness. Pattern inspired by PapervizAgent's Critic-Visualizer loop (`paperviz_processor.py:60-100`).

1. Run the validation script:
   ```
   python scripts/validate_network.py --report {file_path} --seeds "{seed_id_1},{seed_id_2}"
   ```
2. Review the JSON output. The script checks:
   - vis.js CDN loaded
   - vis.DataSet initialization for nodes and edges
   - Network container div present
   - Node and edge data present (>0 each)
   - All seed papers included in the network
   - Physics/layout configuration set
   - Crimson Pro font loaded (design system)
   - No Tailwind CDN
   - Click handler for node detail panel
   - Key papers table present
   - Cluster/component information present

3. If all checks pass → deliver report to user.
4. If any checks fail:
   - Read the `failures` from the script output.
   - Revise the HTML to fix each failure.
   - Re-run the validation script.
   - Max 2 rounds. After 2 rounds, deliver with caveats noting unresolved issues.

5. After validation passes (or max rounds reached):
   - Return the exact absolute file path to the user.
   - Ask whether the user wants it opened.
   - Only run `open {file_path}` after the user explicitly confirms.

## ERROR HANDLING

1. **Seed paper not found in Semantic Scholar:**
   - First retry with title search if DOI was used (or vice versa).
   - If still not found, try OpenAlex as fallback: `GET https://api.openalex.org/works/https://doi.org/{doi}`.
   - If all fail, report which seed could not be resolved and proceed with remaining seeds.
   - See `references/api-reference.md` for OpenAlex endpoint details.

2. **Paper has >500 citations:**
   - Truncate to top 200 citations sorted by citation count.
   - Add a truncation note in the report: "This paper had N citations; showing top 200."
   - Never attempt to fetch all citations for a paper with >500.

3. **vis.js CDN unavailable:**
   - Detect load failure with an `onerror` handler on the script tag.
   - Fall back to a static HTML table listing all nodes and edges.
   - Add a note: "Interactive graph unavailable — showing static table."

4. **Rate limited by Semantic Scholar (HTTP 429):**
   - Apply exponential backoff: wait 2s → 4s → 8s → 16s → 32s → 60s max.
   - After 5 consecutive 429 responses, pause for 60 seconds.
   - If still blocked after 3 minutes total wait, skip remaining API calls and proceed with data collected so far.

5. **Circular citations (A cites B AND B cites A):**
   - Mark the edge as `"bidirectional": true` in the edge list.
   - Render with double-headed arrow in vis.js: `{arrows: "to;from"}`.

6. **Network too large (>300 nodes):**
   - Prune peripheral nodes (degree 1) that are not seeds.
   - Keep all seed, key, and bridge nodes.
   - Note the pruning in the report statistics.

## TOKEN BUDGET

| Phase | Estimated Tokens |
|---|---|
| Main (seed resolution) | ~5K |
| Network subagent | ~20–40K |
| Visualization subagent | ~10K |
| **Total** | **~35–55K** |

LIMIT crawl depth to 2 levels from any seed paper. Do NOT exceed this.

## REPORT DESIGN

Read and follow the design system in `skills/shared/report-template.md` EXACTLY.
Do NOT use Tailwind CDN. Use the custom CSS variables, Crimson Pro font, and academic book aesthetic defined there.
