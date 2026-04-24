---
name: literature-review
description: >-
  Execute hybrid literature search and draft Introduction/Related Work sections.
  Uses literature_scripts Python backend for querying academic databases
  (CrossRef, OpenAlex, arXiv), with DOI-based deduplication, citation-count
  ranking, and open-access detection. Builds a verified citation registry and
  drafts literature-grounded LaTeX sections. Use when running Step 3 of
  paper-orchestra, or standalone when the user asks to "search for papers",
  "find academic literature", "literature review", "citation search", or
  "related work writing". Do NOT use for citation verification (use
  citation_tool.py), citation networks (use connected-citations), or journal
  matching (use journal-match).
---

# Literature Review Agent

> **Source**: Song et al. (2026), PaperOrchestra, Appendix B — updated to use
> literature_scripts Python backend for secure, reliable querying.

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
3. `template.tex`: The target structure to fill in
4. `cutoff_date`: Papers after this date are concurrent work, not prior art

**When invoked standalone (as literature search):**

1. A search query or topic from the user
2. Optional: discipline hint, date range, output format preference
3. No `cutoff_date` or template — skip Phase 4, return results table instead

## Process Overview

### Phase 1: Script-Based Candidate Discovery

Execute search using **literature_scripts Python backend**. This replaces direct
API calls with secure, stdlib-based script invocations.

#### 1a. Generate Search Queries

From the outline's search directions (paper-orchestra) or the user query
(standalone), create 3-5 query variants:

- Original query / core topic
- Synonyms and related terms
- Broader category
- More specific sub-topic
- Methodology-focused variant (if applicable)

#### 1b. Detect Discipline → Select Scripts

| Signal | Scripts to include |
|--------|----------------|
| Medical / biomedical terms | **search_crossref.py** + **search_openalex.py** |
| CS / math / physics terms | **search_crossref.py** + **search_openalex.py** + **search_arxiv** (via OpenAlex) |
| Social sciences / humanities | **search_crossref.py** + **search_openalex.py** |
| Unclear / mixed | **search_crossref.py** + **search_openalex.py** (always) |

#### 1c. Script Execution Pattern

**Secure subprocess invocation using stdlib-based scripts:**

```
python skills/literature-review/scripts/search_openalex.py --query "QUERY" --max-results 20 --year-range 2020-2026 -o openalex_results.jsonl
python skills/literature-review/scripts/search_crossref.py --query "QUERY" --rows 20 -o crossref_results.jsonl
```

| Script | Flags | Rate Limit | Output |
|--------|-------|-----------|--------|
| **search_openalex.py** | `--query`, `--max-results`, `--year-range`, `--min-citations`, `--sort` | 100K/day | JSONL |
| **search_crossref.py** | `--query`, `--rows`, `--bibtex`, `--output` | 50 req/s | JSONL or .bib |

**Implementation pattern:**
- Execute scripts sequentially with proper rate limiting (scripts handle internally)
- On script error: log and continue with remaining scripts
- Parse JSONL output for results

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

### Phase 2: Citation Verification via Script

Process top candidates using script-based lookup:

1. For each candidate with DOI:
   - Query CrossRef for exact match and full metadata
   - Verify publication date against `cutoff_date` (paper-orchestra only)
   - Fetch abstract and full metadata
2. For papers without DOI:
   - Use OpenAlex to resolve by title
3. Final deduplication by DOI or Semantic Scholar ID
4. Build citation registry with:
   - BibTeX key (auto-generated: `AuthorYYYYKeyword`)
   - Full BibTeX entry (via `--bibtex` flag)
   - Abstract (for writing context)

### Phase 3: Generate BibTeX File

Use CrossRef script with `--bibtex` flag to generate `refs.bib`:

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

Fill in the Introduction and Related Work sections of `template.tex`.

**Citation Requirements:**

- You have access to the abstract of `{paper_count}` collected papers.
- You MUST cite at least `{min_cite_paper_count}` of them across the intro and related work.
- **Introduction:** Cite key statistics, foundational models, and broad problem statements.
- **Related Work:** Do deep comparative citations. Group distinct works (e.g., "Several methods [A, B, C]...").
- Ensure every `\cite{key}` corresponds exactly to a key in the citation registry.

**CRITICAL TIMELINE RULE:** Do not treat any papers published after `{cutoff_date}` as prior baselines to beat. Treat them strictly as concurrent work.

**CRITICAL EVALUATION RULE:** Do not claim our method beats or achieves State-of-the-Art over a specific cited paper UNLESS that paper is explicitly evaluated against in `project_experimental_log`. Frame other recent papers strictly as concurrent, orthogonal, or conceptual work.

## Output

**Paper-orchestra mode:**

1. **`desk/refs.bib`**: Complete BibTeX file with all verified citations
2. **`desk/drafts/intro.md`**: The completed LaTeX for Introduction and Related Work sections

The output must be the full code for the new `template.tex`, where the two
empty sections are now filled in, while all other code is identical to the
original `template.tex`.

**Output Format:**
```latex
% Full template.tex with Introduction and Related Work filled in
```

**Standalone mode:**

Return a markdown table:

```
| # | Authors | Title | Year | Venue | Cites | DOI | OA |
|---|---------|-------|------|-------|-------|-----|----|
| 1 | Smith et al. | Deep learning for... | 2023 | Nature | 1,204 | 10.1038/... | PDF |
```

Then offer next actions:
1. "Build a citation network?" �� `/connected-citations DOI1 DOI2`
2. "Find research gaps?" → `/research-gap {topic}`
3. "Save results to BibTeX?"

## Important Notes

- YOU MUST ONLY CITE THE VERIFIED PAPERS in the citation registry. DO NOT cite new papers other than the verified ones.
- DO NOT change `\usepackage[capitalize]{cleveref}` into `\usepackage[capitalize]{cleverref}`.
- Return the full code for the updated `template.tex`.

## Script Reference

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `scripts/search_openalex.py` | Search OpenAlex (broad coverage, free) | `--query`, `--max-results`, `--year-range`, `--min-citations`, `--sort`, `-o` |
| `scripts/search_crossref.py` | Search CrossRef (DOI lookup, BibTeX) | `--query`, `--rows`, `--bibtex`, `--output`, `-o` |
| `scripts/download_arxiv_source.py` | Download arXiv source | `--title`, `--arxiv-id`, `--max-results`, `--output-dir` |

## Validation

After generation:
1. All `\cite{key}` commands must have matching entries in `refs.bib`
2. No papers cited after `cutoff_date` as prior art
3. Minimum citation count met
4. Introduction and Related Work sections are non-empty

## Error Handling

| Error | Handling |
|-------|----------|
| Script timeout | Increase timeout, retry once. If persistent, skip script |
| 0 results from all scripts | Suggest broader search terms |
| Script parse error | Log error, continue with remaining scripts |
| Non-Latin script query | Try transliterated version alongside original |
| BibTeX key collision | Auto-suffix with letters (a, b, c...) |

## Token Budget

- Standalone search: ~15-25K
- Paper-orchestra mode: ~20-30K (includes LaTeX generation)
