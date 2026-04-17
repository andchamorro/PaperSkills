---
description: >-
  Find potentially missing references for an academic manuscript by searching
  Semantic Scholar, OpenAlex, and CrossRef. Detects gaps in the bibliography by
  comparing against the manuscript's topic and existing cited authors. Used by
  the peer-review orchestrator — do not invoke directly.
---

# Missing References Detector

Find potentially missing references for a manuscript about "{topic}".

**Input:** Manuscript topic (extracted from title/abstract), existing cited authors from manuscript

**Output:** Table of 15 potentially missing references ranked by relevance × citations

## Quick Usage

### 1. Extract Topic

From the manuscript's title and abstract, identify:
- Core research question
- Main methodology
- Key domain terms

### 2. Generate Search Queries

Create 3-5 query variants:
1. Core topic (exact)
2. Broader category
3. Methodology-focused
4. Recent developments (add "2022-2026")
5. Key author or theory

### 3. Search APIs (Parallel)

**Semantic Scholar:**
```
GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=20&fields=title,authors,year,venue,citationCount,abstract,externalIds
```

**OpenAlex:**
```
GET https://api.openalex.org/works?search={query}&per_page=20&sort=cited_by_count:desc&mailto=paperskills@example.com
```

**CrossRef:**
```
GET https://api.crossref.org/works?query={query}&rows=10&sort=relevance
```

### 4. Deduplicate

- Normalize DOIs (lowercase, strip URL prefix)
- Fuzzy match by title (>80% similarity) for papers without DOI
- Remove works already in manuscript bibliography

### 5. Rank and Filter

Sort by: `relevance score × log(citationCount + 1)`

Take top 15 that are:
- Not already cited
- Relevant to the topic
- From reputable sources

### 6. Output Table

```
| # | Author(s) | Title | Venue/Year | Citations | Why Relevant |
|---|-----------|-------|------------|-----------|--------------|
| 1 | Smith et al. | ... | Nature 2023 | 1,204 | Extends... |
```

Include brief "why relevant" note for each.

## Error Handling

| Error | Handling |
|-------|----------|
| 429 rate limit | Wait 60s, retry once |
| 0 results | Broaden query terms |
| API unavailable | Skip that API, use others |
| Cannot determine topic | Ask user for clarification |

## Output Fields

For each potential reference:
- **Author(s)**: First author + et al. if >3
- **Title**: Paper title
- **Venue/Year**: Journal/conference + year
- **Citations**: Citation count
- **Why Relevant**: 1-2 sentence explanation of how it relates to the manuscript

## Notes

- Focus on foundational papers (high citations) AND recent work (last 3 years)
- Include methodologically relevant papers even if topic slightly different
- Consider both positive citations (supporting) and critical citations (counterarguments)