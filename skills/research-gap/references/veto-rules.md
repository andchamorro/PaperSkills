# Veto Rules for Research Gap Identification

Absolute failure conditions for gap claims. Inspired by PapervizAgent's Veto Rules evaluation framework (`diagram_eval_prompts.py`). A vetoed gap is downgraded to Priority 3 (niche) regardless of its Impact x Feasibility score.

**Rule:** If a Veto Rule fires for a gap claim, that gap's priority is forced to 3 (lowest) with an explicit explanation. The gap is still reported but flagged as potentially invalid.

---

## Veto 1: Unsupported Gap Claim

**Condition:** Claiming a gap exists with zero supporting papers.

**Triggers when:**
- The gap description names a missing research area but cites zero papers that study adjacent topics
- No publication count data supports the claim of absence
- The "what exists" field is empty or contains only vague references ("some studies")

**Veto action:** Priority forced to 3. Flag: "This gap claim has no supporting evidence. To validate, provide publication counts or specific papers that demonstrate the absence."

**Why this matters:** A gap claim without evidence is unfalsifiable. The literature might simply not have been searched thoroughly.

---

## Veto 2: Premature Temporal Gap

**Condition:** Declaring a "temporal gap" when the topic is genuinely emerging (<3 years old).

**Triggers when:**
- The topic's earliest publication is within the last 3 years
- The publication trend is clearly increasing (each year has more papers than the previous)
- The gap claim states "research has declined" but the data shows the field hasn't had time to mature

**Veto action:** Priority forced to 3. Flag: "This topic appears to be emerging (first papers within 3 years). A temporal gap requires a decline from a previously established research activity, not merely a young field."

**Why this matters:** Emerging fields naturally have low publication counts. Labeling this as a "gap" conflates newness with neglect.

---

## Veto 3: Unanchored Methodological Gap

**Condition:** Listing a "methodological gap" without identifying the dominant method it contrasts against.

**Triggers when:**
- The gap says "no qualitative studies exist" without showing how many quantitative studies exist
- The gap says "no experimental studies" without identifying what method IS being used
- No distribution of methods across the literature is provided
- The contrast method is unnamed or vague ("standard approaches")

**Veto action:** Priority forced to 3. Flag: "Methodological gaps require a baseline: identify the dominant method (with paper count) before claiming an alternative is missing."

**Why this matters:** Without knowing what method dominates, the "gap" is a guess. The field might use a third method entirely.

---

## Veto 4: Trivial Thematic Combination

**Condition:** Claiming a thematic gap for a combination that has no logical connection.

**Triggers when:**
- The two themes combined have no shared theoretical basis or practical application
- No argument is provided for why the combination would be valuable
- The combination produces zero results not because it's understudied but because it's nonsensical

**Veto action:** Priority forced to 3. Flag: "The combination '{theme_A} + {theme_B}' lacks a stated rationale for why this intersection would produce meaningful research."

**Why this matters:** Not every missing combination is a gap. Some combinations don't exist because they have no intellectual basis.

---

## Veto 5: Overgeneralized Population Gap

**Condition:** Claiming a population/context gap without checking if the population is relevant to the research question.

**Triggers when:**
- The gap claims "no studies in {country}" but the phenomenon is jurisdiction-specific and doesn't apply there
- The gap claims "no pediatric studies" for a condition that only affects adults
- No argument for why the missing population would yield different results

**Veto action:** Priority forced to 3. Flag: "The population gap '{missing_population}' requires justification for why studying this group would contribute new insights to the research question."

**Why this matters:** Geographic or demographic extension is only valuable when the context might produce different results.

---

## Application in Gap Analysis

When identifying gaps in Step 2, apply these veto checks to each gap before assigning priority:

```
For each candidate gap:
  1. Check Veto 1-5 conditions
  2. If any veto fires → priority = 3, add veto_flag and veto_reason
  3. If no vetoes → calculate priority normally (Impact x Feasibility)
```

### Output Schema for Vetoed Gaps

```json
{
  "gap_number": 3,
  "type": "B",
  "description": "No qualitative studies on LLM peer review",
  "priority": 3,
  "veto_triggered": true,
  "veto_rule": "Veto 3: Unanchored Methodological Gap",
  "veto_reason": "Gap claims no qualitative studies but does not report the count of quantitative studies or identify the dominant method",
  "original_priority": 1,
  "evidence": {
    "what_exists": "...",
    "what_is_missing": "..."
  }
}
```

### Report Display

In the HTML report, vetoed gaps should be visually distinct:
- Gray badge instead of priority color
- Strikethrough on the original priority
- Veto reason displayed in an orange callout box
- Placed after non-vetoed gaps of the same type
