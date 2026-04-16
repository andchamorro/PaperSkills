---
name: plotting-agent
description: Generate publication-quality figures and diagrams for academic papers using PaperBanana. Use when executing the plotting plan from the outline agent to create conceptual diagrams, statistical plots, and data visualizations. TRIGGER when running Step 2 of paper-orchestra or when "plot generation" or "figure generation" is needed.
---

# Plotting Agent

> **Source**: Song et al. (2026), PaperOrchestra, Appendix B - Plotting Agent Prompt
> **External Dependency**: PaperBanana (Zhu et al., 2026)

## Role

Execute the visualization plan to generate conceptual diagrams and statistical plots for academic papers.

## Integration Note

This agent uses **PaperBanana** (Zhu et al., 2026) as the default module. PaperBanana employs a closed-loop refinement system where a VLM critic evaluates rendered images against design objectives, iteratively revising text descriptions and regenerating images to resolve visual artifacts.

If PaperBanana is not available, fall back to matplotlib/seaborn for plots and manual diagram creation.

## Pre-Instruction: Anti-Leakage

Before generating any content, read and internalize `references/anti-leakage-prompt.md`. You MUST NOT include any author-identifying information in figures.

## Inputs

You will receive:

1. `plotting_plan`: Array of figure specifications from `ol.json`
2. `idea.md`: Technical details for conceptual diagrams
3. `experimental_log.md`: Raw data for statistical plots

Each plot specification contains:
- `figure_id`: Unique identifier (e.g., `fig_framework_overview`)
- `title`: Human-readable title
- `plot_type`: Either `"plot"` or `"diagram"`
- `data_source`: `"idea.md"`, `"experimental_log.md"`, or `"both"`
- `objective`: What the figure should communicate
- `aspect_ratio`: Target aspect ratio

## Process

For each entry in `plotting_plan`:

### 1. Extract Data

If `data_source` includes `experimental_log.md`:
- Parse tables and numeric data
- Identify comparison baselines
- Extract exact values (no hallucination)

If `data_source` includes `idea.md`:
- Extract architectural components
- Identify key relationships
- Note mathematical formulations

### 2. Generate Figure

**For `plot_type: "plot"`:**
- Create statistical visualizations using appropriate chart types
- Ensure axis labels are clear and units specified
- Include legends for multi-series data
- Match the specified `aspect_ratio`

**For `plot_type: "diagram"`:**
- Create conceptual or architectural diagrams
- Use consistent visual language (shapes, colors, arrows)
- Ensure readability at typical paper figure sizes
- Match the specified `aspect_ratio`

### 3. VLM Critique Loop (if PaperBanana available)

1. Render initial figure
2. VLM critic evaluates against `objective`
3. If artifacts or misalignment detected:
   - Revise text description
   - Regenerate image
4. Repeat until satisfactory (max 3 iterations)

### 4. Generate Caption

For each completed figure, generate a caption:

**Input Data:**
- Task Type: `{task_name}`
- Contextual Section: `{raw_content}`
- Overall Figure Intent: `{description}`
- Detailed Figure Description: `{figure_desc}`

**Requirements:**
- The caption should be concise and informative, and can be directly used as a caption for academic papers.
- The caption MUST NOT contain a "Figure X:" or "Caption X:" prefix, as the LaTeX template will add it automatically.
- The caption MUST NOT contain any markdown formatting (like bold, italics, etc), it should be plain text.

Respond with the plain text caption only.

## Output

Save to `desk/fig/`:

1. **Figure files:** `{figure_id}.png` for each figure
2. **Caption context:** `cc.json`

### cc.json Schema

```json
{
  "figures": [
    {
      "figure_id": "fig_framework_overview",
      "path": "fig/fig_framework_overview.png",
      "caption": "Generated caption text without Figure X prefix",
      "raw_content": "Source section text used for generation",
      "description": "Detailed figure description from plotting plan"
    }
  ]
}
```

## Guidelines

- **Data Integrity:** Never hallucinate or extrapolate numeric data beyond what's in `experimental_log.md`
- **Visual Clarity:** Use colorblind-friendly palettes when possible
- **Consistency:** Maintain consistent styling across all figures
- **Resolution:** Generate at minimum 300 DPI for print quality
- **Simplicity:** Academic figures should communicate one main point clearly

## Validation

After generation, verify:
1. All figures in `plotting_plan` have corresponding `.png` files
2. `cc.json` contains entries for all figures
3. Captions do not contain "Figure X:" prefixes
4. No author-identifying information in figures
