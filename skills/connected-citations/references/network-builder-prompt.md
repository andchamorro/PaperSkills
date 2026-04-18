# Network Builder — Subagent Prompt

Use this prompt verbatim when launching the network-building subagent in STEP 2.
Replace `{seed_paper_data}` with the JSON from STEP 1.

---

```
TASK: Build a citation network from seed papers.

SEED PAPERS (with references and citations already fetched):
{seed_paper_data}

PROCESS:

1. Extract each seed paper's references (backward citations) and citations (forward citations) into separate lists.

2. Identify OVERLAP papers — papers appearing in multiple seeds' reference or citation lists. These are KEY PAPERS in the field. Assign role "key" to any paper appearing in ≥2 seeds' lists.

3. For the top 10 most-connected papers (by combined in-degree + out-degree), fetch one additional level of references:
   WebFetch: https://api.semanticscholar.org/graph/v1/paper/{paperId}?fields=title,authors,year,citationCount,references.title,references.citationCount
   LIMIT: Do NOT go deeper than 2 levels from any seed paper.
   Wait ≥1 second between Semantic Scholar requests.

4. Cross-check with OpenCitations for additional edges (only for papers that have DOIs):
   WebFetch: https://opencitations.net/index/api/v2/citations/{doi}
   WebFetch: https://opencitations.net/index/api/v2/references/{doi}
   Merge any new edges not already captured from Semantic Scholar.

5. Handle edge cases:
   - If a paper has >500 citations, truncate to top 200 by citation count. Record truncation in the output.
   - If circular citations are detected (A cites B AND B cites A), mark the edge as bidirectional.
   - If rate-limited by any API, apply exponential backoff: wait 2s, 4s, 8s, up to 60s max.

6. Classify all papers by role:
   - "seed": Original input papers.
   - "key": Appears in ≥2 seeds' reference/citation lists.
   - "bridge": Connects two otherwise disconnected clusters (high betweenness centrality).
   - "peripheral": All other papers.

7. Identify temporal and thematic clusters:
   - Temporal: Group by publication decade (foundational ≤10yr ago vs. recent <2yr).
   - Thematic: Group by shared reference patterns or keyword overlap in titles.
   - Methodological: Group by shared methods if discernible from titles/abstracts.

OUTPUT FORMAT (strict JSON):
{
  "nodes": [
    {
      "id": "paperId or DOI",
      "title": "string",
      "authors": ["name1", "name2"],
      "year": 2023,
      "citationCount": 150,
      "role": "seed|key|bridge|peripheral",
      "cluster": "cluster_name"
    }
  ],
  "edges": [
    {
      "source": "id_of_citing_paper",
      "target": "id_of_cited_paper",
      "type": "cites",
      "bidirectional": false
    }
  ],
  "clusters": [
    {
      "name": "cluster_name",
      "papers": ["id1", "id2"],
      "description": "Brief description of what unites these papers"
    }
  ],
  "key_papers": ["id1", "id2", "...top 10 by connectivity"],
  "foundational_works": ["ids of highly cited papers >10 years old"],
  "recent_frontier": ["ids of papers from last 2 years with growing citations"],
  "truncation_notes": ["Paper X had 1200 citations, truncated to top 200"]
}
```
