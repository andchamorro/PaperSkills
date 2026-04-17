---
description: >-
  Perform academic peer review with 8-criteria scoring (originality, argument,
  literature, discussion, consistency, methodology, presentation, evidence) and
  Veto Rules. Generates an interactive HTML report with Chart.js radar chart.
  Uses a 4-agent pipeline: RetrieverAgent (few-shot examples), EvaluatorAgent
  (K1-K8 scoring with Veto Rules), ReporterAgent (HTML output), and CriticAgent
  (report quality validation, max 2 rounds). Use when the user asks to review a
  manuscript, evaluate a paper, assess peer review criteria, or generate a formal
  review report. Do NOT use for citation verification (use cite-verify), literature
  search (use lit-search), or abstract generation (use abstract).
---

# Peer Review

Perform an academic peer review of "$ARGUMENTS".

## When to Use This Skill

- User asks to "peer review this paper", "review my manuscript", or "evaluate this academic paper"
- User wants formal 8-criteria assessment (K1-K8) with Veto Rules
- User needs HTML report with radar chart visualization
- User wants missing reference detection alongside review

## File Resolution

- Filename only: look in current working directory
- Full path: use as-is
- .docx: extract text with `pandoc -t plain "$ARGUMENTS"` first

## Pipeline Architecture

```
peer-review orchestrator (this file) — coordination only
  │
  ├── STEP 1  RetrieverAgent → find 3-5 similar reviews as few-shot examples
  │
  ├── STEP 2a EvaluatorAgent → read + evaluate 8 criteria with Veto Rules  ┐ PARALLEL
  ├── STEP 2b MissingRefsAgent → find potentially missing references        ┘
  │
  ├── STEP 3  ReporterAgent → combine results → HTML report
  │
  └── STEP 4  CriticAgent → validate report quality (max 2 rounds)
```

## Step 1: Retriever Agent

1. Read the manuscript to extract: title, first 300 words of abstract, discipline.
2. Invoke sub-skill: `skills/peer-review/skills/retriever-agent`
3. Pass: manuscript title, abstract excerpt, discipline.
4. Receive: JSON array of 3-5 similar review examples with review methodology and criteria used.
5. If retriever returns empty (API failure or no results), proceed without few-shot examples — they are optional enrichment.

## Step 2a: Evaluator Agent (parallel)

1. Invoke sub-skill: `skills/peer-review/skills/evaluator-agent`
2. Pass: manuscript file path + few-shot examples from Step 1 (if available).
3. The evaluator reads `references/veto-rules.md` for K1-K8 Veto Rules.
4. Receive: structured JSON with 8-criteria scores, veto status, strengths, weaknesses, section notes, citation spot-check, and recommendation.

## Step 2b: Missing References Detector (parallel with 2a)

1. Invoke sub-skill: `skills/peer-review/skills/missing-refs-detector`
2. Pass: topic extracted from manuscript title/abstract, existing cited authors.
3. Receive: table of 15 potentially missing references ranked by relevance x citations.

**Steps 2a and 2b run IN PARALLEL.** Main session waits for both to complete.

## Step 3: Reporter Agent

1. Invoke sub-skill: `skills/peer-review/skills/reporter-agent`
2. Pass: evaluator JSON from Step 2a + missing-refs table from Step 2b + language setting.
3. The reporter reads the design system from `skills/shared/report-template.md` and the peer-review template from `references/report-template.md`.
4. Receive: HTML report file path at `reports/{date}-peer-review-{slug}.html`.

## Step 4: Critic Agent (max 2 rounds)

1. Invoke sub-skill: `skills/peer-review/skills/critic-agent`
2. Pass: report file path + evaluator JSON + manuscript metadata (title, authors).
3. The critic validates: score completeness, veto consistency, radar chart accuracy, missing refs table, factual accuracy, language consistency, HTML validity.
4. If any check fails → critic returns revision instructions → reporter revises → critic re-validates.
5. Max 2 rounds. After 2 rounds, finalize with caveats noting unresolved issues.
6. Optionally run `python scripts/validate_report.py --report {file_path}` for a deterministic second check.

## Step 5: Deliver Report

1. Return the exact absolute file path to the user.
2. Ask whether the user wants it opened.
3. Only run `open {file_path}` after the user explicitly confirms.

## Next Actions

Offer after report delivery:
- "Verify citations?" -> `/cite-verify {file}`
- "Search literature on specific gaps?" -> `/lit-search {topic}`
- "Generate abstract?" -> `/abstract {file}`

## Error Handling

| Error | Handling |
|-------|----------|
| 429 rate limit | Wait 60s, retry once |
| 0 API results | Broaden query terms |
| API down | Skip affected agent, note in report |
| .docx without pandoc | Tell user to install or convert to .md |
| Empty $ARGUMENTS | Ask user for file path |
| Retriever returns empty | Proceed without few-shot examples |
| Critic fails after 2 rounds | Finalize with caveat note |
| Evaluator JSON malformed | Reporter reports missing fields, ask user to re-run |

## Language

- If user explicitly requests a language (e.g., "in Chinese"): use that
- If manuscript is primarily in Chinese: default to Chinese
- Otherwise: English

When Chinese: `<html lang="zh">`, Chinese headings/labels, Chinese punctuation, Chinese criterion names (K1 原创性, K2 论证结构, K3 文献覆盖, K4 讨论深度, K5 概念一致性, K6 方法论, K7 表达规范, K8 论据支撑)

## Token Budget

| Phase | Estimated Tokens |
|---|---|
| Main (coordination) | ~3K |
| Step 1: Retriever | ~5K |
| Step 2a: Evaluator | ~15-30K |
| Step 2b: Missing refs | ~10-20K |
| Step 3: Reporter | ~5-10K |
| Step 4: Critic (per round) | ~3-5K |
| **Total** | **~45-75K** |

## References

- `references/veto-rules.md` — K1-K8 Veto Rules and evaluator output schema
- `references/report-template.md` — Peer-review-specific design system
- `skills/evaluator-agent/SKILL.md` — 8-criteria evaluation with Veto Rules
- `skills/retriever-agent/SKILL.md` — Few-shot review example retrieval
- `skills/reporter-agent/SKILL.md` — HTML report generation
- `skills/critic-agent/SKILL.md` — Report quality validation
- `skills/missing-refs-detector/SKILL.md` — Missing reference detection
