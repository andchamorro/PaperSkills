---
name: peer-review
description: Perform academic peer review with 8-criteria scoring (originality, argument, literature, discussion, consistency, methodology, presentation, evidence). Generates HTML report with radar chart. Use this skill whenever the user wants to review an academic manuscript, evaluate a paper's quality, assess peer review criteria, or generate a formal peer review report. This skill coordinates manuscript evaluation and missing reference detection sub-agents, then combines results into an HTML report with Chart.js radar visualization.
---

# Peer Review

Perform an academic peer review of "$ARGUMENTS".

## When to Use This Skill

- User asks to "peer review this paper", "review my manuscript", or "evaluate this academic paper"
- User wants formal 8-criteria assessment (K1-K8)
- User needs HTML report with radar chart visualization
- User wants missing reference detection alongside review
- User asks for "peer review" or "academic review" of a paper

## File Resolution

- Filename only: look in current working directory
- Full path: use as-is
- .docx: extract text with `pandoc -t plain "$ARGUMENTS"` first

## Main Flow

```
Main Session — coordination only, does NOT read the manuscript
  │
  ├── 1a. Subagent → manuscript-evaluator: read + evaluate 8 criteria (parallel)
  ├── 1b. Subagent → missing-refs-detector: find potentially missing refs (parallel)
  │
  └── 2. Report subagent → combine results → HTML report + offer to open
```

**1a and 1b run IN PARALLEL.** Main session stays clean.

## Step 1a: Manuscript Evaluator

Invoke sub-skill: `skills/peer-review/skills/manuscript-evaluator`

Input: manuscript file path

Output: 8-criteria scores with justifications, strengths, areas for improvement, section notes, citation spot-check.

## Step 1b: Missing Reference Detector

Invoke sub-skill: `skills/peer-review/skills/missing-refs-detector`

Input: topic (extracted from manuscript), existing cited authors

Output: Table of 15 potentially missing references ranked by relevance × citations.

## Step 2: Report Generation

Combine 1a + 1b results. Write HTML report to:
`reports/{date}-peer-review-{manuscript-name}.html`

**Design requirements:**
- Radar chart for 8 criteria (Chart.js)
- Color-coded scores: green (4-5), yellow (3), red (1-2)
- Collapsible sections (details/summary)
- Missing references table
- Print-friendly styling
- Read `assets/report-template.md` from paperskills root — use that design system exactly

After writing file:
1. Return exact absolute file path to user
2. Ask whether they want it opened
3. Only run `open {file_path}` after user confirms

## Next Actions

Offer after report:
- "Verify citations?" → `/cite-verify {file}`
- "Search literature on specific gaps?" → `/lit-search {topic}`
- "Generate abstract?" → `/abstract {file}`

## Error Handling

| Error | Handling |
|-------|----------|
| 429 rate limit | Wait 60s, retry once |
| 0 API results | Broaden query terms |
| API down | Skip, note in report |
| .docx without pandoc | Tell user to install or convert to .md |
| Empty $ARGUMENTS | Ask user for file path |

## Language

- If user explicitly requests a language (e.g., "in Chinese"): use that
- If manuscript is primarily in Chinese: default to Chinese
- Otherwise: English

When Chinese: `<html lang="zh">`, Chinese headings/labels, Chinese punctuation, Chinese criterion names (K1 原创性, K2 论证结构, etc.)

## Token Budget

- Main: ~2K (coordination)
- 1a subagent: ~15-30K (manuscript + evaluation)
- 1b subagent: ~10-20K (API calls + dedup)
- Report subagent: ~5-10K
- Total: ~35-60K

## References

- `references/report-template.md` — Design system for HTML output
- `skills/manuscript-evaluator/SKILL.md` — 8-criteria evaluation details
- `skills/missing-refs-detector/SKILL.md` — Reference detection details