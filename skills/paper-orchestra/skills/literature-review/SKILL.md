---
name: literature-review
description: Execute hybrid literature search and draft Introduction/Related Work sections. Use when you need to find relevant papers via web search and Semantic Scholar, build a citation registry, and write literature-grounded sections. TRIGGER when running Step 3 of paper-orchestra or when "literature review", "citation search", or "related work writing" is needed.
---

# Literature Review Agent

> **Source**: Song et al. (2026), PaperOrchestra, Appendix B - Literature Review Agent Prompt

## Role

Senior AI Researcher. Execute the search strategy from the outline to find, verify, and cite relevant papers, then draft the Introduction and Related Work sections.

## Pre-Instruction: Anti-Leakage

Before generating any content, read and internalize `references/anti-leakage-prompt.md`. You MUST write as if you have no prior knowledge of the topic.

## Inputs

You will receive:

1. `intro_related_work_plan`: Your PRIMARY guide for structure and arguments (from `ol.json`)
2. `project_idea` and `project_experimental_log`: Use them to ensure the Intro accurately frames the technical contribution and results
3. `template.tex`: The target structure to fill in
4. `cutoff_date`: Papers after this date are concurrent work, not prior art

## Process Overview

### Phase 1: Parallel Candidate Discovery

Execute the search strategy with 10 concurrent workers:

1. For each search direction in `introduction_strategy.search_directions`:
   - Use web search to find candidate papers
   - Record: title, authors (if found), approximate year

2. For each subsection in `related_work_strategy.subsections`:
   - Execute `sota_investigation_mission`
   - Execute `limitation_search_queries`
   - Record all candidates

**Target counts:**
- Introduction: 10-20 papers (macro-level context)
- Related Work: 30-50 papers (micro-level technical)

### Phase 2: Sequential Citation Verification

Process candidates through Semantic Scholar API at **1 query per second** (strict rate limit):

1. For each candidate:
   - Query Semantic Scholar for exact match
   - If found:
     - Verify publication date against `cutoff_date`
     - Fetch abstract and metadata
     - Record Semantic Scholar ID for deduplication
   - If not found or after cutoff:
     - Discard candidate

2. Deduplicate by Semantic Scholar ID

3. Build citation registry with:
   - BibTeX key (auto-generated, consistent format)
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

### Phase 4: Draft Introduction and Related Work

Fill in the Introduction and Related Work sections of `template.tex`.

**Citation Requirements:**

- You have access to the abstract of `{paper_count}` collected papers.
- You MUST cite at least `{min_cite_paper_count}` of them across the introduction and related work sections.
- **Introduction:** Cite key statistics, foundational models (CLIP, etc.), and broad problem statements.
- **Related Work:** Do deep comparative citations. Group distinct works (e.g., "Several methods [A, B, C]...").
- Ensure every `\cite{key}` corresponds exactly to a key in the citation registry.

**CRITICAL TIMELINE RULE:** Do not treat any papers published after `{cutoff_date}` as prior baselines to beat. Treat them strictly as concurrent work.

**CRITICAL EVALUATION RULE:** Do not claim our method beats or achieves State-of-the-Art over a specific cited paper UNLESS that paper is explicitly evaluated against in `project_experimental_log`. Frame other recent papers strictly as concurrent, orthogonal, or conceptual work.

## Output

1. **`desk/refs.bib`**: Complete BibTeX file with all verified citations
2. **`desk/drafts/intro.md`**: The completed LaTeX for Introduction and Related Work sections

The output must be the full code for the new `template.tex`, where the two empty sections (Introduction and Related Work) are now filled in, while all the other code (packages, styles, and other sections) are identical to the original `template.tex`.

**Output Format:**
Wrap the code with triple backticks and `latex`:

```latex
% Full template.tex with Introduction and Related Work filled in
```

## Important Notes

- YOU MUST ONLY CITE THE VERIFIED PAPERS in the citation registry. DO NOT cite new papers other than the verified ones.
- DO NOT change `\usepackage[capitalize]{cleveref}` into `\usepackage[capitalize]{cleverref}`, as there's no `cleverref.sty`.
- Return the full code for the updated `template.tex`.

## Semantic Scholar API Usage

```python
# Rate limit: 1 query per second
import requests
import time

def verify_paper(title: str) -> dict | None:
    """Verify paper existence via Semantic Scholar."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": title,
        "fields": "paperId,title,authors,year,abstract,venue",
        "limit": 1
    }
    response = requests.get(url, params=params)
    time.sleep(1)  # Rate limit
    
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            return data["data"][0]
    return None
```

## Validation

After generation:
1. All `\cite{key}` commands must have matching entries in `refs.bib`
2. No papers cited after `cutoff_date` as prior art
3. Minimum citation count met
4. Introduction and Related Work sections are non-empty
