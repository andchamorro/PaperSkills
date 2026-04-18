---
description: >-
  Generate the HTML peer review report from structured evaluator and missing-refs
  JSON output. Applies the academic style guide, creates Chart.js radar
  visualization, and writes a single-file HTML report. Used by the peer-review
  orchestrator — do not invoke directly.
---

# Reporter Agent

Generate an HTML peer review report from structured evaluation data.

**Input:** Evaluator JSON (8-criteria scores, veto status, strengths, weaknesses, recommendation) + Missing-refs table
**Output:** Single-file HTML report at `reports/{date}-peer-review-{slug}.html`

## Step 1 — Validate Input

1. Confirm the evaluator JSON contains all 8 criteria with scores, reasoning, and suggestions.
2. Confirm the missing-refs data contains a ranked table of references.
3. If either input is malformed, report the specific missing fields and stop.

## Step 2 — Apply Style Guide

1. Read the design system from `skills/shared/report-template.md` and follow it EXACTLY.
2. Read `references/report-template.md` for peer-review-specific layout.
3. Do NOT use Tailwind CDN. Use custom CSS variables, Crimson Pro font, and academic book aesthetic.

## Step 3 — Build HTML Report

The report MUST include all sections below in this order:

### 3a. Header
- Report tag: "Peer Review Report"
- Manuscript title (from evaluator `structural_analysis.title`)
- Authors (from evaluator `structural_analysis.authors`)
- Generation date
- Recommendation badge — color-coded:
  - Accept: green `#38a169` ("ACCEPT" / "接受")
  - Minor Revisions: yellow `#d69e2e` ("MINOR REVISIONS" / "小修")
  - Major Revisions: orange `#dd6b20` ("MAJOR REVISIONS" / "大修")
  - Reject: red `#e53e3e` ("REJECT" / "拒绝")

### 3b. Veto Alert Banner (conditional)
- If `veto_summary.total_vetoes > 0`, display a prominent banner:
  - Red background for 3+ vetoes
  - Orange background for 1-2 vetoes
  - List each vetoed criterion and the veto reason

### 3c. Radar Chart
Use Chart.js to render the 8-criteria radar chart:

```javascript
const ctx = document.getElementById('radarChart').getContext('2d');
new Chart(ctx, {
  type: 'radar',
  data: {
    labels: ['K1 Originality', 'K2 Argument', 'K3 Literature', 'K4 Discussion',
             'K5 Consistency', 'K6 Methodology', 'K7 Presentation', 'K8 Evidence'],
    datasets: [{
      label: 'Scores',
      data: [/* scores from evaluator JSON */],
      backgroundColor: 'rgba(44, 82, 130, 0.2)',
      borderColor: 'rgba(44, 82, 130, 1)',
      pointBackgroundColor: function(context) {
        // Color points by score: green (4-5), yellow (3), red (1-2)
        var score = context.dataset.data[context.dataIndex];
        if (score >= 4) return '#38a169';
        if (score >= 3) return '#d69e2e';
        return '#e53e3e';
      }
    }]
  },
  options: {
    scales: { r: { min: 0, max: 5, ticks: { stepSize: 1 } } },
    plugins: { legend: { display: false } }
  }
});
```

### 3d. Criteria Detail Cards
For each K1-K8 criterion, create a collapsible `<details>` section:
- Score badge: color-coded (green 4-5, yellow 3, red 1-2)
- Veto indicator: red "VETO" badge if `veto_triggered: true`
- Reasoning paragraph
- Suggestions as bulleted list

### 3e. Strengths
Bulleted list from `evaluator.strengths`.

### 3f. Areas for Improvement
Numbered list with issue and suggestion from `evaluator.areas_for_improvement`.

### 3g. Missing References Table

```html
<table>
  <thead>
    <tr><th>#</th><th>Author(s)</th><th>Title</th><th>Venue/Year</th><th>Citations</th><th>Why Relevant</th></tr>
  </thead>
  <tbody>
    <!-- Populate from missing-refs data -->
  </tbody>
</table>
```

### 3h. Section Notes
Brief observations per manuscript section from `evaluator.section_notes`.

### 3i. Citation Spot-Check
Table of 5 sampled citations with claim, cited source, and assessment.

### 3j. Methodology Note (footer)
"This review was generated using 8-criteria scoring with Veto Rules. Scores reflect the evaluator's assessment based on the manuscript text. Few-shot examples from similar published reviews were used for calibration when available."

## Step 4 — Write File

1. Write the HTML report to: `reports/{date}-peer-review-{slug}.html`
   - `{date}`: YYYY-MM-DD format
   - `{slug}`: kebab-case manuscript title, max 50 chars
2. Return the structured report data (file path + any warnings) for the critic-agent to validate.

## Language

All output is in English. Set `<html lang="en">`. Keep technical terms in original form (DOI, API names, journal names).

## Error Handling

| Condition | Action |
|---|---|
| Missing evaluator JSON | Stop and report: "Reporter requires evaluator output" |
| Missing-refs data absent | Generate report without missing-refs table; note omission |
| Chart.js CDN fails | Include `onerror` fallback: static score table replacing radar |
| Scores outside 1-5 range | Clamp to 1-5, note the anomaly |
