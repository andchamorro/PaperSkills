---
name: topic-framing
description: Converges a fuzzy academic idea into a concrete, researchable paper framing and title through a structured 6-step dialogue. Produces an HTML framing card by default (Markdown on explicit request). Use when the user has a vague research idea, wants to sharpen a title, or needs to test framing viability. Don't use for full literature review, detailed method design, manuscript drafting, or citation verification.
---

Converge the user's fuzzy academic idea into a concrete, researchable paper framing and title. Input: "$ARGUMENTS".

## Input Format

Input may specify:
- **Seed idea**: keyword, topic area, puzzle, case, debate, or half-formed question
- **Goal**: sharpen question, test framing viability, improve literature positioning, or finalize a title
- **Output**: HTML framing card, markdown framing card, or short in-chat framing summary

Examples:
- `frame a paper topic about AI search ads and advertiser strategy`
- `帮我把"平台算法治理"收敛成一个可写论文题目`
- `turn this fuzzy idea into a researchable title and output html`

## Validation

**IMPORTANT:** If "$ARGUMENTS" is empty or only whitespace:
1. Ask the user: "What's the seed idea or topic you'd like to frame?"
2. Do NOT proceed until a non-empty seed idea is provided.

## Main Flow

```
Main Session — academic framing dialogue
  │
  ├── Step 1: Seed Capture — restate the initial idea as a research interest
  ├── Step 2: Academic Sharpening — six framing questions, one at a time
  ├── Step 3: Literature Positioning — quick scan to test viability
  ├── Step 4: Framing Synthesis — question, gap, contribution, boundaries
  ├── Step 5: Title Workshop — generate and refine academic title options
  └── Step 6: Output Framing Card — write HTML or Markdown deliverable
```

## Step 1: Seed Capture

1. Parse "$ARGUMENTS" and extract language preference (explicit request or inferred from prompt).
2. Extract output format preference (HTML card, markdown card, or in-chat summary). Default to HTML.
3. Restate the idea in 2-3 sentences as an academic research interest. Avoid business/product language.
4. Ask the user via AskUserQuestion:
   > I understand your current research interest roughly as: "{restatement}".
   > Which best describes where you are now?
   > A) I only have a broad topic or phenomenon
   > B) I have a tentative research question
   > C) I have several possible academic angles
   > D) I mostly need help sharpening the title

5. Route to Step 2 accordingly: A → all six questions; B → Q2-Q6; C → collect angles first, then Q2-Q6 on strongest; D → verify Q3-Q6, then skip to Step 5.

## Step 2: Academic Sharpening

Ask 6 questions ONE AT A TIME via AskUserQuestion. Wait for each answer before proceeding. For detailed question scripts, push-until criteria, and good/bad examples, read `references/dialogue-protocol.md`.

1. **Research Puzzle** — what specific phenomenon, tension, or underexplained pattern?
2. **Literature Location** — which 1-2 scholarly conversations does this paper enter?
3. **Gap or Tension** — what is missing, unresolved, or conflated in that literature?
4. **Core Contribution** — what does this paper add to scholarship? (A-G options)
5. **Unit of Analysis** — what is being studied? (texts, cases, organizations, etc.)
6. **Boundaries** — what does this paper explicitly NOT claim or cover?

**Smart-skip:** If "$ARGUMENTS" or earlier answers already cover a question clearly, skip it.
**Escape hatch:** If the user becomes impatient, compress to puzzle + literature + contribution only.

## Step 3: Literature Positioning

1. Generate 3 search queries: (a) direct research question, (b) main scholarly conversation, (c) gap-focused with "review"/"debate"/"framework" terms.
2. For each query, fetch via Semantic Scholar:
   ```
   GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=10&fields=title,authors,year,citationCount,abstract&year=2020-2026
   ```
3. If Semantic Scholar fails, fall back to OpenAlex:
   ```
   GET https://api.openalex.org/works?search={query}&per_page=10&mailto=paperskills@example.com
   ```
4. If both APIs fail, note "Literature positioning unavailable — manual verification recommended" and proceed to Step 4.
5. Classify the framing as: **Saturated**, **Active but open**, **Fragmented**, **Emerging**, or **Poorly framed**.
6. If framing is weak or saturated, revise before moving on (narrow phenomenon, shift to specific debate, replace generic novelty).

## Step 4: Framing Synthesis

1. Present a compact framing summary for confirmation. For the exact template, see `references/dialogue-protocol.md` Phase 4.
2. Ask via AskUserQuestion: Does this capture the paper? (A) Yes → Step 5; (B-E) specific adjustment needed.
3. If B/C/D/E: revise and re-present until confirmed.

## Step 5: Title Workshop

1. Generate 5 academic title candidates covering styles: direct descriptive, question-driven, concept-first, case-and-claim, two-part subtitle.
2. Present via AskUserQuestion. If user picks "None — different emphasis", ask what emphasis is missing and generate 3 revised options.
3. Once selected, offer one final refinement pass.

## Step 6: Output Framing Card

1. Run `python scripts/slugify.py "{seed idea or confirmed title}"` to generate the topic slug for the output filename.
2. Write the framing card to `artifacts/{date}-topic-framing-{topic-slug}.html` (or `.md` if user explicitly requested Markdown). Read `references/html-template.md` for the HTML template and field mapping.
3. Return the exact absolute file path to the user.
4. Ask whether they want it opened. Only run `open {file_path}` after the user explicitly confirms.

## Token Budget

- Steps 1-2 (dialogue): ~8-15K
- Step 3 (literature scan): ~3-5K
- Steps 4-5 (synthesis + titles): ~2-3K
- Step 6 (output): ~2-3K
- **Total: ~15-26K**

## Error Handling

| Issue | Handling |
|-------|----------|
| Empty or whitespace input | Ask user for seed idea; do not proceed without it |
| Topic too broad | Narrow to one phenomenon, case, debate, or comparison |
| Topic too narrow or trivial | Widen from case description to a general analytical question |
| Wrong vocabulary | Propose better field terms based on literature scan results |
| Gap already filled | State directly; help reposition the question |
| User impatient or unresponsive | Compress: "I only need puzzle, literature, contribution for a sharp title" |
| Semantic Scholar API failure | Fall back to OpenAlex; if both fail, note unavailability and proceed |
| Slugify script failure | Fall back to lowercase-hyphenated title manually |

## References

- Detailed phase protocols, question scripts, good/bad examples: `references/dialogue-protocol.md`
- HTML template and field mapping: `references/html-template.md`
