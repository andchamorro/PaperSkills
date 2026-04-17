---
description: >-
  Find 3-5 similar peer reviews from the paper's field via Semantic Scholar to
  use as few-shot examples for the evaluator agent. Extracts field from the
  manuscript's title and abstract, searches for highly-cited review papers and
  editorial commentaries, and returns structured review summaries. Used by the
  peer-review orchestrator — do not invoke directly.
---

# Retriever Agent

Find similar peer reviews for a manuscript about "{topic}" in the field of "{field}".

**Input:** Manuscript title, abstract (first 300 words), and discipline
**Output:** 3-5 structured review examples as few-shot context for the evaluator

## Step 1 — Extract Field and Keywords

1. From the input title and abstract, identify:
   - Primary discipline (e.g., computer science, law, medicine)
   - Sub-field (e.g., NLP, criminal law theory, oncology)
   - 5-7 keywords relevant to the manuscript's topic
   - Methodology type (empirical, theoretical, review, mixed)

## Step 2 — Search for Similar Reviews

1. Construct 3 search queries:
   - `"{sub_field}" peer review criteria` — finds review methodology papers
   - `"{keyword_1} {keyword_2}" review evaluation` — finds domain-specific reviews
   - `"{discipline}" manuscript assessment quality` — finds editorial guidance
2. For each query, search Semantic Scholar:
   ```
   GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=20&fields=title,authors,year,venue,citationCount,abstract,tldr
   ```
3. Wait >=1 second between requests.
4. Filter results:
   - Prefer papers with "review", "evaluation", "assessment", or "peer review" in title or abstract
   - Prefer papers from the same discipline
   - Prefer highly cited papers (>50 citations)
   - Prefer papers from the last 10 years

## Step 3 — Rank and Select Top 3-5

1. Score each candidate: `relevance_to_field * log(citationCount + 1)`
   - `relevance_to_field`: 3 = same sub-field, 2 = same discipline, 1 = related discipline
2. Select top 3-5 by score.
3. For each selected paper, extract from the abstract/TLDR:
   - What criteria did this review use?
   - What was the review's methodology?
   - What scoring or evaluation framework was applied?

## Step 4 — Return Structured Examples

Return a JSON array:

```json
[
  {
    "id": "semantic_scholar_paper_id",
    "title": "Paper Title",
    "authors": "First Author et al.",
    "venue": "Journal Name",
    "year": 2024,
    "citations": 150,
    "review_methodology": "Multi-criteria evaluation with 6 dimensions...",
    "criteria_used": ["originality", "methodology", "significance", "clarity"],
    "relevance_note": "Same sub-field (NLP fairness), uses similar K-criteria framework"
  }
]
```

## Fallback Behavior

1. If Semantic Scholar returns 0 results for all queries:
   - Broaden to discipline-level queries (drop sub-field keywords).
   - Try searching for "{discipline} peer review guidelines" as a last resort.
2. If fewer than 3 results after broadening:
   - Return what was found with a note: `"coverage_warning": "Only {N} review examples found. Evaluator should rely on built-in criteria."`.
3. If Semantic Scholar is unavailable (429 or timeout):
   - Return an empty array with `"api_error": "Semantic Scholar unavailable. Evaluator proceeds without few-shot examples."`.
   - The pipeline continues — few-shot examples are optional enrichment, not a hard dependency.

## Error Handling

| Condition | Action |
|---|---|
| Empty title/abstract input | Return error: "Retriever requires title and abstract" |
| API rate limit (429) | Wait 5s, retry once; if still failing, return empty with warning |
| No results for any query | Broaden to discipline-level, then return partial or empty |
| Abstract too short to determine field | Use title keywords only; note reduced confidence |
