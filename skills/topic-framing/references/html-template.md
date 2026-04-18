# HTML Framing Card Template

Template for the HTML output in Phase 6 of topic-framing.

## Structure

```html
<!DOCTYPE html>
<html lang="{en|zh}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Topic Framing Card - {short topic}</title>
  <style>
    :root {
      --bg: #fafafa;
      --card-bg: #ffffff;
      --text: #333;
      --text-light: #666;
      --accent: #2c5282;
      --border: #e2e8f0;
      --code-bg: #f7fafc;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2rem;
    }
    .container { max-width: 800px; margin: 0 auto; }
    header {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    header h1 {
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-light);
      margin-bottom: 0.5rem;
    }
    header .title {
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--accent);
    }
    header .date { color: var(--text-light); font-size: 0.875rem; margin-top: 0.5rem; }
    section {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    section h2 {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
    }
    .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 0.75rem; }
    .label { font-weight: 500; color: var(--text-light); font-size: 0.875rem; }
    .value { color: var(--text); }
    .snapshot {
      background: var(--code-bg);
      padding: 1rem;
      border-radius: 4px;
      font-size: 0.875rem;
    }
    .titles { list-style: none; }
    .titles li { padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
    .titles li:last-child { border-bottom: none; }
    .titles .selected {
      background: var(--code-bg);
      padding: 0.5rem;
      border-radius: 4px;
      font-weight: 500;
    }
    .titles .selected::before { content: "✓ "; color: #38a169; }
    @media print {
      body { background: white; padding: 0; }
      section { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Topic Framing Card</h1>
      <div class="title">{confirmed title}</div>
      <div class="date">{YYYY-MM-DD}</div>
    </header>

    <section>
      <h2>Executive Summary</h2>
      <p>{2-4 sentence synthesis of the framing}</p>
    </section>

    <section>
      <h2>Academic Framing</h2>
      <div class="grid">
        <div class="label">Working Question</div>
        <div class="value">{one clear research question}</div>

        <div class="label">Research Puzzle</div>
        <div class="value">{what is puzzling or unresolved}</div>

        <div class="label">Primary Literature</div>
        <div class="value">{the conversation this paper enters}</div>

        <div class="label">Gap / Tension</div>
        <div class="value">{what is missing, unclear, or contested}</div>

        <div class="label">Contribution Claim</div>
        <div class="value">{what the paper contributes to scholarship}</div>

        <div class="label">Unit of Analysis</div>
        <div class="value">{what is being analyzed}</div>

        <div class="label">Scope (IN)</div>
        <div class="value">{what is IN}</div>

        <div class="label">Non-scope (OUT)</div>
        <div class="value">{what is OUT}</div>
      </div>
    </section>

    <section>
      <h2>Literature Snapshot</h2>
      <div class="snapshot">
        <p><strong>Related papers (2020-2026):</strong> {N}</p>
        <p><strong>Anchor paper:</strong> "{title}" ({year}, {citations} citations)</p>
        <p><strong>Positioning:</strong> {Saturated / Active but open / Fragmented / Emerging}</p>
        <p><strong>Assessment:</strong> {1-2 sentence judgment}</p>
      </div>
    </section>

    <section>
      <h2>Candidate Titles Considered</h2>
      <ol class="titles">
        <li class="selected">{selected title}</li>
        <li>{title}</li>
        <li>{title}</li>
        <li>{title}</li>
        <li>{title}</li>
      </ol>
    </section>
  </div>
</body>
</html>
```

## Field Mapping

| Variable | Source |
|----------|--------|
| `{en\|zh}` | Language from Phase 1 |
| `{short topic}` | Slugified version of seed idea |
| `{confirmed title}` | Phase 5 final selection |
| `{YYYY-MM-DD}` | Current date |
| `{2-4 sentence synthesis}` | Phase 4 synthesis condensed |
| `{research question}` | Q1 + Q3 combined |
| `{research puzzle}` | Q1 response |
| `{primary literature}` | Q2 response |
| `{gap/tension}` | Q3 response |
| `{contribution}` | Q4 response |
| `{unit of analysis}` | Q5 response |
| `{scope IN/OUT}` | Q6 responses |
| `{literature snapshot}` | Phase 3 output |
| `{candidate titles}` | Phase 5 generation with selection |

## Markdown Fallback Template

If user explicitly requests markdown:

```markdown
# Topic Framing Card

**Title:** {confirmed title}
**Date:** {YYYY-MM-DD}

## Executive Summary
{2-4 sentence synthesis}

## Working Question
{the sharpened research question}

## Research Puzzle
{what is puzzling or unresolved}

## Primary Literature
{which scholarly conversation}

## Gap / Tension
{what is missing/unclear/contested}

## Contribution Claim
{what this adds to scholarship}

## Unit of Analysis
{what is being studied}

## Scope
**IN:** {what is covered}
**OUT:** {what is explicitly excluded}

## Literature Snapshot
- Related papers (2020-2026): {N}
- Anchor: "{title}" ({year})
- Positioning: {classification}

## Candidate Titles
1. {selected title} ←
2. {title}
3. {title}
4. {title}
5. {title}
```