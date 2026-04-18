# PaperSkills

Nine AI agent skills that cover the academic paper lifecycle — from topic framing to submission-ready manuscripts.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

---

## What's in this repo

PaperSkills is a suite of reusable [Vercel Agent Skills](https://skills.sh) for academic research. Each skill handles a discrete stage of the paper-development lifecycle and can run standalone or in combination.

The flagship skill, **paper-orchestra**, implements the full PaperOrchestra multi-agent pipeline (Song et al., 2026) — five coordinated agents that transform raw research materials into a submission-ready LaTeX manuscript in a single run. The remaining eight skills cover everything else: sharpening an idea, searching literature, generating abstracts, reviewing manuscripts, and finding target journals.

---

## Skill Catalog

### Ideation & Framing

- **[topic-framing](./skills/topic-framing/)** — Converge a fuzzy idea into a concrete, researchable paper framing through a structured 6-step dialogue.
  *Try:* "frame a paper topic", "sharpen a title", "test framing viability"

- **[research-gap](./skills/research-gap/)** — Identify temporal, methodological, and thematic research gaps using Semantic Scholar and OpenAlex trend data.
  *Try:* "find research gaps in X", "map underexplored areas", "generate research questions"

### Literature & Citations

- **[literature-review](./skills/literature-review/)** — Hybrid multi-API literature search (Semantic Scholar, OpenAlex, PubMed, arXiv) with DOI deduplication, citation-count ranking, and drafted Introduction/Related Work sections.
  *Try:* "search for papers on X", "draft a related work section", "literature review for my topic"

- **[connected-citations](./skills/connected-citations/)** — Build multi-level citation networks from seed papers and generate interactive HTML reports with network graphs, timeline views, and cluster analysis.
  *Try:* "map a research landscape", "find seminal papers", "visualize how papers connect"

- **[paper-tracker](./skills/paper-tracker/)** — Track newly published papers by author, institution, venue, or keyword within a time window.
  *Try:* "monitor recent publications from X", "list papers from this lab in 2026"

### Writing & Manuscript

- **[abstract](./skills/abstract/)** — Generate structured abstracts (IMRaD, thematic, extended) with multiple word-count variants and keyword sets.
  *Try:* "write an abstract", "draft a 250-word abstract for my paper"

- **[paper-orchestra](./skills/paper-orchestra/)** — *Flagship.* Full 5-agent pipeline: outline generation, figure synthesis, literature review, section drafting, and iterative content refinement. Turns an idea summary, experimental log, LaTeX template, and guidelines into a complete manuscript. ~60-70 LLM calls, ~40 min.
  *Try:* "write a paper from my experiments", "run paper-orchestra", "generate a conference submission"

### Review & Submission

- **[peer-review](./skills/peer-review/)** — Academic peer review with 8-criteria scoring (originality, methodology, evidence, etc.), Veto Rules, and an interactive HTML report with radar chart.
  *Try:* "peer review this paper", "evaluate my manuscript", "review with scoring criteria"

- **[journal-match](./skills/journal-match/)** — Recommend target journals by analyzing manuscript scope, searching for comparable published work, and enriching venue metadata (h-index, OA status, citation metrics).
  *Try:* "where should I publish this?", "find matching journals", "journal recommendation"

---

## Installation

```bash
# Install via skills.sh (all skills)
npx skills add andchamorro/paperskills

# Install specific skills
npx skills add andchamorro/paperskills --skill abstract --skill peer-review
```

**Requirements:**
- An AI agent supporting the [Vercel Agent Skills](https://skills.sh) standard
- Python 3.12+
- Semantic Scholar API key (used by most skills; optional for abstract and paper-orchestra)
- OpenAlex API (free, no authentication required)

---

## Usage Examples

### Topic to Paper

```
1. "Frame a paper topic around federated learning for medical imaging"
   → topic-framing produces a framing card with title options and research puzzle

2. "Run paper-orchestra with my idea.md and log.md"
   → paper-orchestra generates outline, figures, literature review, full manuscript
```

### Review and Submit

```
1. "Peer review my manuscript.tex"
   → peer-review scores 8 criteria and generates an HTML report with radar chart

2. "Where should I publish this?"
   → journal-match returns a tiered list of journals ranked by scope alignment
```

### Map a Research Landscape

```
1. "Find research gaps in transformer-based time series forecasting"
   → research-gap identifies temporal, methodological, and thematic gaps

2. "Visualize how these seed papers connect"
   → connected-citations builds an interactive citation network graph
```

---

## How Skills Relate

Most skills are **independent** — install and use any combination.

Two skills are **orchestrators** with sub-agents:

- **paper-orchestra** coordinates 5 sub-agents: outline-agent, plotting-agent, literature-review (Step 3), section-writing, and content-refinement-agent. Steps 2 and 3 run in parallel.
- **peer-review** coordinates 6 sub-agents: retriever-agent, evaluator-agent, missing-refs-detector, reporter-agent, critic-agent, and manuscript-evaluator.

**literature-review** works both as a standalone skill and as Step 3 of paper-orchestra.

All skills that search academic databases use a multi-API fallback chain: Semantic Scholar, OpenAlex, CrossRef, with PubMed and arXiv added conditionally for biomedical and STEM content.

---

## Repo Layout

```
skills/              9 active skills + 1 deprecated stub (lit-search → literature-review)
evaluation/          paper-orchestra evaluation (5 models x 10 prompts, 6 dimensions)
images/              evaluation visualizations (heatmap, radar, regression)
tables/              evaluation CSV data (scores, errors, regressions)
```

---

## Evaluation (PaperOrchestra)

The paper-orchestra skill was evaluated across 5 models using 10 prompts and 6 weighted dimensions.

| Dimension | Weight | Coverage |
|-----------|--------|----------|
| D1 — Functional Correctness | 30% | Scripts execute without error |
| D2 — Instruction Adherence | 25% | Skill follows step-by-step instructions |
| D3 — Robustness | 15% | Handles missing inputs, invalid data |
| D4 — Safety | 15% | No author leaks, no hallucinated citations |
| D5 — Output Quality | 10% | Quality of generated JSON and LaTeX |
| D6 — Latency/Cost Proxy | 5% | Token efficiency |

### Results

| Model | Overall (weighted) | D1 | D2 | D3 | D4 | D5 | D6 | Passed |
|-------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Big Pickle** (baseline) | **5.00** | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 10/10 |
| NVIDIA Nemotron 3 | 4.83 | 5.0 | 5.0 | 4.0 | 5.0 | 5.0 | 4.5 | 9/10 |
| **Elephant** (DeepSeek-V3) | **5.00** | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 10/10 |
| Gemma 4 31B | 4.60 | 5.0 | 5.0 | 3.0 | 5.0 | 5.0 | 4.5 | 9/10 |
| **GLM-4.5-Air** | **5.00** | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 10/10 |

Three models achieve a perfect 5.00 weighted score. All five are production-ready — the minor D3 regressions in Nemotron 3 and Gemma 4 31B trace to a test design artifact (P6), not a skill defect.

![Dimension Radar](images/dimension_radar.png)

Full details: [`evaluation/EVALUATION_REPORT.md`](./evaluation/EVALUATION_REPORT.md)

---

## Contributing

### Setup

```bash
git clone https://github.com/andchamorro/paperskills.git
cd paperskills
pip install ruff pre-commit
pre-commit install
```

### Guidelines

- Follow the [Vercel Agent Skills](https://skills.sh) specification
- `name:` in SKILL.md frontmatter must match the directory name
- `description:` must include trigger conditions
- Optional subdirectories: `scripts/`, `references/`, `assets/`, `evals/`
- Pre-commit hooks are enforced: ruff linting, trailing-whitespace, end-of-file, JSON/YAML checks

```bash
# Verify before submitting
pre-commit run --all-files
```

---

## References

> **PaperOrchestra: A Multi-Agent Framework for Automated AI Research Paper Writing**
> Yiwen Song, Yale Song, Tomas Pfister, Jinsung Yoon — Google DeepMind
> *arXiv:2604.05018, 2026*

- [skills.sh](https://skills.sh) — Vercel Agent Skills registry
- [Semantic Scholar API](https://api.semanticscholar.org/)
- [OpenAlex API](https://docs.openalex.org/)

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
