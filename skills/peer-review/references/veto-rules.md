# Veto Rules for Peer Review K-Criteria

Absolute pass/fail conditions for each K-criterion. Inspired by PapervizAgent's evaluation framework (`diagram_eval_prompts.py`).

**Rule:** If any Veto Rule fires for a criterion, that criterion's score is capped at 2/5 with an explicit explanation. No nuanced scoring on fundamentals — a veto is a hard failure.

---

## K1 Originality

**Veto condition:** Paper makes no novel claim beyond incremental improvement of an existing method without new insight.

**Triggers when ALL of these hold:**
- No new theoretical contribution, framework, dataset, or empirical finding
- Contribution section only claims "we apply X to Y" without explaining why the combination is non-trivial
- No comparison to prior attempts at the same combination

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: the paper does not articulate a novel contribution beyond applying {method} to {domain}. To lift this veto, the authors must demonstrate what prior attempts missed or why this combination yields non-obvious results."

---

## K2 Argument Structure

**Veto condition:** Thesis is absent or self-contradictory across sections.

**Triggers when ANY of these hold:**
- Introduction lacks a clear thesis or research question
- Conclusion contradicts claims made in the introduction
- Logical chain has a gap where a major claim is asserted without connection to prior reasoning
- Paper argues for and against the same position in different sections without acknowledging the tension

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: {specific contradiction or missing thesis}. The argument cannot be evaluated without a coherent throughline."

---

## K3 Literature Coverage

**Veto condition:** Major field references missing; no primary sources.

**Triggers when ANY of these hold:**
- Seminal papers in the field (>1000 citations, foundational to the topic) are absent from the bibliography
- All citations are secondary sources (textbooks, reviews) with zero primary research papers
- Literature review cites fewer than 5 sources for a field with >100 relevant publications
- Key opposing viewpoints are entirely absent

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: the bibliography omits {specific seminal work(s)} which are foundational to this topic. Additionally, {additional issue}."

---

## K4 Discussion Depth

**Veto condition:** Author misrepresents cited sources or conflates own views with others' views.

**Triggers when ANY of these hold:**
- A cited source is used to support a claim it actually opposes
- Author presents another researcher's contested opinion as established fact
- Discussion section merely restates results without interpretation or comparison to prior work
- No engagement with counterarguments or limitations

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: {specific misrepresentation or conflation}. The discussion does not demonstrate genuine engagement with the cited literature."

---

## K5 Conceptual Consistency

**Veto condition:** Terminology contradicts itself across sections.

**Triggers when ANY of these hold:**
- A key term is defined differently in the introduction vs. methods vs. discussion
- A central concept is used with contradictory meanings without acknowledgment
- Framework components are renamed mid-paper without explanation

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: the term '{term}' is used inconsistently — defined as {def_A} in {section_A} but as {def_B} in {section_B}."

---

## K6 Methodology

**Veto condition:** Method is unspecified or fundamentally mismatched to the research question.

**Triggers when ANY of these hold:**
- No methodology section exists and no method is described elsewhere
- The stated method cannot answer the research question (e.g., survey data used to claim causation without controls)
- Sample/data selection is not justified or described
- Statistical methods are inappropriate for the data type (e.g., parametric tests on ordinal data without justification)

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: {specific methodological failure}. The research question requires {what's needed} but the paper provides {what's present}."

---

## K7 Presentation

**Veto condition:** Entirely incomprehensible prose; >50% grammatical errors rendering meaning unclear.

**Triggers when ANY of these hold:**
- More than half of paragraphs contain grammatical errors that change or obscure meaning
- Paper has pervasive grammatical errors suggesting insufficient proofreading
- Figures/tables are referenced but missing, or present but never referenced
- Section ordering is incoherent (e.g., results before methods, no introduction)

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: presentation quality prevents meaningful evaluation. {specific examples of incomprehensible passages or structural issues}."

---

## K8 Evidence

**Veto condition:** Three or more major claims lack any supporting evidence.

**Triggers when ANY of these hold:**
- Three or more central claims have zero citations, data, or logical derivation supporting them
- Key numerical results are stated without showing the data or analysis that produced them
- Conclusions go significantly beyond what the evidence supports (overgeneralization)
- Critical evidence is "data not shown" or "results available upon request" for core claims

**Score if vetoed:** capped at 2/5
**Explanation template:** "Veto triggered: {N} major claims lack supporting evidence: {list claims}. These are central to the paper's argument and cannot be accepted on assertion alone."

---

## Evaluator Output Schema

When applying Veto Rules, the evaluator MUST return structured JSON for each criterion:

```json
{
  "criterion": "K1 Originality",
  "score": 3,
  "veto_triggered": false,
  "veto_reason": null,
  "reasoning": "The paper introduces a novel framework combining...",
  "suggestions": [
    "Strengthen the novelty claim by comparing to Smith et al. (2024)",
    "Add ablation study to demonstrate which component drives improvement"
  ]
}
```

When a veto fires:

```json
{
  "criterion": "K6 Methodology",
  "score": 2,
  "veto_triggered": true,
  "veto_reason": "Method is fundamentally mismatched: survey data used to claim causation without experimental controls",
  "reasoning": "Veto triggered: the research question asks 'does X cause Y' but the methodology is a cross-sectional survey with no control group or longitudinal design.",
  "suggestions": [
    "Redesign as a controlled experiment or longitudinal study",
    "Alternatively, reframe the research question to match descriptive methodology"
  ]
}
```

## Veto Summary

The evaluator MUST also produce an overall veto summary:

```json
{
  "total_vetoes": 1,
  "vetoed_criteria": ["K6"],
  "recommendation_override": "If >=3 vetoes fire, recommendation MUST be 'Reject' regardless of other scores."
}
```

**Decision rules:**
- 0 vetoes: recommendation based on average score
- 1-2 vetoes: recommendation capped at "Major Revisions"
- 3+ vetoes: recommendation forced to "Reject"
