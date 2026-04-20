---
name: paper-orchestra
description: Orchestrate the full PaperOrchestra (Song et al., 2026, arXiv:2604.05018) five-agent pipeline to turn unstructured research materials (idea, experimental log, markdown template, conference guidelines, optional figures, optional references) into a submission-ready Markdown manuscript, with optional LaTeX export via pandoc. TRIGGER when the user asks to "write a paper from my experiments", "turn this idea and these results into a paper", "generate a conference submission", "run paper-orchestra on X", or otherwise wants the end-to-end paper-writing pipeline. Coordinates the outline, plotting, literature-review, section-writing, and content-refinement skills.
---

# PaperOrchestra

> **Source**: Song et al. (2026), "PaperOrchestra: A Multi-Agent Framework for Automated AI Research Paper Writing"

A multi-agent framework that autonomously transforms pre-writing materials into submission-ready manuscripts. This implementation is **Markdown-first**: the canonical manuscript is `manuscript.md`. LaTeX is a secondary export produced on demand.

## What This Skill Produces

A complete submission package written into `desk/final/`, plus a full audit trail under `desk/`:

```
desk/
├── ol.json              # Outline (Step 1)
├── fig/*.png            # Generated figures (Step 2)
├── fig/cc.json          # Caption context
├── refs.bib             # Verified citations (Step 3)
├── drafts/intro.md      # Introduction + Related Work (Step 3)
├── drafts/manuscript.md # Complete draft (Step 4)
├── refin/               # Refinement iterations (Step 5)
├── final/manuscript.md  # Accepted Markdown snapshot (canonical)
├── final/manuscript.tex # Optional LaTeX export (Step 6, if requested)
└── provenance.json      # Input/output hashes
```

## Inputs: The (I, E, T, G, F, R) Tuple

The desk MUST contain:

| File | Symbol | Required | Description |
|------|--------|----------|-------------|
| `desk/inputs/idea.md` | I | **Yes** | Idea Summary (Sparse or Dense variant) |
| `desk/inputs/log.md` | E | **Yes** | Experimental Log: setup, raw numeric data, observations |
| `desk/inputs/tmpl.md` | T | **Yes** | **Markdown template** with `#`/`##` section headings |
| `desk/inputs/gl.md` | G | **Yes** | Formatting rules, page limit, mandatory sections |
| `desk/inputs/fig/` | F | No | Optional pre-existing figures |
| `desk/inputs/ref/` | R | No | Optional pre-existing references |
| `desk/inputs/tmpl.tex` | — | No | Optional LaTeX template used only by the export step |

See `references/io-contract.md` for detailed format specifications.

## Pipeline Overview

See `references/pln.md` for the complete pipeline diagram.

```
Step 1: Outline           ──▶  ol.json                    (1 call)
Step 2: Plotting     ─┐
                     ├──▶  fig/*.png + cc.json           (~20-30 calls)
Step 3: Lit Review   ─┘                                  (~20-30 calls)
                         intro.md + refs.bib

Step 4: Section Writing  ──▶  drafts/manuscript.md       (1 call)
Step 5: Content Refine   ──▶  final/manuscript.md        (~5-7 calls)
Step 6: LaTeX Export     ──▶  final/manuscript.tex       (optional, 0 calls)
```

**Total: ~60-70 LLM calls, ~40 minutes latency**

Step 2 and Step 3 are independent and **MUST run in parallel** when your host supports parallel sub-agents. If not, run Step 3 first (longer wall time due to Semantic Scholar rate limits) then Step 2.

## Manuscript Authoring Conventions (Markdown)

All writing agents produce pandoc-flavored Markdown:

