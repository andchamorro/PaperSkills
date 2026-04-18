# Peer Review Report Template

Reference for HTML report design in peer-review skill.

## Design System

The peer-review HTML report MUST follow the design system in `assets/report-template.md` from the paperskills root directory. This includes:

- Custom CSS variables (no Tailwind)
- Crimson Pro font for academic book aesthetic
- Professional, publication-ready styling

## Radar Chart

Use Chart.js for the 8-criteria radar:

```javascript
const ctx = document.getElementById('radarChart').getContext('2d');
new Chart(ctx, {
  type: 'radar',
  data: {
    labels: ['K1 Originality', 'K2 Argument', 'K3 Literature', 'K4 Discussion', 
             'K5 Consistency', 'K6 Methodology', 'K7 Presentation', 'K8 Evidence'],
    datasets: [{
      label: 'Scores',
      data: [4, 3, 4, 3, 5, 4, 3, 4],
      backgroundColor: 'rgba(44, 82, 130, 0.2)',
      borderColor: 'rgba(44, 82, 130, 1)',
      pointBackgroundColor: 'rgba(44, 82, 130, 1)'
    }]
  },
  options: {
    scales: {
      r: {
        min: 0,
        max: 5,
        ticks: { stepSize: 1 }
      }
    }
  }
});
```

## Color Coding

| Score Range | Color | RGB |
|-------------|-------|-----|
| 4-5 (good) | Green | #38a169 |
| 3 (acceptable) | Yellow | #d69e2e |
| 1-2 (poor) | Red | #e53e3e |

## Sections

1. **Header** — Title "Peer Review Report", manuscript title, date
2. **Summary** — Overall recommendation badge, brief summary
3. **Radar Chart** — Visual 8-criteria display
4. **Criteria Details** — Expandable sections for each K1-K8
5. **Strengths** — Bulleted list
6. **Areas for Improvement** — Numbered with suggestions
7. **Missing References** — Table with why-relevant column
8. **Section Notes** — Per-section observations
9. **Citation Spot-Check** — Sampled citations with assessment

## Recommendation Badges

| Recommendation | Badge Style |
|----------------|-------------|
| Accept | Green: "ACCEPT" |
| Minor Revisions | Yellow: "MINOR REVISIONS" |
| Major Revisions | Orange: "MAJOR REVISIONS" |
| Reject | Red: "REJECT" |