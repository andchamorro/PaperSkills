---
description: Identifies research gaps in a field using Semantic Scholar and OpenAlex trend data. Covers temporal, methodological, thematic, application, and population gaps. Produces an HTML report with Chart.js visualizations by default. Use when the user wants to find research gaps, map underexplored areas, or generate research questions from a literature landscape. Don't use for topic framing, paper drafting, citation verification, or journal matching.
---

Analyze research gaps for "$ARGUMENTS".

## Input Format

Input may specify:
- **Topic**: research area, field, or keyword to analyze
- **Focus**: temporal gaps, methodological gaps, thematic gaps, or all (default: all)
- **Output**: HTML report (default), markdown, or in-chat summary

Examples:
- `find research gaps in LLM fairness`
- `分析"联邦学习"领域的研究空白`
- `what are the main research gaps in climate finance? Give me an HTML report`

## Validation

**IMPORTANT:** If "$ARGUMENTS" is empty or only whitespace:
1. Ask the user: "What research field or topic would you like to analyze for gaps?"
2. Do NOT proceed until a non-empty topic is provided.

## Main Flow

```
Main Session — coordination
  │
  ├── Step 1: Literature Landscape — gather trend data via APIs
  ├── Step 2: Gap Identification — analyze landscape for gaps
  ├── Step 3: HTML Report — write gap analysis report
  └── Step 4: Budget Check — verify token usage is within bounds
```

## Step 1: Literature Landscape (subagent)

Launch a subagent with these instructions:

1. Generate 5 search queries from the topic: (a) core topic exact, (b) broader field, (c) methodology-focused, (d) application-focused, (e) "{topic} challenges OR future OR limitations".
2. For each query, fetch papers from Semantic Scholar:
   ```
   GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=40&fields=title,authors,year,venue,citationCount,abstract,fieldsOfStudy&year=2019-2026
   ```
3. Fetch publication trends from OpenAlex:
   ```
   GET https://api.openalex.org/works?search={topic}&group_by=publication_year&mailto=paperskills@example.com
   ```
4. Fetch concept trends from OpenAlex:
   ```
   GET https://api.openalex.org/concepts?search={topic}&mailto=paperskills@example.com
   ```
5. Fetch recent vs. classic paper comparison from OpenAlex:
   ```
   Recent: GET https://api.openalex.org/works?search={topic}&filter=publication_year:2023-2026&per_page=20&sort=cited_by_count:desc&mailto=paperskills@example.com
   Classic: GET https://api.openalex.org/works?search={topic}&filter=publication_year:2010-2015&per_page=20&sort=cited_by_count:desc&mailto=paperskills@example.com
   ```
6. Alternatively, run `python scripts/aggregate.py "{topic}" --format json` to collect OpenAlex data in one step.

Collect: paper count per year, top 30 cited papers, top 20 recent papers, top venues, key authors, related concepts, abstracts of top 30 papers.

For detailed API docs and fallback chains, read `references/api-reference.md`.

## Step 2: Gap Identification (subagent)

Launch a subagent with the landscape data from Step 1 and these instructions:

1. Analyze temporal gaps: topics studied 5+ years ago but not revisited recently, declining publication counts, emerging topics with <5 papers.
2. Analyze methodological gaps: theory-empirical imbalance, quant-qual imbalance, single-country vs. comparative, missing meta-analyses.
3. Analyze thematic gaps: extract themes from abstracts, find theme combinations that do NOT appear together, identify disconnected literature clusters.
4. Analyze application gaps: theory without applied studies, method validated in one domain but not others.
5. Analyze population/context gaps: geographic, demographic, temporal, institutional coverage.
6. Identify contradictions and unresolved debates.
7. **Apply Veto Rules:** For each identified gap, check the 5 veto conditions in `references/veto-rules.md`. If any veto fires, force priority to 3 and add `veto_triggered: true` with the veto reason. Vetoed gaps are still reported but flagged as potentially invalid.

For the full gap identification framework, output format, and scoring rubric, read `references/gap-analysis-methodology.md`.
For veto conditions and failure rules, read `references/veto-rules.md`.

## Step 3: HTML Report (subagent)

1. Write the report to `reports/{date}-research-gap-{topic-slug}.html`.
2. Include sections: Executive Summary (top 5 gaps), Literature Landscape (Chart.js line chart, venues table, authors table, concept list), Gap Analysis (cards with badges), Suggested Research Questions, Methodology Notes.
3. Follow the design system in `references/gap-analysis-methodology.md` (Crimson Pro font, CSS custom properties, academic book aesthetic, NO Tailwind CDN).
4. Return the exact absolute file path to the user.
5. Ask whether they want it opened. Only run `open {file_path}` after the user explicitly confirms.

## Step 4: Budget Check

After Step 3, verify token usage stayed within budget:
- If landscape subagent output exceeded ~40K tokens, note this and suggest summarizing landscape data before passing to gap analysis in future runs.
- Log approximate token usage per step for the user's reference.

## Token Budget

- Main coordination: ~3K
- Landscape subagent (Step 1): ~25-40K
- Gap analysis subagent (Step 2): ~15-25K
- Report subagent (Step 3): ~10-15K
- **Total: ~55-85K** (most intensive skill)

If landscape output is too large: summarize top 20 papers and trend data before passing to gap analysis subagent.

## Language

- If the user explicitly requests a language, use that language throughout.
- If the topic/input is primarily in Chinese, default to Chinese.
- Otherwise, default to English.

When generating in Chinese: set `<html lang="zh">`, use Chinese headings/labels, Chinese punctuation (，。、；：), Chinese badge text (e.g., "高优先级" not "HIGH PRIORITY").

## Error Handling

| Issue | Handling |
|-------|----------|
| Empty or whitespace input | Ask user for topic; do not proceed without it |
| Topic too broad (>100K papers) | Ask user to narrow to a subfield or specific phenomenon |
| Topic too narrow (0-5 papers) | Broaden search terms; check spelling; suggest alternative keywords |
| Semantic Scholar API failure | Fall back to OpenAlex for paper search; note reduced coverage |
| OpenAlex API failure | Fall back to Semantic Scholar only; note missing trend data |
| Both APIs fail | Report failure to user; offer to proceed with manual literature input |
| API rate limit hit | Exponential backoff (wait 2^n seconds, max 3 retries); then fall back |
| Trend data incomplete | Note which years have missing data; proceed with available evidence |
| Abstract coverage gaps | Note "abstract not available" count; analyze available abstracts only |
| Landscape output exceeds budget | Summarize to top 20 papers + yearly counts before passing to Step 2 |

## References

- API endpoints, parameters, fallback chains, fetch helper: `references/api-reference.md`
- Gap identification framework, scoring rubric, report structure: `references/gap-analysis-methodology.md`
- Veto Rules for gap claim validation: `references/veto-rules.md`