- **Sections**: `# Title`, `## Section`, `### Subsection` (no `\section{...}`).
- **Citations**: `[@BibKey]`, `[@Key1; @Key2]`. Legacy `\cite{Key}` is accepted by orphan-check but new output SHOULD use `[@Key]`.
- **Figures**: `![Caption](fig/fig_id.png){#fig:id}` and reference with `[@fig:id]` (pandoc-crossref). Keep figure files in `desk/fig/`.
- **Tables**: GitHub-flavored Markdown pipe tables, or pandoc grid tables for wide data. Label with `{#tbl:id}` when cross-referenced.
- **Math**: `$inline$` and `$$display$$` LaTeX math — pandoc passes these through to both HTML and LaTeX.
- **Metadata**: a YAML front-matter block at the top of `manuscript.md` with `title`, `author: [Anonymous Author(s)]`, `bibliography: ../refs.bib`, and any template knobs (documentclass, classoption) for the optional LaTeX export.

## Critical Pre-Instruction

Before any LLM call that *writes* manuscript content, you MUST prepend the **Anti-Leakage Prompt** from `references/anti-leakage-prompt.md` to your system prompt.

## Step-by-Step Execution

### 0. Scaffold, Check, and Validate

```bash
python scripts/init.py --out desk/
python scripts/validate.py --desk desk/
```

**Before failing on missing inputs**, check whether aggregation can supply them:

| Inputs State | Action |
|--------------|--------|
| `idea.md` and `log.md` both present and non-empty | Continue to Step 1 |
| Either missing/empty, user mentioned a directory | Ask to run research aggregator on that directory |
| Either missing/empty, no directory mentioned | Ask user: "Your desk is missing `idea.md` / `log.md`. Do you have a folder with research notes I can aggregate from?" |

If validation still fails after aggregation, stop and tell the user exactly which files remain outstanding.

### 1. Outline Generation (1 LLM call)

Invoke `skills/outline-agent` with:
- `desk/inputs/idea.md`
- `desk/inputs/log.md`
- `desk/inputs/tmpl.md`
- `desk/inputs/gl.md`

**Output:** `desk/ol.json`

**HALT if outline-agent validation fails** — every downstream agent depends on this schema.

### 2 ∥ 3. Plotting and Literature Review (in parallel)

Parse `ol.json`. Extract:
- `outline.plotting_plan` → drives Step 2
- `outline.intro_related_work_plan` → drives Step 3

**If parallel sub-agents supported**, spawn two concurrent sub-tasks:

**Sub-task A (Step 2):** Invoke `skills/plotting-agent`
- Input: `ol.json.plotting_plan`, `idea.md`, `log.md`
- Output: `desk/fig/*.png`, `desk/fig/cc.json`

**Sub-task B (Step 3):** Invoke `skills/literature-review`
- Input: `ol.json.intro_related_work_plan`, `idea.md`, `log.md`
- Output: `desk/drafts/intro.md` (Markdown), `desk/refs.bib`

**If parallel NOT supported**, run Sub-task B first (slower due to Semantic Scholar 1 QPS limit), then Sub-task A.

### 4. Section Writing (CRITICAL: ONE single call)

Invoke `skills/section-writing` with:
- `ol.json`
- `idea.md`, `log.md`
- `intro.md` (preserve verbatim from Step 3)
- `refs.bib`
- `gl.md`
- Actual figure image files from `desk/fig/` (multimodal input)

**Output:** `desk/drafts/manuscript.md` (pandoc-flavored Markdown).

**Post-generation validation:**

```bash
python scripts/citation_tool.py orphan-check desk/drafts/manuscript.md desk/refs.bib
python scripts/markdown_sanity.py desk/drafts/manuscript.md
python scripts/anti_leakage_check.py desk/drafts/manuscript.md
```

If any validation fails, re-prompt the writing step with the error report before proceeding.

### 5. Content Refinement (~3 iterations, ~5-7 calls)

Invoke `skills/content-refinement-agent` with:
- `desk/drafts/manuscript.md`
- `desk/inputs/gl.md`
- `desk/inputs/log.md`
- `desk/refs.bib`
- Empty `worklog.json` initially

The skill implements the loop with strict halt rules from `references/halt-rules.md`.

**Halt conditions** (any one triggers stop):

1. Iteration count reaches cap (default 3)
2. Overall score **decreases** → revert to previous, halt
3. Overall score **ties** but net sub-axis change negative → revert, halt
4. Reviewer issues no new actionable weaknesses

