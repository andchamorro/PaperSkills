---
name: paper-tracker
description: >-
  Track newly published academic papers by author, institution, journal, venue,
  keyword, or domain within a specified time window. Produces a one-shot summary
  report in Markdown or HTML. Use when the user asks to monitor, track, or list
  recent publications for a person, lab, university, conference, or topic.
  Do NOT use for full systematic literature reviews, citation network analysis,
  citation verification, bibliometric mapping, or paper recommendation. Do NOT
  use when the user already has a specific paper and wants to read or summarize it.
---

Track newly published papers for "$ARGUMENTS".

Input may specify:
- **Time window**: `1 day`, `1 week`, `1 month`, `last 90 days`, or explicit dates such as `2026-01-01 to 2026-03-01`
- **Scope**: one or more of author, institution, journal/venue, keyword, domain
- **Output format**: quick list, HTML report, or Markdown report

Examples:
- `track papers from Nature and Science in the last month`
- `追踪 Geoffrey Hinton 和 Yann LeCun 过去 30 天的新论文`
- `track new LLM safety papers from CMU and Stanford between 2026-01-01 and 2026-03-15`

## MAIN FLOW

```
Main Session — coordination (no subagents unless user requests comparative analysis)
  │
  ├── STEP 1  Normalize tracking request
  ├── STEP 2  Query primary source by scope type
  ├── STEP 3  Merge, deduplicate, filter to time window
  ├── STEP 4  Enrich every matched paper with abstracts / links
  └── STEP 5  Produce one-shot summary report
```

---

## STEP 1 — Normalize Tracking Request

1. Extract the **time window**.
   - If the user provides a relative window (`1 week`, `last 30 days`), resolve it to explicit `start` / `end` ISO dates.
   - If the user provides no window, default to the last 30 days and state that assumption.
2. Classify every **scope entity** into exactly one type:
   - `author` — a person name
   - `institution` — a university, lab, or company
   - `journal` / `venue` — a publication outlet or conference
   - `keyword` / `domain` — a topic or discipline
3. Determine the **output format**:
   - `html` (default) — single-file HTML report
   - `markdown` — single-file Markdown report
   - `short` — inline chat answer
4. Report language is **English**.

---

## STEP 2 — Query Sources by Scope Type

Use **OpenAlex** as the primary source. See `references/api-reference.md` for full endpoint details, parameter templates, and fallback APIs.

Follow the decision tree below for each scope entity:

1. **If scope is `author`**:
   1. Search the OpenAlex authors endpoint for the name.
   2. If multiple candidates are returned, pick the best match by affiliation and publication count; note the ambiguity.
   3. Query works filtered by the resolved `author.id` and the date window.
2. **If scope is `institution`**:
   1. Search the OpenAlex institutions endpoint for the name.
   2. If multiple candidates are returned, pick the best match by country/type; note the ambiguity.
   3. Query works filtered by `institutions.id` and the date window.
3. **If scope is `journal` / `venue`**:
   1. Search the OpenAlex sources endpoint for the name.
   2. Query works filtered by `primary_location.source.id` and the date window.
4. **If scope is `keyword` / `domain`**:
   1. Query works using full-text search with the keyword and the date window filter.

When the user provides **multiple scope entities**, run one focused query per entity, then merge all result sets in Step 3.

### Abstract and Metadata Enrichment (within Step 2)

5. For papers that need enrichment (missing abstract, DOI, or publication date), use **batch processing with concurrency control** (PapervizAgent semaphore pattern from `paperviz_processor.py:185-240`):

   **Option A — Script-based batch (recommended for >10 papers):**
   1. Export papers needing enrichment to a JSON file:
      ```json
      [{"doi": "10.1234/...", "title": "..."}, ...]
      ```
   2. Run the batch fetch script:
      ```
      python scripts/batch_fetch.py --input papers_to_enrich.json --max-concurrent 10 --output enriched.json
      ```
   3. The script uses `asyncio.Semaphore(max_concurrent)` to limit parallel API requests:
      - Tries OpenAlex first (by DOI)
      - Falls back to Semantic Scholar (by DOI or title search)
      - Last resort: CrossRef (by DOI)
   4. Read the enriched JSON output and merge back into the paper list.

   **Option B — Sequential enrichment (for <=10 papers):**
   1. For each paper, attempt to obtain an abstract:
      1. Use the OpenAlex abstract if available.
      2. If missing, query Semantic Scholar by DOI or title. See `references/api-reference.md`.
      3. If still missing, keep the paper and mark abstract as `Abstract unavailable`.
   2. If a paper is missing a DOI or publication date, query CrossRef by title as a last resort.

6. If a paper is missing a DOI or publication date after enrichment, keep it with available metadata and note the gap.

---

## STEP 3 — Merge, Deduplicate, and Filter

