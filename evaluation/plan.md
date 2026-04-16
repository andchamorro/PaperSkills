# Evaluation Plan: paper-orchestra Skill

## 1. Overview

Evaluates the `paper-orchestra` skill across 5 models:
- **Big Pickle** (opencode/big-pickle) — baseline
- **NVIDIA Nemotron 3** (nvidia/llama-3.1-nemotron-70b-instruct)
- **Elephant** (deepseek-ai/DeepSeek-V3-0324)
- **Gemma 4 31B** (google/gemma-3-31b-it)
- **GLM-4.5-Air** (thudm/glm-4-9b-chat)

**Evaluation date:** 2026-04-16
**Skill version:** de12bed (commit after all scripts black-formatted)
**Skill path:** `skills/paper-orchestra/`

## 2. Evaluation Dimensions

| # | Dimension | Description | Max Score |
|---|-----------|-------------|-----------|
| D1 | Functional Correctness | Scripts execute without error; desk scaffolded correctly | 5 |
| D2 | Instruction Adherence | Skill follows its own step-by-step instructions exactly | 5 |
| D3 | Robustness (Edge Cases) | Handles missing inputs, invalid data, boundary conditions | 5 |
| D4 | Safety | No author leaks, no hallucinated citations, no harmful content | 5 |
| D5 | Output Quality | Quality of generated outline JSON, LaTeX, prose | 5 |
| D6 | Latency/Cost Proxy | Token usage as proxy for efficiency | 5 |

**Overall score:** Weighted average (D1: 30%, D2: 25%, D3: 15%, D4: 15%, D5: 10%, D6: 5%)

## 3. Prompt Set

### P1: Desk Initialization (D1, D2)
**Prompt:** "Initialize a paper-orchestra desk for a new CVPR 2025 submission on video object tracking. Use `python scripts/init.py --out /tmp/eval-desk-P1 --with-examples`. Then run `python scripts/validate.py --desk /tmp/eval-desk-P1`."

**Pass criteria:**
- `init.py` exits 0 and creates all 4 required input files
- `validate.py` exits 0 on complete desk
- Output matches expected directory structure

### P2: Input Validation — Incomplete Desk (D3, D4)
**Prompt:** "Run `python scripts/validate.py --desk skills/paper-orchestra/evals/files/sample-desk/` and report what is missing and what passes."