**Output:**
- `desk/refin/worklog.json`
- `desk/refin/iter<N>/manuscript.md` (for each iteration)
- `desk/final/manuscript.md` (accepted Markdown snapshot — the canonical artifact)

### 6. Optional LaTeX Export (on request, 0 LLM calls)

Run only if the user asked for a `.tex`/PDF artifact or a conference submission that mandates LaTeX:

```bash
python scripts/export_latex.py --desk desk/
```

- Uses **pandoc** to convert `desk/final/manuscript.md` → `desk/final/manuscript.tex`.
- If `desk/inputs/tmpl.tex` exists, it is passed to pandoc via `--template`; otherwise pandoc's built-in default template is used.
- If `pandoc` is not on PATH, the script exits non-zero with a clear message and leaves the Markdown outputs untouched.
- Optional `--pdf` flag additionally invokes `pandoc --pdf-engine=xelatex` (falls back with a clear message if no LaTeX toolchain is installed).

Post-export, you may optionally run `python scripts/latex_sanity.py desk/final/manuscript.tex` on the generated `.tex`.

### 7. Provenance Snapshot

```bash
python scripts/snapshot.py --desk desk/
```

**Output:** `desk/provenance.json` with SHA-256 hashes of all inputs and outputs (including any exported `.tex`/`.pdf`).

### 8. Report to User

Summarize:
- Path to `desk/final/manuscript.md` (always)
- Path to `desk/final/manuscript.tex` / `.pdf` (if export was requested)
- Sections drafted
- Citation count
- Refinement iterations completed
- Any gates that failed mid-pipeline

## Cost Budget

| Step | Agent | Calls |
|------|-------|-------|
| 1 | Outline Agent | 1 |
| 2 | Plotting Agent | ~20-30 |
| 3 | Literature Review Agent | ~20-30 |
| 4 | Section Writing Agent | 1 |
| 5 | Content Refinement Agent | ~5-7 |
| 6 | LaTeX Export (pandoc) | 0 |
| **Total** | | **~60-70** |

Mean latency: 39.6 minutes (from manuscript benchmarks)

## Security
scripts/export_latex.py integrates pandoc via subprocess under strict Socket.dev compliance:

* Injection Prevention: Mandates shell=False and explicit argument lists; execution is locked to the fixed "pandoc" binary.
* Path Sandboxing: All I/O paths (input, output, templates, bib) are resolved and strictly validated against the base directory; violations trigger immediate ValueError.
* Extension Lockdown: Hard whitelisting limits processing to .md, .tex, .pdf, and .bib files.
* Automated Audit: Compliance is enforced by tests/test_socket_security.py using pytest.

## Resources

- `references/io-contract.md` — Input formats and desk layout
- `references/pln.md` — Pipeline diagram and step details
- `references/halt-rules.md` — Content refinement halt conditions
- `references/anti-leakage-prompt.md` — Anti-leakage instructions (prepend to all writing calls)
- `scripts/init.py` — Scaffold project desk
- `scripts/validate.py` — Validate inputs before running
- `scripts/anti_leakage_check.py` — Check for leaked author info
- `scripts/citation_tool.py` — Unified citation tool (orphan-check, verify, smoke-test); understands pandoc `[@key]` and `\cite{key}`
- `scripts/markdown_sanity.py` — Validate Markdown manuscript structure
- `scripts/latex_sanity.py` — Validate LaTeX structure (run only against exported `.tex`)
- `scripts/export_latex.py` — Pandoc-based Markdown → LaTeX/PDF exporter (hardened; see Security section)
- `scripts/snapshot.py` — Create provenance snapshot

## Sub-Skills

- `skills/outline-agent/` — Step 1: Generate structured outline
- `skills/plotting-agent/` — Step 2: Generate figures
- `skills/literature-review/` — Step 3: Search, verify, and draft lit review (Markdown)
- `skills/section-writing/` — Step 4: Draft remaining sections (Markdown)
- `skills/content-refinement-agent/` — Step 5: Iterative refinement (Markdown)
