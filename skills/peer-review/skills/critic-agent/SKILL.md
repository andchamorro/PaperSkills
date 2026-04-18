---
description: >-
  Validate and iteratively improve the peer review HTML report. Checks
  completeness of K-scores, radar chart accuracy, missing references table,
  language consistency, and factual accuracy against the manuscript. Runs up to
  2 refinement rounds. Used by the peer-review orchestrator — do not invoke
  directly.
---

# Critic Agent

Validate and refine the peer review report.

**Input:** HTML report file path + evaluator JSON + manuscript metadata (title, authors)
**Output:** Validated report (pass) or revision instructions (fail, up to 2 rounds)

## Validation Checklist

For each round, check ALL of the following. A check fails if the condition is not met.

### 1. Score Completeness
- [ ] All 8 K-criteria (K1-K8) have scores present in the report
- [ ] All scores are within the 1-5 range
- [ ] Each score has a non-empty justification paragraph
- [ ] Each criterion has at least 1 suggestion

### 2. Veto Consistency
- [ ] If evaluator JSON has `veto_triggered: true` for any criterion, the report shows a veto banner
- [ ] Vetoed criteria show a "VETO" badge in their detail card
- [ ] Vetoed criteria scores do not exceed 2/5 in the report
- [ ] Recommendation matches veto rules (3+ vetoes = Reject, 1-2 = capped at Major Revisions)

### 3. Radar Chart Accuracy
- [ ] Chart.js `data` array contains exactly 8 values
- [ ] The 8 values match the scores from the evaluator JSON (in the correct K1-K8 order)
- [ ] Labels match the 8 criterion names

### 4. Missing References Table
- [ ] Table is present in the report
- [ ] Contains at least 5 entries (unless the missing-refs detector found fewer)
- [ ] Each entry has: author(s), title, venue/year, citations, why-relevant
- [ ] Entries are ranked (highest relevance first)

### 5. Factual Accuracy
- [ ] Manuscript title in the report matches the actual manuscript title
- [ ] Author names in the report match the actual authors
- [ ] No hallucinated content (paper claims, scores, or references not from the evaluator data)

### 6. Language Consistency
- [ ] `<html lang="en">` is set
- [ ] ALL headings, labels, and descriptions are in English
- [ ] No mixed-language sections (except technical terms in original form)

### 7. HTML Validity
- [ ] Chart.js CDN script tag is present
- [ ] Crimson Pro font is loaded
- [ ] No Tailwind CDN references
- [ ] All `<details>` sections have matching `<summary>` tags
- [ ] Report follows design system from `skills/shared/report-template.md`

## Iteration Protocol

Follows the PapervizAgent critic pattern (`paperviz_processor.py:60-100`):

```
Round 0: First validation pass
  │
  ├── All checks pass → FINALIZE (return "No changes needed.")
  │
  └── Any check fails → return revision instructions
        │
        Round 1: Reporter revises → Critic re-validates
          │
          ├── All checks pass → FINALIZE
          │
          └── Any check fails → return revision instructions
                │
                Round 2 (max): Reporter revises → Critic re-validates
                  │
                  ├── All checks pass → FINALIZE
                  └── Still failing → FINALIZE with caveats
```

**Max rounds: 2.** After 2 rounds, finalize the best version with a caveat note listing unresolved issues.

## Output Format

### When all checks pass:

```json
{
  "status": "pass",
  "round": 0,
  "message": "No changes needed.",
  "checks_passed": 7,
  "checks_total": 7
}
```

### When checks fail:

```json
{
  "status": "revise",
  "round": 0,
  "message": "3 checks failed. Revision required.",
  "checks_passed": 4,
  "checks_total": 7,
  "failures": [
    {
      "check": "Radar Chart Accuracy",
      "issue": "Chart data array has 7 values instead of 8 — K5 Consistency score is missing",
      "fix": "Add the K5 score (value: 4) at index 4 in the Chart.js data array"
    },
    {
      "check": "Language Consistency",
      "issue": "Report is lang='zh' but Section Notes heading is in English ('Section Notes' instead of '章节评注')",
      "fix": "Replace 'Section Notes' with '章节评注'"
    },
    {
      "check": "Missing References Table",
      "issue": "Table has only 3 entries, detector found 15",
      "fix": "Include all 15 missing references from the detector output"
    }
  ]
}
```

### When finalizing with caveats (after max rounds):

```json
{
  "status": "pass_with_caveats",
  "round": 2,
  "message": "Finalized after 2 rounds. 1 unresolved issue.",
  "checks_passed": 6,
  "checks_total": 7,
  "unresolved": [
    {
      "check": "Radar Chart Accuracy",
      "issue": "Point color callback not rendering correctly in static validation",
      "severity": "low"
    }
  ]
}
```

## Error Handling

| Condition | Action |
|---|---|
| Report file not found | Return error: "Report file not found at {path}" |
| Evaluator JSON missing | Return error: "Cannot validate without evaluator data" |
| Report is empty | Return error: "Report file is empty" |
| Cannot parse HTML | Return specific parse error location and stop |
