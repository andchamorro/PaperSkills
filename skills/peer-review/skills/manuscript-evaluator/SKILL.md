---
name: manuscript-evaluator
description: Evaluate academic manuscripts against 8 peer review criteria (K1-K8): originality, argument structure, literature coverage, discussion depth, conceptual consistency, methodology, presentation, and evidence. Provides scores (1-5), justifications, and improvement suggestions. Used by the peer-review orchestrator.
---

# Manuscript Evaluator

Evaluate this manuscript to peer-review standards.

**Input:** File path to manuscript (PDF, DOCX, MD, or TXT)

**Output:** Structured evaluation with 8 criteria scores, strengths, weaknesses, and recommendation.

## Quick Usage

### 1. Read the Manuscript

Use Read tool to load the file content. Handle formats:
- PDF: Use extract if available, or note file cannot be read directly
- DOCX: Run `pandoc -t plain {file}` first
- MD/TXT: Read directly

### 2. Structural Analysis

Extract:
- Title, author(s), section count, estimated word count
- Reference/footnote count and distribution
- Clear thesis statement in introduction?
- Conclusion aligns with introductory promises?
- Abstract present and accurate?

### 3. 8-Criteria Evaluation

For each criterion, provide: score (1-5), justification, specific suggestion

| Criterion | What to Assess | Scoring Guide |
|-----------|----------------|---------------|
| **K1 Originality** | What does this contribute? Novel argument, new data, synthesis? | 5=highly original, 1=novelty unclear |
| **K2 Argument Structure** | Thesis clear? Logical chain coherent? Repetition? | 5=crystal clear, 1=unclear |
| **K3 Literature Coverage** | Source base adequate? Primary/secondary? Currency? Missing key works? | 5=comprehensive, 1=major gaps |
| **K4 Discussion Depth** | Counterarguments fair? Author takes position? Genuine engagement? | 5=deep engagement, 1=superficial |
| **K5 Conceptual Consistency** | Terminology consistent? Translations correct? Multilingual terms? | 5=consistent, 1=confusing |
| **K6 Methodology** | Method stated? Source/data selection justified? | 5=sound, 1=unclear |
| **K7 Presentation** | Academic language, paragraph lengths, footnote balance? | 5=polished, 1=needs work |
| **K8 Evidence** | Claims supported? Unsupported assertions? | 5=well-supported, 1=under-argued |

### 4. Strengths

List 5-6 specific strengths with evidence from text.

### 5. Areas for Improvement

List 5-6 areas with concrete suggestions for each.

### 6. Section-by-Section Notes

1-2 sentences per major section (intro, methods, results, discussion, conclusion).

### 7. Citation Spot-Check

Pick 5 key claims that rely on citations:
- Does the cited source actually support the claim?
- Is the author citing someone's view or their report of another's view?
- Any overstatement, misattribution, or approval/critique confusion?

Note: Full verification via `/cite-verify`

### 8. Recommendation

Choose one:
- **Accept** — publish as-is
- **Minor revisions** — small fixes needed
- **Major revisions** — substantial work required
- **Reject** — not suitable for publication

## Output Format

```
STRUCTURAL ANALYSIS:
- Title: ...
- Authors: ...
- Sections: N
- Word count: ~X,XXX
- References: N

8-CRITERIA SCORES:
K1 Originality:      X/5 — {justification}
K2 Argument:        X/5 — {justification}
K3 Literature:      X/5 — {justification}
K4 Discussion:       X/5 — {justification}
K5 Consistency:     X/5 — {justification}
K6 Methodology:     X/5 — {justification}
K7 Presentation:    X/5 — {justification}
K8 Evidence:        X/5 — {justification}

STRENGTHS:
1. ...
2. ...

AREAS FOR IMPROVEMENT:
1. {issue} → {suggestion}
2. ...

SECTION NOTES:
- Introduction: ...
- Methods: ...
- Results: ...
- Discussion: ...
- Conclusion: ...

CITATION SPOT-CHECK:
- Claim: "..." [citation]
  - Assessment: ...
- ...

RECOMMENDATION: {Accept/Minor/Major/Reject}
```

## Error Handling

- Cannot read file: tell user format not supported, ask for alternative
- Very short manuscript: note limitations, adjust expectations
- Missing sections: note in structural analysis, score criteria appropriately
- Non-academic content: note this is not a standard academic paper

## References

For full criterion definitions, see `references/criteria-reference.md`.