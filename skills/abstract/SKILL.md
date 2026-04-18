---
name: abstract
description: >
  Generate structured and unstructured abstracts (IMRaD, thematic, extended,
  short, single-paragraph) for academic manuscripts in any discipline. Produces
  multiple word-count variants (50-75, 150, 250, 500 words) with keyword sets.
  Use when the
  user asks to write, draft, generate, or improve an abstract for a paper,
  thesis, dissertation, or conference submission. Do NOT use for literature
  reviews, annotated bibliographies, executive summaries of non-academic
  documents, book reports, or press releases. Do NOT use when the user wants to
  summarize a paper for personal reading notes — that is a summarization task,
  not an abstract.
---

Generate an abstract for "$ARGUMENTS".

## FILE RESOLUTION

1. If the argument is a filename only, resolve it relative to the current
   working directory.
2. If the argument is a full path, use it as-is.
3. Do NOT use sub-agents — this is a pure LLM task.

---

## STEP 0 — RETRIEVE SIMILAR ABSTRACTS (few-shot)

Find 3-5 high-impact abstracts from the same field as few-shot examples. This is the PapervizAgent Retriever→Planner pattern: retrieved examples guide field-appropriate abstract generation.

1. After reading the manuscript (Step 1), extract: title, 5 keywords, discipline.
2. Run the retrieval script:
   ```
   python scripts/find_similar_abstracts.py --field "{discipline}" --keywords "{keywords}" --limit 5
   ```
3. The script returns a JSON array with each example's abstract, word count, format (structured/unstructured), and venue.
4. Use these examples to:
   - Match the field's abstract conventions (structured vs. unstructured, typical length).
   - Adopt discipline-appropriate terminology and phrasing patterns.
   - Calibrate the level of technical detail for the target audience.
5. If the script returns empty (API failure or no results), proceed without few-shot examples — the built-in format templates are sufficient.

**Fallback:** If Semantic Scholar is unavailable, skip this step entirely. Few-shot examples are optional enrichment.

## STEP 1 — READ MANUSCRIPT

1. Open the manuscript with the Read tool.
2. If the file is empty or unreadable, **STOP** and report the error
   (see [Error Handling](#error-handling)).
3. Extract the following elements:
   - Title
   - Research question or thesis statement
   - Methodology (if applicable)
   - Key arguments or findings
   - Conclusion or contribution
4. If the manuscript contains an existing abstract, save it verbatim for
   comparison in Step 6.

## STEP 2 — DETECT DISCIPLINE AND CHOOSE FORMAT

Examine the manuscript content and determine the discipline:

| Signal                                  | Classification        |
|-----------------------------------------|-----------------------|
| Empirical data, experiments, stats      | **STEM / empirical**  |
| Argumentation, close reading, theory    | **Humanities / theoretical** |
| Mixed or unclear                        | **Ambiguous**         |

- **STEM / empirical** → select IMRaD format (Step 3-A).
- **Humanities / theoretical** → select thematic format (Step 3-B).
- **Ambiguous** → generate BOTH formats (Steps 3-A and 3-B) and let the
  user choose.

## STEP 3 — GENERATE VARIANTS

Generate every applicable variant below. After generating each variant, run
the word-count validation script:

```bash
python scripts/word_count.py <file> --target <N> --tolerance 20
```

### 3-A. Structured Abstract — IMRaD (~250 words)

Use for STEM / empirical manuscripts.

```
Background:    [1-2 sentences]
Objective:     [1 sentence]
Methods:       [1-2 sentences]
Results:       [2-3 sentences]
Conclusion:    [1-2 sentences]
Keywords:      [5-7 terms]
```

### 3-B. Structured Abstract — Thematic (~250 words)

Use for humanities / theoretical manuscripts.

```
Context:       [1-2 sentences — why this topic matters]
Thesis:        [1 sentence — central argument]
Approach:      [1-2 sentences — methodology, scope, sources]
Argument:      [2-3 sentences — key reasoning steps]
Contribution:  [1-2 sentences — what this adds to the field]
Keywords:      [5-7 terms]
```

### 3-C. Unstructured Abstract (~150 words)

Single narrative paragraph. No section headings.

### 3-D. Extended Abstract (~500 words)

Conference-submission style. May include sub-headings.

### 3-E. Short Abstract (~50-75 words)

Suitable for indexing and cataloging services.

## STEP 4 — QUALITY CHECKS

Run the automated quality-check script on each generated abstract:

```bash
python scripts/quality_check.py <abstract_file> --format imrad|thematic
```

The script validates:
- No first-person pronouns (unless a documented discipline norm)
- No citation patterns (brackets `[1]`, parenthetical `(Author, Year)`)
- Word count within tolerance of target
- Standalone readability (heuristic)

Review the JSON output. If any check fails, revise the abstract and re-run
until all checks pass.

### Manual verification checklist

After the script passes, confirm these semantic criteria:

- [ ] Contains the main research question
- [ ] States methodology or approach
- [ ] Mentions key findings or arguments
- [ ] Does NOT include information absent from the manuscript
- [ ] Keywords are specific enough for discoverability

## STEP 5 — PRESENT RESULTS

1. Display every generated variant with its word count.
2. If the manuscript had an existing abstract, show a side-by-side comparison
   highlighting differences.
3. Prompt the user:
   - "Which format fits your target journal or conference?"
   - "Need a specific word-count limit?"
   - "Search keyword usage in the literature? (`/lit-search {keywords}`)"

---

## ERROR HANDLING

| Condition                              | Action                                                        |
|----------------------------------------|---------------------------------------------------------------|
| File is empty or unreadable            | Report: "The file could not be read or is empty." **STOP.**   |
| Manuscript < 500 words                 | Warn: "Manuscript is very short (<500 words). The abstract may lack detail." Proceed but flag output as provisional. |
| Ambiguous discipline                   | Generate BOTH IMRaD and thematic variants (see Step 2).       |
| Non-UTF-8 encoding detected            | Attempt re-read with Latin-1 fallback. If still unreadable, ask user for encoding. |
| Unrecognized manuscript language        | Ask user to confirm the language. English output only — see `.paperskills/legacy/atomic_language_support.md` for prior bilingual behavior. |
| quality_check.py reports failures       | Revise the failing abstract and re-run. Max 3 revision cycles; then present best effort with caveats. |

---

## NOTES

- No external API calls required.
- Total token budget: ~10-20 K depending on manuscript length.
- All script paths are relative to the skill directory (`scripts/`).
