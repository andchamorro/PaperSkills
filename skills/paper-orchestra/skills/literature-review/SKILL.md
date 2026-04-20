---
description: >-
  Execute hybrid literature search and draft Introduction/Related Work sections.
  Searches Semantic Scholar, OpenAlex, PubMed, and arXiv in parallel with
  DOI-based deduplication, citation-count ranking, and open-access detection.
  Builds a verified citation registry and drafts literature-grounded LaTeX
  sections. Use when running Step 3 of paper-orchestra, or standalone when the
  user asks to "search for papers", "find academic literature", "literature
  review", "citation search", or "related work writing". Do NOT use for
  citation verification (use citation_tool.py), citation networks
  (use connected-citations), or journal matching (use journal-match).
---

# Literature Review Agent

> **Source**: Song et al. (2026), PaperOrchestra, Appendix B — extended with
> multi-API parallel search from the former `lit-search` skill.

## Role

Senior AI Researcher. Execute the search strategy to find, verify, and cite
relevant papers, then draft the Introduction and Related Work sections.

## Pre-Instruction: Anti-Leakage

Before generating any content, read and internalize
`references/anti-leakage-prompt.md`. You MUST write as if you have no prior
knowledge of the topic.

## Inputs

**When invoked from paper-orchestra (Step 3):**

1. `intro_related_work_plan`: Your PRIMARY guide for structure and arguments (from `ol.json`)
2. `project_idea` and `project_experimental_log`: Use them to ensure the Intro accurately frames the technical contribution and results
3. `tmpl.md`: The target **Markdown** structure to fill in
4. `cutoff_date`: Papers after this date are concurrent work, not prior art

**When invoked standalone (as literature search):**

1. A search query or topic from the user
2. Optional: discipline hint, date range, output format preference
3. No `cutoff_date` or template — skip Phase 4, return results table instead

## Process Overview

### Phase 1: Parallel Multi-API Candidate Discovery

Execute search across multiple APIs using **parallel WebFetch calls** with
concurrency limits. This replaces the former sequential Semantic-Scholar-only
approach with the multi-API pattern from `lit-search`.

#### 1a. Generate Search Queries

From the outline's search directions (paper-orchestra) or the user query
(standalone), create 3-5 query variants:

- Original query / core topic
- Synonyms and related terms
- Broader category
- More specific sub-topic
- Methodology-focused variant (if applicable)

#### 1b. Detect Discipline → Select APIs

| Signal | APIs to include |
|--------|----------------|
| Medical / biomedical terms | Semantic Scholar + OpenAlex + **PubMed** |
| CS / math / physics terms | Semantic Scholar + OpenAlex + **arXiv** |
| Social sciences / humanities | Semantic Scholar + OpenAlex |
| Unclear / mixed | Semantic Scholar + OpenAlex (always) |

#### 1c. Parallel WebFetch Calls

Fire all API calls concurrently. Respect per-API rate limits:

| API | Endpoint | Rate Limit | Concurrency |
|-----|----------|------------|-------------|
| **Semantic Scholar** | `GET https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=20&fields=paperId,title,authors,year,venue,citationCount,abstract,externalIds,openAccessPdf` | 1 req/s | Serial |
| **OpenAlex** | `GET https://api.openalex.org/works?search={q}&per_page=20&sort=cited_by_count:desc&mailto=paperskills@example.com` | 10 req/s | Parallel OK |
| **PubMed** (if biomedical) | `GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={q}&retmax=20&retmode=json` then `GET /esummary.fcgi?db=pubmed&id={pmids}&retmode=json` | 3 req/s | Parallel OK |
| **arXiv** (if STEM) | `GET https://export.arxiv.org/api/query?search_query=all:{q}&max_results=20&sortBy=relevance` | 1 req/3s | Serial |

**Implementation pattern:**
- Group Semantic Scholar calls sequentially (1 QPS strict).
- Fire OpenAlex + PubMed + arXiv calls in parallel per query variant.
- On 429 (rate limit): back off 5s, retry once; if still failing, skip that API for the current query and note the gap.
- On timeout or error: skip that API call, continue with others.

#### 1d. Merge and Deduplicate

1. Normalize DOIs: lowercase, strip URL prefixes (`https://doi.org/`, `doi:`).
2. Group results by DOI — keep the record with the richest metadata.
3. For papers without DOI: fuzzy-match by title (>80% token overlap after lowercasing and stopword removal). Keep the higher-cited variant.
4. Keep one record per unique paper.

#### 1e. Rank Results

Sort by: `relevance_to_query × log(citationCount + 1)`

For paper-orchestra mode, separate into:
- **Introduction candidates**: 10-20 papers (macro-level context)
- **Related Work candidates**: 30-50 papers (micro-level technical)

