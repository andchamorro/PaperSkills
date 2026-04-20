# PaperOrchestra Pipeline Specification

> **Source**: Song et al. (2026), PaperOrchestra, §Method and Appendix B

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INPUTS                                         │
│  idea.md (I)  │  log.md (E)  │  tmpl.md (T)  │  gl.md (G)  │  fig/ (F)  │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STEP 1: OUTLINE GENERATION                           │
│                         (Outline Agent, 1 call)                          │
│                                                                          │
│  Input:  I, E, T, G                                                      │
│  Output: ol.json (plotting_plan, intro_related_work_plan, section_plan) │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │         PARALLEL            │
                    ▼                             ▼
┌───────────────────────────────┐  ┌───────────────────────────────────────┐
│   STEP 2: PLOT GENERATION     │  │   STEP 3: LITERATURE REVIEW            │
│     (Plotting Agent)          │  │     (Literature Review Agent)          │
│     (~20-30 calls)            │  │     (~20-30 calls)                     │
│                               │  │                                        │
│  Input:  ol.json.plotting_plan│  │  Input:  ol.json.intro_related_work_plan│
│          I, E                 │  │          I, E                          │
│  Output: fig/*.png            │  │  Output: drafts/intro.md               │
│          fig/cc.json          │  │          refs.bib                      │
└───────────────────┬───────────┘  └───────────────────┬───────────────────┘
                    │                                   │
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STEP 4: SECTION WRITING                              │
│                   (Section Writing Agent, 1 call)                        │
│                                                                          │
│  Input:  ol.json, I, E, drafts/intro.md, refs.bib, G, fig/*             │
│  Output: drafts/manuscript.md                                            │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   STEP 5: CONTENT REFINEMENT                             │
│                (Content Refinement Agent, ~5-7 calls)                    │
│                                                                          │
│  Loop:  Until halt condition (max 3 iterations)                          │
│  Input:  manuscript.md, G, E, worklog.json, refs.bib, reviewer_feedback │
│  Output: refin/iter<N>/manuscript.md → final/manuscript.md              │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTPUTS                                        │
│  final/manuscript.md (canonical)  │  final/manuscript.tex? (pandoc)       │
│  provenance.json                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## LLM Call Budget

| Step | Agent | Calls | Notes |
|------|-------|-------|-------|
| 1 | Outline Agent | 1 | Initial manuscript structuring and planning |
| 2 | Plotting Agent | ~20-30 | Few-shot retrieval, visual planning, generation, VLM critique cycles, captioning |
| 3 | Literature Review Agent | ~20-30 | Parallel candidate discovery (10 workers), sequential citation verification (1 QPS) |
| 4 | Section Writing Agent | **1** | Single comprehensive multimodal call |
| 5 | Content Refinement Agent | ~5-7 | Score-driven iterative revision (max 3 iterations × 2-3 calls each) |
| 6 | LaTeX Export (pandoc) | 0 | Optional: Markdown → `.tex`/`.pdf` only if requested |
| **Total** | | **~60-70** | Mean latency: 39.6 minutes |

---

## Parallelization Strategy

### Step 2 ∥ Step 3

These steps are **independent** and **MUST run in parallel** when the host supports concurrent sub-agents.

**If parallel execution is NOT supported:**
1. Run Step 3 first (longer wall-clock due to Semantic Scholar rate limits)
2. Then run Step 2

The artifacts are independent, so execution order does not affect correctness.

### Within Step 3: Literature Search

The literature search pipeline is internally parallelized:

1. **Parallel Candidate Discovery** (10 concurrent workers)
   - Search-grounded LLM calls to rapidly pool candidate papers
   - Leverages high concurrency tolerance of LLM APIs

2. **Sequential Citation Verification** (1 QPS)
   - Processes pooled candidates through Semantic Scholar API
   - Respects the maximum allowable rate (1 query per second)
   - Prevents quota-induced latency

---

## Step Details

### Step 1: Outline Generation

The Outline Agent synthesizes all inputs into a structured JSON outline:

**Directive 1: Plotting & Visualization Plan**
- Identify essential figures to prove the hypothesis
- Specify plot types, data sources, aspect ratios

**Directive 2: Research Graph & Investigation Strategy**
- Introduction Strategy: Macro-level context (10-20 papers)
- Related Work Strategy: Micro-level technical baselines (30-50 papers)
- Strict separation to prevent citation overlap

**Directive 3: Section Writing Plan**
- Structural hierarchy for all sections
- Content specificity with source material references
- EXHAUSTIVE citation hints for all external dependencies

### Step 2: Plot Generation

Uses PaperBanana (Zhu et al., 2026) as the default module:
- Closed-loop refinement system
- VLM critic evaluates rendered images against design objectives
- Iterative revision to resolve visual artifacts
- Context-aware caption synthesis

### Step 3: Literature Review

Hybrid discovery pipeline:
- Web search to identify candidate papers
- Semantic Scholar API to authenticate existence
- Temporal cutoff enforcement
- Deduplication via Semantic Scholar IDs
- Auto-generated BibTeX file
- Drafts Introduction and Related Work sections

**Critical Rules:**
- Do not cite papers after the cutoff date
- Treat post-cutoff papers as concurrent work
- Do not claim SOTA over papers not in experimental_log

### Step 4: Section Writing

**Single call** that receives:
- Complete outline (`ol.json`)
- Source materials (`idea.md`, `log.md`)
- Pre-written sections (`intro.md`, Markdown)
- Citation map (`refs.bib`)
- Conference guidelines (`gl.md`)
- Generated figures (multimodal input)

**Critical Rules:**
- Output is **pandoc-flavored Markdown** (`drafts/manuscript.md`)
- Preserve existing content (Introduction, Related Work)
- Extract numeric data directly from log (no hallucination)
- Use exact citation keys from citation map via `[@key]` syntax
- Include ALL provided figures with `![caption](fig/<id>.png){#fig:<id>}`
- Match the heading structure of `tmpl.md`

### Step 5: Content Refinement

Uses AgentReview (Jin et al., 2024) as the default reviewer system.

**Loop mechanics:**
1. Receive reviewer feedback (Strengths, Weaknesses, Questions)
2. Analyze and deconstruct into editing tasks
3. Revise sections to address weaknesses
4. Integrate answers directly into manuscript
5. Check against halt conditions
6. Accept or revert based on score delta

**Critical Rules:**
- Operate directly on the Markdown manuscript — never convert to LaTeX mid-loop
- Ignore requests for new experiments (not in experimental_log)
- Never explicitly state limitations (prevents reward hacking)
- All numerical claims must match experimental_log
- Use only citations from citation_map.json

### Step 6: LaTeX Export (optional, pandoc)

Produced only if the user asks for a `.tex` or `.pdf`:

- `scripts/export_latex.py --desk desk/` converts `final/manuscript.md` → `final/manuscript.tex`.
- If `desk/inputs/tmpl.tex` exists, it is passed to pandoc via `--template`; otherwise pandoc defaults apply.
- If pandoc is missing, the script prints a clear error and exits non-zero — the Markdown manuscript remains the authoritative artifact.
- Add `--pdf` to additionally build a PDF; missing LaTeX engines degrade gracefully.