1. Collect all papers from Step 2 into a single list.
2. Run deduplication. Use `scripts/deduplicate.py` for deterministic DOI normalization and fuzzy title matching:
   ```
   cat merged.json | python scripts/deduplicate.py --threshold 0.8
   ```
3. Run date-window filtering. Use `scripts/window_filter.py`:
   ```
   cat deduped.json | python scripts/window_filter.py --from {start} --to {end}
   ```
4. For each surviving paper, record **why it matched** (author, journal, institution, keyword). If a paper matches multiple scopes, keep all reasons.
5. Sort results by publication date descending. Use citation count only as a secondary tie-breaker.

---

## STEP 4 — Build Tracking Summary

For each paper, collect these fields:

| Field             | Required | Fallback                        |
|-------------------|----------|---------------------------------|
| title             | yes      | —                               |
| authors           | yes      | —                               |
| publication_date  | yes      | indexed date (state fallback)   |
| journal / venue   | yes      | `Unknown venue`                 |
| match_reason      | yes      | —                               |
| doi               | no       | source URL                      |
| abstract          | no       | `Abstract unavailable`          |
| abstract_snippet  | no       | first 2-4 sentences of abstract |
| open_access_url   | no       | —                               |

Also compute aggregate statistics:
- Total papers found
- Papers grouped by day or week within the window
- Top journals / venues in the matched set
- Most frequent authors in the matched set
- Keyword themes inferred from titles and abstracts

---

## STEP 5 — Output Report

### 5a. HTML Report (default)

1. Read `skills/shared/report-template.md` and follow that design system exactly.
2. Include the following sections:
   1. Header with scope description and date range
   2. Executive summary (total papers, top venue, main themes)
   3. Stats bar (papers by week, top authors, top venues)
   4. Paper cards — each card contains: title, authors, date, venue, match reason, DOI link, abstract block
   5. Thematic observations (2-3 short paragraphs)
   6. Methodology / coverage note
3. Write to `reports/{date}-paper-tracker-{slug}.html`.
4. Return the exact absolute file path to the user.
5. Ask whether the user wants the file opened. Only run `open {file_path}` after explicit confirmation.

### 5b. Markdown Report

If the user requests Markdown, use this template:

```markdown
# Paper Tracking Report

## Tracking Scope
- **Window**: {start} to {end}
- **Journals**: {list or "—"}
- **Authors**: {list or "—"}
- **Institutions**: {list or "—"}
- **Keywords**: {list or "—"}

## Executive Summary
- {N} papers matched
- Most active venue: {venue}
- Main themes: {theme_1}, {theme_2}, {theme_3}

## New Papers

### 1. {Paper Title}
- **Date**: {publication_date}
- **Authors**: {author_list}
- **Venue**: {venue}
- **Match Reason**: {reason}
- **DOI**: {doi_or_url}
- **Abstract**: {abstract_or_unavailable}

<!-- repeat for each paper -->

## Observations
- {Trend summary}
- {Notable new authors or labs}
- {Gaps or caveats in coverage}
```

Write to `reports/{date}-paper-tracker-{slug}.md`.

---

## ERROR HANDLING

### Zero Results for a Scope
1. Broaden the date window by 2× (e.g., 30 days → 60 days).
2. If still zero, relax the scope (e.g., search by keyword instead of exact author ID).
3. Report the broadening to the user and explain what changed.

### Ambiguous Author or Institution Name
1. Retrieve the top 3-5 candidates from OpenAlex with display name, affiliation, and works count.
2. Present the candidates to the user and ask for confirmation before proceeding.
3. If non-interactive context, pick the candidate with the highest works count and note the assumption.

### Rate Limiting
1. **OpenAlex**: include `mailto=paperskills@example.com` in every request (raises limit to ~10 req/s). If a 429 response is received, back off 2 seconds and retry once.
2. **Semantic Scholar**: limit to 1 request per second. On 429, wait 5 seconds and retry once.
3. **CrossRef**: no strict limit, but keep requests ≤5/s.

### Missing Abstracts
1. Do not block the report. Mark the abstract field as `Abstract unavailable`.
2. Continue building the summary with the remaining metadata.

### Date Field Unavailable
1. Prefer `publication_date` from OpenAlex.
2. If missing, fall back to `created_date` (indexed date) and add a note: `"Date reflects indexing, not publication."`.

### Missing DOI
1. Keep the paper in the report with its source URL or OpenAlex ID.
2. Note `DOI unavailable` in the paper card.

---

## COVERAGE RULES

- Treat this as a **freshness-first** task: prioritize newest papers over highly cited historical papers.
- Prefer publication date over citation count for ordering.
- State clearly when a result is early-access or online-first.
- If the exact entity resolution is ambiguous, show the top candidate and mention the ambiguity.

---

## TOKEN BUDGET

- Normal run: ~20-35K
- Multi-scope tracking with HTML report: ~30-45K
