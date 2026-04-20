# I/O Contract for PaperOrchestra

> **Source**: Song et al. (2026), PaperOrchestra, §Task and Dataset

This document specifies the exact input format, desk layout, and output expectations for the PaperOrchestra pipeline.

---

## Task Formulation

The framework maps unconstrained pre-writing materials to a complete submission package:

```
P = (P_md, P_tex?, P_pdf?) = W(I, E, T, G, F, R)
```

Where:
- `W` = the PaperOrchestra framework
- `P_md` = the **canonical Markdown manuscript** (`desk/final/manuscript.md`)
- `P_tex` = the exported LaTeX source, produced on demand by `scripts/export_latex.py` (pandoc)
- `P_pdf` = the rendered PDF, produced on demand via `pandoc --pdf-engine=xelatex`

---

## Input Components

| Symbol | File | Required | Description |
|--------|------|----------|-------------|
| `I` | `desk/inputs/idea.md` | **Yes** | Idea Summary - methodology, core contributions, theoretical foundation |
| `E` | `desk/inputs/log.md` | **Yes** | Experimental Log - raw data, ablations, metrics |
| `T` | `desk/inputs/tmpl.md` | **Yes** | **Markdown** section skeleton (pandoc-flavored) with `#`/`##` headings and an optional YAML front-matter block |
| `G` | `desk/inputs/gl.md` | **Yes** | Conference guidelines (page limits, mandatory sections) |
| `F` | `desk/inputs/fig/` | No | Optional pre-existing figures |
| `R` | `desk/inputs/ref/` | No | Optional pre-existing references |
| —   | `desk/inputs/tmpl.tex` | No | Optional pandoc LaTeX template used only by the export step; if absent, pandoc defaults are used |

---

## Idea Summary Variants

The manuscript supports two variants of the Idea Summary:

### Sparse Variant
High-level summary only:
- Problem statement
- Core hypothesis
- Proposed methodology (high-level)
- Expected contribution

### Dense Variant
Retains formal definitions and LaTeX equations:
- All of Sparse variant, plus:
- Mathematical formulations
- Loss functions
- Algorithm pseudocode

Both variants MUST be:
- Fully anonymized (no author names, affiliations)
- Self-contained (no citations, URLs, or figure references)
- Methodology-focused (excluding experimental results)

---

## Experimental Log Format

The log contains:

1. **Experimental Setup**
   - Datasets used (names, sizes, splits)
   - Evaluation metrics
   - Baselines compared
   - Implementation details (hardware, optimizer, hyperparameters)

2. **Raw Numeric Data**
   - Performance tables with exact values
   - Ablation study results
   - Hyperparameter sensitivity analysis

3. **Qualitative Observations**
   - Analysis of results
   - Comparison with baselines
   - Visual qualitative analysis

---

## Desk Layout

```
desk/
├── inputs/                          # User-provided inputs
│   ├── idea.md                      # I: Idea Summary (Sparse or Dense)
│   ├── log.md                       # E: Experimental Log
│   ├── tmpl.md                      # T: Markdown section skeleton
│   ├── tmpl.tex                     # Optional: pandoc LaTeX template for export
│   ├── gl.md                        # G: Conference guidelines
│   ├── fig/                         # F: Optional pre-existing figures
│   └── ref/                         # R: Optional pre-existing references
│
├── ol.json                          # Step 1 output: Outline
│
├── fig/                             # Step 2 output: Generated figures
│   ├── <figure_id>.png
│   └── cc.json                      # Caption context
│
├── refs.bib                         # Step 3 output: BibTeX citations
│
├── drafts/                          # Step 3 + Step 4 outputs
│   ├── intro.md                     # Introduction + Related Work (Step 3)
│   └── manuscript.md                # Complete draft (Step 4)
│
├── refin/                           # Step 5 working directory
│   ├── worklog.json                 # Refinement history
│   ├── iter1/
│   │   └── manuscript.md
│   ├── iter2/
│   │   └── manuscript.md
│   └── iter3/
│       └── manuscript.md
│
├── final/                           # Accepted snapshot
│   ├── manuscript.md                # Canonical Markdown artifact
│   ├── manuscript.tex               # Optional LaTeX export (pandoc)
│   └── manuscript.pdf               # Optional rendered PDF (pandoc)
│
└── provenance.json                  # Input/output hashes for reproducibility
```

---

## Output: Outline JSON Schema (`ol.json`)

```json
{
  "plotting_plan": [
    {
      "figure_id": "fig_<semantic_name>",
      "title": "Human-readable title",
      "plot_type": "plot" | "diagram",
      "data_source": "idea.md" | "experimental_log.md" | "both",
      "objective": "What the figure should show",
      "aspect_ratio": "1:1" | "1:4" | "2:3" | "3:2" | "3:4" | "4:1" | "4:3" | "4:5" | "5:4" | "9:16" | "16:9" | "21:9"
    }
  ],
  "intro_related_work_plan": {
    "introduction_strategy": {
      "hook_hypothesis": "...",
      "problem_gap_hypothesis": "...",
      "search_directions": ["query1", "query2", "..."]
    },
    "related_work_strategy": {
      "overview": "...",
      "subsections": [
        {
          "subsection_title": "2.X ...",
          "methodology_cluster": "...",
          "sota_investigation_mission": "...",
          "limitation_hypothesis": "...",
          "limitation_search_queries": ["...", "..."],
          "bridge_to_our_method": "..."
        }
      ]
    }
  },
  "section_plan": [
    {
      "section_title": "...",
      "subsections": [
        {
          "subsection_title": "...",
          "content_bullets": ["...", "..."],
          "citation_hints": ["Author (Title)" | "research paper introducing 'X'"]
        }
      ]
    }
  ]
}
```

---

## Output: Caption Context (`fig/cc.json`)

```json
{
  "figures": [
    {
      "figure_id": "fig_framework_overview",
      "path": "fig/fig_framework_overview.png",
      "caption": "Generated caption text",
      "raw_content": "Source section text",
      "description": "Detailed figure description"
    }
  ]
}
```

---

## Output: Provenance JSON (`provenance.json`)

```json
{
  "timestamp": "ISO-8601",
  "inputs": {
    "idea.md": "<sha256>",
    "log.md": "<sha256>",
    "tmpl.md": "<sha256>",
    "gl.md": "<sha256>"
  },
  "outline": "<sha256 of ol.json>",
  "refs": "<sha256 of refs.bib>",
  "figures": {
    "<figure_id>": "<sha256>"
  },
  "final_manuscript": "<sha256>"
}
```
