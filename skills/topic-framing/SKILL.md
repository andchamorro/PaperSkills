---
name: topic-framing
description: Help converge from a fuzzy academic idea to a concrete, researchable paper framing and title through structured dialogue. Produces a one-shot framing card in HTML by default, with Markdown as an explicit fallback. Use this skill whenever the user has a vague research idea, wants to turn a concept into a paper topic, needs help sharpening an academic title, or is exploring possible research directions. This skill walks through a 6-phase dialogue (seed capture, academic sharpening, literature positioning, framing synthesis, title workshop, output card) and produces a deliverable framing document.
---

# Topic Framing

Help the user converge from a fuzzy academic idea to a concrete, researchable paper framing and title. Input: "$ARGUMENTS".

## When to Use This Skill

- User has a "fuzzy idea" or concept and wants to turn it into a research topic
- User asks to "frame a paper topic about X", "sharpening a title", or "find a research gap"
- User provides a topic in another language and wants English framing
- User wants to test whether an idea is viable before committing to it
- User asks for "topic framing", "paper framing", or "research framing"

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
- Ask the user: "What's the seed idea or topic you'd like to frame?"
- Do NOT proceed without input

## Main Flow

```
Main Session — academic framing dialogue
  │
  ├── PHASE 1: Seed Capture — restate the initial idea as a research interest
  ├── PHASE 2: Academic Sharpening — six framing questions, one at a time
  ├── PHASE 3: Literature Positioning — quick scan to test whether the framing is viable
  ├── PHASE 4: Framing Synthesis — question, gap, contribution, boundaries
  ├── PHASE 5: Title Workshop — generate and refine academic title options
  └── PHASE 6: Output Framing Card
```

## Quick Phase Overview

### Phase 1: Seed Capture
Parse "$ARGUMENTS" and restate the idea in 2-3 sentences as an academic research interest. Avoid business/product language. Ask where the user is (A) broad topic, (B) tentative question, (C) multiple angles, (D) need title help.

### Phase 2: Academic Sharpening
Ask 6 questions ONE AT A TIME via AskUserQuestion:
1. Research Puzzle — what's the specific phenomenon/ tension?
2. Literature Location — which scholarly conversation?
3. Gap or Tension — what's missing/unresolved?
4. Core Contribution — what does it add to scholarship?
5. Unit of Analysis — what is being studied?
6. Boundaries — what is NOT claimed?

### Phase 3: Literature Positioning
Quick Semantic Scholar scan (3 queries) to test viability. Classify as: Saturated, Active but open, Fragmented, Emerging, or Poorly framed. Revise if weak.

### Phase 4: Framing Synthesis
Present compact framing for confirmation. Ask user to verify question, literature, contribution, and scope.

### Phase 5: Title Workshop
Generate 5 title candidates in different styles. Let user pick, then offer refinement.

### Phase 6: Output Framing Card
Default: HTML framing card → `artifacts/{date}-topic-framing-{topic-slug}.html`
Markdown fallback available.

## Error Handling

| Issue | Handling |
|-------|----------|
| Topic too broad | Narrow to one phenomenon, case, debate, or comparison |
| Topic too narrow/trivial | Widen from case to general analytical question |
| Wrong vocabulary | Propose better field terms based on literature scan |
| Gap already filled | Say directly, help reposition question |
| User impatient | Compress: "I only need puzzle, literature, contribution for sharp title" |

## Language

- If user explicitly requests a language: use that language
- Infer from prompt if not specified
- If user writes mainly in Chinese: dialogue and card in Chinese
- Otherwise: English default

When generating in Chinese: `<html lang="zh">`, Chinese headings/labels, Chinese punctuation.

## References

For detailed phase protocols, see `references/dialogue-protocol.md`.
For HTML template, see `references/html-template.md`.

## Token Budget

- Main session (dialogue): ~8-15K
- Literature scan (Phase 3): ~3-5K
- Framing synthesis + title workshop: ~2-3K
- HTML output: ~2-3K
- Total: ~15-26K