For standalone mode:
- Return top 20 results as a ranked table.

**Target counts (paper-orchestra):**
- Introduction: 10-20 papers
- Related Work: 30-50 papers

### Phase 2: Sequential Citation Verification

Process top candidates through Semantic Scholar at **1 query per second**:

1. For each candidate:
   - Query Semantic Scholar for exact match (by DOI if available, else title)
   - If found:
     - Verify publication date against `cutoff_date` (paper-orchestra only)
     - Fetch abstract and full metadata
     - Record Semantic Scholar ID for final deduplication
   - If not found or after cutoff:
     - Discard candidate
2. Final deduplication by Semantic Scholar ID
3. Build citation registry with:
   - BibTeX key (auto-generated: `AuthorYYYYKeyword`)
   - Full BibTeX entry
   - Abstract (for writing context)

### Phase 3: Generate BibTeX File

Create `refs.bib` with all verified citations:

```bibtex
@inproceedings{AuthorYYYYKeyword,
  title = {Full Paper Title},
  author = {First Author and Second Author and Third Author},
  booktitle = {Proceedings of Conference},
  year = {YYYY},
  pages = {XXX--YYY}
}
```

### Phase 4: Draft Introduction and Related Work (paper-orchestra only)

**Skip this phase in standalone mode.** In standalone mode, present results as
a ranked markdown table and offer next actions (see Standalone Output below).

Fill in the Introduction and Related Work sections of `tmpl.md`, writing in
**pandoc-flavored Markdown**. Use pandoc citation syntax `[@Key]` / `[@Key1; @Key2]`
(not `\cite{}`).

**Citation Requirements:**

- You have access to the abstract of `{paper_count}` collected papers.
- You MUST cite at least `{min_cite_paper_count}` of them across the intro and related work.
- **Introduction:** Cite key statistics, foundational models, and broad problem statements.
- **Related Work:** Do deep comparative citations. Group distinct works (e.g., "Several methods [@KeyA; @KeyB; @KeyC]...").
- Ensure every `[@key]` corresponds exactly to a key in the citation registry.

**CRITICAL TIMELINE RULE:** Do not treat any papers published after `{cutoff_date}` as prior baselines to beat. Treat them strictly as concurrent work.

**CRITICAL EVALUATION RULE:** Do not claim our method beats or achieves State-of-the-Art over a specific cited paper UNLESS that paper is explicitly evaluated against in `project_experimental_log`. Frame other recent papers strictly as concurrent, orthogonal, or conceptual work.

## Output

**Paper-orchestra mode:**

1. **`desk/refs.bib`**: Complete BibTeX file with all verified citations
2. **`desk/drafts/intro.md`**: The Markdown for the Introduction and Related Work sections, ready to splice into `tmpl.md`.

The output must be the full Markdown for the two sections (Introduction and
Related Work) with pandoc `[@key]` citations, so that a downstream step can
concatenate it into the manuscript skeleton without further transformation.

**Output Format:**

````markdown
# Introduction

...text with [@Key] citations...

# Related Work

## 2.1 ...
...
````

**Standalone mode:**

Return a markdown table:

```
| # | Authors | Title | Year | Venue | Cites | DOI | OA |
|---|---------|-------|------|-------|-------|-----|----|
| 1 | Smith et al. | Deep learning for... | 2023 | Nature | 1,204 | 10.1038/... | PDF |
```

Then offer next actions:
1. "Build a citation network?" → `/connected-citations DOI1 DOI2`
2. "Find research gaps?" → `/research-gap {topic}`
3. "Save results to BibTeX?"

## Important Notes

- YOU MUST ONLY CITE THE VERIFIED PAPERS in the citation registry. DO NOT cite new papers other than the verified ones.
- Return the full Markdown for the Introduction and Related Work sections; do not wrap them in LaTeX preamble.

## API Reference

For detailed endpoint documentation, response formats, DOI normalization, and
deduplication logic, see `references/api-reference.md`.

## Validation

After generation:
1. All `[@key]` (and any legacy `\cite{key}`) references must have matching entries in `refs.bib`
2. No papers cited after `cutoff_date` as prior art
3. Minimum citation count met
4. Introduction and Related Work sections are non-empty

## Error Handling

| Error | Handling |
|-------|----------|
| 429 rate limit | Back off 5s, retry once. If persistent, skip API and note gap |
| 0 results on all APIs | Suggest broader search terms |
| Non-Latin script query | Try transliterated version alongside original |
| arXiv XML parse error | Skip arXiv results, note in output |
| API timeout | Skip that call, continue with remaining APIs |
| PubMed returns PMIDs but esummary fails | Keep PMIDs, mark metadata as partial |

## Token Budget

- Standalone search: ~15-25K
- Paper-orchestra mode: ~20-30K (includes LaTeX generation)
