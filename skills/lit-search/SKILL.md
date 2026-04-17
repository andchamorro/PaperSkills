---
name: lit-search
description: Search academic literature across Semantic Scholar, OpenAlex, PubMed, and arXiv. Returns deduplicated, ranked results with abstracts and open access status. Use this skill whenever the user wants to find academic papers, search scholarly databases, locate relevant research, explore what's been published on a topic, or discover recent work in a field. This skill handles multi-API querying, DOI-based deduplication, relevance ranking by citation impact, and presents results in a clear table format with next-action suggestions. It does NOT use subagents — executes directly.
---

# Literature Search

Search academic literature for "$ARGUMENTS".

## When to Use this skill

- User asks to "search for papers on X", "find academic literature about Y", "what's been published on Z"
- User wants to explore a research topic, find key papers, or get a literature overview
- User mentions specific APIs (Semantic Scholar, OpenAlex, PubMed, arXiv) or wants database coverage
- User asks for "recent papers", "highly cited works", or "open access versions"
- User wants to build a bibliography, start a literature review, or find gap candidates

## Quick Usage

**Step 1: Generate queries** — From "$ARGUMENTS", create 3-5 search variants:
- Original query as-is
- Synonyms and related terms
- Broader category
- More specific sub-topic

**Step 2: Detect discipline** — Infer from query:
- Medical/bio → include PubMed
- CS/math/physics → include arXiv
- Social sciences/humanities → Semantic Scholar + OpenAlex
- Unclear → Semantic Scholar + OpenAlex (always)

**Step 3: Search APIs** — Use parallel WebFetch calls:

| API | Endpoint | When |
|-----|----------|------|
| Semantic Scholar | `https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=20&fields=title,authors,year,venue,citationCount,abstract,externalIds,openAccessPdf` | Always |
| OpenAlex | `https://api.openalex.org/works?search={query}&per_page=20&sort=cited_by_count:desc&mailto=paperskills@example.com` | Always |
| PubMed | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=20&retmode=json` | Biomedical only |
| arXiv | `https://export.arxiv.org/api/query?search_query=all:{query}&max_results=20&sortBy=relevance` | CS/Math/Physics only |

**Step 4: Deduplicate and merge**
- Normalize DOIs (lowercase, strip URL prefix)
- Group by DOI — keep richest metadata
- No DOI: fuzzy match by title (>80% similarity)
- Keep one record per paper

**Step 5: Rank and present**

Sort by: `relevance score × log(citationCount + 1)`

Display as a markdown table:

```
| # | Authors | Title | Year | Venue | Cites | DOI | OA |
|---|---------|-------|------|-------|-------|-----|----|
| 1 | Smith, Jones | Deep learning for... | 2023 | Nature | 1,204 | 10.1038/... | PDF |
```

Show top 20. For papers with abstracts, show first 100 words in italics below.

## Error Handling

| Error | Handling |
|-------|----------|
| 429 rate limit | Wait 60s, retry once. If persistent, skip that API and note in output |
| 0 results on all APIs | Suggest broader search terms |
| Non-Latin script | Try transliterated version |
| arXiv XML parse error | Skip, note in output |
| API timeout | Log error, try alternative API |

## Next Actions

Offer after presenting results:

1. "Expand any of these? I can fetch full details + references."
2. "Build a citation network?" → `/citation-network DOI1 DOI2`
3. "Generate a literature review outline from these?"
4. "Save results to markdown table?"
5. "Find papers that cite a specific paper?"

## API Reference

For detailed endpoint documentation, see `references/api-reference.md`.

## Token Budget

- Direct execution (no subagent): ~15-25K total
- API responses: ~1-2K per call
- Abstract display: ~5K if all 20 shown