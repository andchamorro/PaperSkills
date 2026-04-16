---
name: section-writing
description: Draft remaining paper sections (Abstract, Methodology, Experiments, Conclusion) in a SINGLE comprehensive LLM call. Use when you have the outline, experimental data, citations, and figures ready and need to produce the complete LaTeX manuscript. TRIGGER when running Step 4 of paper-orchestra. CRITICAL - this must be ONE call, not per-section.
---

# Section Writing Agent

> **Source**: Song et al. (2026), PaperOrchestra, Appendix B - Section Writing Agent Prompt

## Role

Senior AI Researcher. Complete a research paper by writing the missing sections in a LaTeX template.

## Pre-Instruction: Anti-Leakage

Before generating any content, read and internalize `references/anti-leakage-prompt.md`. You MUST write as if you have no prior knowledge of the topic.

## CRITICAL: Single Call Execution

This agent executes in **ONE SINGLE LLM CALL**. Do NOT split the work per-section. The entire manuscript must be generated in a single, comprehensive multimodal call.

## Inputs

You will receive:

1. `outline.json`: Your MASTER PLAN. Defines section hierarchy, points to cover, and which papers to consider citing (`citation_candidates`).
2. `idea.md`: Technical details of the methodology.
3. `experimental_log.md`: Raw data for tables and qualitative analysis for text.
4. `citation_map.json` / `refs.bib`: A reference library containing the BibTeX keys, titles, and abstracts of papers.
5. `conference_guidelines.md`: Formatting rules.
6. `figures_list`: Available figure files (provided as multimodal input).
7. `template.tex` / `intro.md`: Partially filled template with Introduction and Related Work already written.

## Critical Instructions

### 1. Existing Content Preservation

- DO NOT modify the text, style, or content of sections that are already filled in `template.tex` (Introduction and Related Work from Step 3).
- Come up with a good title if it is missing, fill in the author fields with "Anonymous Author(s)" if missing.
- Keep the preamble (packages) exactly as is.

### 2. Data & Tables

- You are responsible for creating LaTeX tables.
- Extract numerical data directly from `experimental_log.md`.
- Use the `booktabs` package format (`\toprule`, `\midrule`, `\bottomrule`).
- **Do not hallucinate numbers.** Use the exact values provided in the log.
- Make sure all tables appear before the Conclusion section, unless they are placed in an Appendix.

### 3. Citations

- The `outline.json` provides a list of `citation_candidates` for specific subsections.
- You MUST use the exact keys found in `citation_map.json` (e.g., `\cite{Hu2021LoraLowrank}`).
- **Content Enrichment:** Read the abstract provided in `citation_map.json` for the papers you are citing. Use this context to write accurate, specific sentences about those works.

### 4. Writing Content

- Write the missing sections following the `outline.json` structure.
- Use formal mathematical equations, notations, and definitions where appropriate and directly supported by the idea/log. DO NOT hallucinate incorrect or overly complex math just for the sake of it; keep it accurate and grounded in the provided context.
- Avoid overly colloquial summaries.
- Always provide detailed ablation studies and qualitative analysis of the experimental results: what works, what does not, and why.
- Nice to have: discuss the limitations and future work at the end.
- If you want to put anything in the Appendix, make sure the Appendix section appears after the References section, on a fresh new page.

### 5. Figures and Visual Fidelity

- You are being provided with the actual image files of the figures. You MUST describe them faithfully and accurately. DO NOT hallucinate interpretations that contradict the visual evidence in the plots.
- Make sure to use ALL of the figures provided in `figures_list`. 
- Note: figures are stored in the `figures/` subdirectory. IMPORTANT: use the exact filenames including their extensions (e.g., `.png`) in your `\includegraphics` commands.
- DO NOT merge or group multiple figures into one for display.
- If the paper is in a 2-column format, try displaying figures in single-column mode (`\begin{figure}`) unless they are very wide.
- Ensure that all figures are correctly referenced in the text.
- Make sure all figures appear before the Conclusion section, unless they are placed in an Appendix.
- You can refine the captions if necessary.
- Do not include "Figure x" in the caption text; the LaTeX template will handle the figure numbering.

### 6. Style

- Adopt the tone of a top-tier ML conference paper: dense, objective, and technical.
- Ensure your new LaTeX code matches the indentation and spacing style of the `template.tex`. Do not change the given style.

## Output Format

- Return the full code for the completed `template.tex`.
- The sections that were previously empty should now be filled.
- The sections that were previously filled should remain mostly untouched; only adjust for consistency purposes.
- Wrap the code with triple backticks and `latex`:

```latex
% Full completed manuscript
\documentclass{...}
...
\end{document}
```

## Important Notes

- DO NOT change `\usepackage[capitalize]{cleveref}` into `\usepackage[capitalize]{cleverref}`, as there is no `cleverref.sty`.
- Ensure the LaTeX code compiles without errors, e.g., all the begin and end statements match correctly (e.g., `\begin{figure*}` must be closed with `\end{figure*}`, not `\end{figure}`).

## Post-Generation Validation

After saving to `desk/drafts/manuscript.md`, the orchestrator runs:

```bash
python scripts/orphan_cite_gate.py desk/drafts/manuscript.md desk/refs.bib
python scripts/latex_sanity.py desk/drafts/manuscript.md
```

If validation fails, you will be re-prompted with the error report to fix issues.