**Pass criteria:**
- Correctly identifies missing files (log.md, tmpl.md, gl.md)
- Does not produce false positives (doesn't flag existing files as missing)
- Exit code is non-zero

### P3: Outline Generation — Step 1 (D1, D2, D5)
**Prompt:** "You are executing Step 1 of the paper-orchestra pipeline. Read `skills/paper-orchestra/evals/files/complete-desk/inputs/idea.md` and `skills/paper-orchestra/evals/files/complete-desk/inputs/log.md`. Also read `skills/paper-orchestra/skills/outline-agent/SKILL.md`. Generate a valid `ol.json` with all three required keys: `plotting_plan`, `intro_related_work_plan`, and `section_plan`. Save it to `/tmp/eval-ol-P3.json`. Then validate it has the required fields."

**Pass criteria:**
- Valid JSON output
- Contains `plotting_plan` array with entries having `figure_id`, `plot_type`, `data_source`, `aspect_ratio`
- Contains `intro_related_work_plan` with `introduction_strategy` and `related_work_strategy`
- Contains `section_plan` array
- Citation hints present for datasets and baselines in log.md

### P4: Anti-Leakage Detection (D4)
**Prompt:** "Run `python scripts/anti_leakage_check.py skills/paper-orchestra/evals/files/sample-manuscript.tex` and report all leaks found. Which specific patterns were detected?"

**Pass criteria:**
- Detects email addresses (jsmith@stanford.edu, jdoe@mit.edu)
- Detects author declarations
- Detects university names (Stanford University, MIT)
- Detects personal GitHub URL
- Detects corresponding author marker
- Total ≥ 5 leak categories detected

### P5: Citation Gate — Orphan Detection (D4)
**Prompt:** "Run `python scripts/orphan_cite_gate.py skills/paper-orchestra/evals/files/sample-manuscript.tex skills/paper-orchestra/evals/files/complete-desk/inputs/tmpl.md`. Report what orphan citations were found."

**Pass criteria:**
- Detects `kirillov2023sam` as orphan (not in tmpl.md which has no refs.bib)
- Detects `smith2024` as orphan
- Reports line numbers for orphan locations
- Exit code is non-zero

### P6: LaTeX Sanity Check (D1, D3)
**Prompt:** "Run `python scripts/latex_sanity.py skills/paper-orchestra/evals/files/sample-manuscript.tex`. Report whether the LaTeX structure passes or fails, and why."

**Pass criteria:**
- Detects that `\\begin{document}` comes before `\\documentclass` OR
- Reports missing sections / environment issues
- Exit code reflects actual validation result

### P7: Snapshot — Hash Computation (D1, D2)
**Prompt:** "Run `python scripts/snapshot.py --desk skills/paper-orchestra/evals/files/complete-desk/ --pretty` and verify the output is valid JSON with timestamp and input hashes."

**Pass criteria:**
- Valid JSON output
- Contains `timestamp` field (ISO-8601)
- Contains `inputs` object with at least 4 entries
- Contains `outputs` object
- SHA-256 hashes are 64-character hex strings

### P8: Skill Trigger — Description Matching (D2)
**Prompt:** "For each of these user queries, decide whether the paper-orchestra skill should trigger. Respond YES or NO for each: (1) 'turn my experimental results into a CVPR paper', (2) 'write a poem about AI', (3) 'run paper-orchestra on my desk', (4) 'debug my Python code', (5) 'generate a conference submission from my idea', (6) 'list files in my directory'."

**Pass criteria:**
- (1) YES
- (2) NO
- (3) YES
- (4) NO
- (5) YES
- (6) NO
- ≥ 5/6 correct

### P9: Pipeline Step Sequence Adherence (D2)
**Prompt:** "Read `skills/paper-orchestra/SKILL.md`. List the 5 steps of the pipeline in order, and for each step state: (a) which sub-skill is invoked, (b) how many LLM calls are made, (c) what the output file is. Then verify: should Step 2 and Step 3 run in parallel? Why?"

**Pass criteria:**
- Correctly lists all 5 steps in order
- Identifies parallel execution of Steps 2 and 3
- Correctly states the reason (independent artifacts, Semantic Scholar rate limits)
- Step 4 must be ONE single call
- Step 5 has max 3 iterations

### P10: Refinement Halt Rules (D2, D3)
**Prompt:** "Read `skills/paper-orchestra/references/halt-rules.md`. Suppose iteration 2 has overall_score=5.5 and iteration 3 has overall_score=5.5 (tie). The sub-scores for iteration 2 sum to 22 and for iteration 3 sum to 21. Should the loop halt or continue? Show your reasoning using the halt conditions."

**Pass criteria:**
- Correctly identifies: score ties, net sub-axis change = 21 - 22 = -1 (negative)
- Therefore halts and reverts to previous snapshot
- Cites the specific halt rule: "tie with negative net sub-axis change"

## 4. Grading Rubric

Each prompt is scored 0–5:

| Score | Meaning |
|-------|---------|
| 5 | Perfect — all pass criteria met |
| 4 | Near-perfect — minor omissions, ≥80% criteria met |
| 3 | Partial — ~60% criteria met, significant gaps |
| 2 | Weak — ~40% criteria met, major gaps |
| 1 | Poor — only basic elements present |
| 0 | Fail — no criteria met or wrong approach |

## 5. Error Categories

| Category | Description |
|----------|-------------|
| E1 | Script execution failure (crash, wrong exit code) |
| E2 | JSON output malformed or missing required keys |
| E3 | False negative (leaks exist but not detected) |
| E4 | False positive (clean content flagged as violation) |
| E5 | Instruction deviation (skipped step, wrong order) |
| E6 | Hallucination (cited paper not in experimental log) |
| E7 | Anti-leakage violation (author info inserted) |

## 6. Model Configuration

| Model | OpenRouter ID | Temperature | Max Tokens |
|-------|---------------|-------------|-------------|
| Big Pickle | opencode/big-pickle | 0.0 | 4096 |
| Nemotron 3 | nvidia/llama-3.1-nemotron-70b-instruct | 0.0 | 4096 |
| Elephant | deepseek-ai/DeepSeek-V3-0324 | 0.0 | 4096 |
| Gemma 4 31B | google/gemma-3-31b-it | 0.0 | 4096 |
| GLM-4.5-Air | thudm/glm-4-9b-chat | 0.0 | 4096 |

## 7. Output Files

```
evaluation/
├── plan.md                        # This document
├── results/
│   ├── big-pickle/
│   │   ├── P1.json ... P10.json  # Per-prompt results
│   │   └── summary.json
│   ├── nemotron3/
│   ├── elephant/
│   ├── gemma4-31b/
│   └── glm-4.5-air/
├── tables/
│   ├── eval_scores.csv            # Scores per prompt per model
│   ├── dimension_scores.csv        # Dimension averages per model
│   ├── errors.csv                 # Error categorization
│   └── regression.csv             # vs Big Pickle baseline
└── images/
    ├── scores_heatmap.png
    ├── dimension_radar.png
    └── regression_delta.png
```
