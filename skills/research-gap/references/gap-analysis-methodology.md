# Gap Analysis Methodology

Framework for identifying research gaps from literature landscape data. Used by the gap identification subagent in Step 2.

## Gap Types

### A. Temporal Gaps

Identify topics that were active in the past but have declined:

- Topics studied 5+ years ago but NOT revisited recently
- Declining publication count despite unresolved questions
- Emerging topics with fewer than 5 papers
- Methodological approaches that peaked and were abandoned

**Evidence required:** Publication counts per year showing the trend.

**Example:** In "federated learning privacy", differential privacy was heavily studied in 2019-2021 (50+ papers/year) but dropped to <10 papers/year by 2024 — despite open questions about utility-privacy tradeoffs in heterogeneous data distributions. This is a temporal gap with high impact.

### B. Methodological Gaps

Identify where the field lacks methodological diversity:

- Mostly theoretical → no empirical studies
- Mostly quantitative → no qualitative work
- Mostly single-country → no comparative studies
- Lab experiments → no field studies
- No meta-analyses or systematic reviews for established topics
- Established methods not applied to new domains

**Evidence required:** Distribution of methods across the literature.

**Example:** In "AI fairness in hiring", 85% of studies use quantitative audit methods on historical datasets. Only 3 papers use qualitative interviews with hiring managers to understand how fairness metrics are interpreted in practice. This is a methodological gap (quant→qual).

### C. Thematic Gaps

Identify underexplored theme combinations and disconnected clusters:

1. Extract themes from top paper abstracts using keyword co-occurrence
2. Find theme combinations that do NOT appear together:
   - e.g., "fairness + NLP" has 200 papers, "fairness + speech" has 3
   - e.g., "causality + reinforcement learning" rarely appears
3. Identify disconnected literature clusters that should connect
4. Look for theory-practice disconnects (theory exists, no applied work)

**Evidence required:** Paper counts for individual themes vs. combinations.

**Example:** "Fairness + NLP" returns 200+ papers; "fairness + speech recognition" returns 3. Both are AI modalities with bias risks, but speech fairness is dramatically understudied. This is a thematic gap (untested combination).

### D. Application Gaps

Identify where established methods/theories haven't been transferred:

- Theory exists but no applied or practical studies
- Method validated in one domain but not others
- Framework developed for one population not tested on others
- Technology tested in one industry but not adjacent ones

**Example:** Explainable AI (XAI) frameworks like LIME and SHAP have been extensively validated in healthcare diagnostics (100+ papers) but have <5 papers applying them to legal sentencing decisions — despite similar high-stakes requirements. This is an application gap (cross-domain transfer).

### E. Population / Context Gaps

Identify who/what is studied vs. overlooked:

- Geographic: studied in US/EU but not Global South?
- Demographic: adults but not children, elderly, specific professions?
- Temporal: historical studies but not contemporary?
- Institutional: large companies but not SMEs, NGOs, governments?
- Biological: animal models but not human studies (or vice versa)?

**Example:** Research on "LLM-assisted peer review" is concentrated on English-language CS venues (NeurIPS, ICLR). Only 2 papers study non-English peer review or humanities/social science venues, despite fundamentally different review norms. This is a population/context gap (geographic + disciplinary).

### F. Contradictions and Debates

Identify unresolved tensions:

- Opposing findings on the same research question
- Unresolved theoretical debates with competing claims
- Inconsistent effect sizes across studies
- Reproducibility concerns

**Example:** In "LLM evaluation", some studies find GPT-4 outperforms human reviewers on consistency (Liang et al., 2024) while others find LLMs systematically miss methodological flaws that humans catch (Li et al., 2025). This contradiction is unresolved — no study has directly compared both claims on the same dataset.

## Gap Scoring Rubric

Prioritize gaps using the **Priority = Impact x Feasibility** formula:

| Level | Impact Score | Feasibility Score |
|-------|:-----------:|:-----------------:|
| High | 3 | 3 |
| Medium | 2 | 2 |
| Low | 1 | 1 |

**Priority score** = Impact x Feasibility (range 1-9):
- **Priority 1 (score 6-9):** Most promising — pursue first
- **Priority 2 (score 3-5):** Viable with effort
- **Priority 3 (score 1-2):** Niche — low impact or hard to execute

**Impact criteria:**
- High: fills a gap that affects multiple subfields or has practical implications
- Medium: addresses a recognized limitation in one subfield
- Low: niche interest, affects a small community

**Feasibility criteria:**
- High: data exists and is accessible; standard methods apply
- Medium: data exists but requires collection effort; methods need adaptation
- Low: data is scarce or proprietary; novel methods required

## Output Format

For each identified gap, produce:

```
GAP [number]:
- Type: {A/B/C/D/E/F}
- Gap description: {1-2 sentence description}
- Evidence:
  - What exists: {paper count, key papers, main findings}
  - What is missing: {specific gap}
- Suggested research question: {concrete, answerable question}
- Feasibility: {high/medium/low}
  - Data availability: {what data exists}
  - Method needed: {what approach would work}
- Impact: {high/medium/low}
- Priority: 1 (most promising) to 3 (niche)
```

## Report Structure

For the HTML report in Step 3, include these sections:

### 1. Executive Summary
Top 5 gaps prioritized by (Impact × Feasibility). Brief narrative of the field landscape.

### 2. Literature Landscape
- Chart.js line chart: papers per year (2010-2026)
- Top venues table (name, paper count)
- Key authors table (name, papers, citations)
- Related concepts as tag cloud or list

### 3. Gap Analysis
Each gap as a card using class `gap-card`:
- `<span class="badge badge-{type}">` for gap type (temporal, methodological, thematic, application, population, contradiction)
- `<div class="evidence">` for what exists vs. what's missing
- `<p class="research-question">` for suggested research question
- `<span class="badge badge-priority-{1|2|3}">` for priority: Priority 1 (red `#c53030`), Priority 2 (yellow `#d69e2e`), Priority 3 (blue `#2b6cb0`)

### 4. Suggested Research Questions
Numbered list of the top 5 research questions, one per priority gap.

### 5. Methodology Notes & Limitations
- Which years have incomplete data
- Which APIs had partial coverage
- Acknowledged gaps in the analysis itself

## Design System

When writing the HTML report, follow `skills/shared/report-template.md` design system:
- Crimson Pro font
- CSS custom properties
- Academic book aesthetic
- Bilingual labels (Chinese/English based on language setting)
- Chart.js for visualizations
- NO Tailwind CDN
