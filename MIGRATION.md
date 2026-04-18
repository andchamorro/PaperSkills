# PaperSkills Migration Plan

**Date:** 2026-04-16
**Scope:** Migrate 9 legacy PaperSkills from `.paperskills/paperskills/` to `skills/`
**Status:** Draft — pending review
**Models Used:** Big Pickle, Nemotron 3, Elephant (DeepSeek-V3), Gemma 4 31B, GLM-4.5-Air

---

## 1. Inventory: Legacy Skills

| # | Skill | Lines | Purpose | Token Budget | Architecture | APIs |
|---|-------|-------|---------|-------------|--------------|------|
| 1 | `abstract` | 90 | Generate IMRaD/thematic/extended/short abstracts | 10–20K | Single agent | None |
| 2 | `topic-framing` | 461 | Converge fuzzy idea → paper title via 6-phase dialogue | 15–25K | Single agent | Semantic Scholar |
| 3 | `lit-search` | 86 | Search Semantic Scholar, OpenAlex, PubMed, arXiv; deduplicated | 15–25K | Single agent | SS, OA, PubMed, arXiv |
| 4 | `cite-verify` | 246 | Verify citations via CrossRef/SS/OA; optional PDF claim check | 25–65K | 4-step pipeline | CrossRef, SS, OA, Unpaywall |
| 5 | `citation-network` | 172 | Build citation networks via SS + OpenCitations; vis.js HTML | 35–55K | 4-step pipeline | SS, OpenCitations |
| 6 | `research-gap` | 187 | Analyze temporal/methodological/thematic gaps; Chart.js HTML | 55–85K | 3-subagent pipeline | SS, OA |
| 7 | `peer-review` | 166 | 8-criteria scoring (K1–K8); Chart.js radar; missing refs | 35–60K | 2-parallel-subagent pipeline | SS, OA, CrossRef |
| 8 | `paper-tracker` | 225 | Track new papers by journal/author/venue/keyword; OpenAlex primary | 20–35K | 5-step single agent | OA (primary), SS, CrossRef |
| 9 | `journal-match` | 153 | Recommend journals by scope/methodology; SS + OA | 25–35K | 4-step pipeline | SS, OA, CrossRef |

**Root orchestrator:** `SKILL.md` (48 lines) — routes to sub-skills, no shared prompts.

**Total skill code:** ~2,334 lines across 9 skills.

---

## 2. API Usage Matrix

| API | Skills | Coverage | Rate Limit | Fallback |
|-----|--------|----------|------------|----------|
| **Semantic Scholar** | 7/9 | 78% | Medium | OpenAlex |
| **OpenAlex** | 6/9 | 67% | Low (mailto) | CrossRef |
| **CrossRef** | 4/9 | 44% | Low | OpenAlex |
| **OpenCitations** | 1/9 | 11% | Low | Semantic Scholar |
| **Unpaywall** | 1/9 | 11% | Low | — |
| **PubMed** | 1/9 | 11% | Medium | — |
| **arXiv** | 1/9 | 11% | Low | Semantic Scholar |

---

## 3. Structure Map: Legacy → New Convention

| Legacy Skill | Action | Target Path | Key Changes |
|---|---|---|---|
| `abstract` | **MOVE** | `skills/abstract/` | Remove `name:` frontmatter; update relative paths |
| `topic-framing` | **MOVE + ENRICH** | `skills/topic-framing/` | Split ~461 lines → orchestrator (~200) + `references/dialogue-protocol.md` + `references/html-template.md`; update asset paths |
| `lit-search` | **MERGE** | Into `paper-orchestra/skills/literature-review/` | Overlaps with paper-orchestra's Step 3 literature agent. Deprecate standalone, redirect triggers |
| `cite-verify` | **MERGE** | Into `skills/paper-orchestra/scripts/` | Merged into `citation_tool.py` (unified CLI: orphan-check, verify, smoke-test) |
| `citation-network` | **MOVE** | `skills/citation-network/` | Move; update asset path references |
| `journal-match` | **MOVE** | `skills/journal-match/` | Move; update asset path references |
| `research-gap` | **MOVE + ENRICH** | `skills/research-gap/` | Move; add `scripts/aggregate.py` for OpenAlex trend data |
| `peer-review` | **RESTRUCTURE** | `skills/peer-review/` | Decompose into orchestrator + sub-skills: `manuscript-evaluator/`, `missing-refs-detector/` |
| `paper-tracker` | **MOVE** | `skills/paper-tracker/` | Move; update asset path references |
| `paperskills` (orchestrator) | **DEPRECATE** | Archive | Remove; all skills become self-routing |

**Root `setup` script:** DEPRECATE — opencode's native skill discovery replaces symlink logic.

**`assets/report-template.md`:** Move to `skills/shared/report-template.md` — referenced by 6/9 skills.

---

## 4. Convention Gap Analysis

| Dimension | Legacy | New Repo | Gap |
|-----------|--------|----------|-----|
| YAML frontmatter | `name:` + `description:` | `name:` + `description:` | None — compatible |
| SKILL.md location | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | None — matches |
| Reference paths | `assets/report-template.md` | `references/*.md` | **Mismatch** — fix on move |
| Scripts | None bundled | `scripts/` per skill | Gap — some legacy skills need scripts |
| Sub-skill hierarchy | Flat | Nested (`skills/parent/skills/child/`) | Gap — `peer-review` needs restructuring |
| Eval infrastructure | None | `evaluation/`, `evals/` | Gap — create during migration |
| Shared utilities | None | `lib/` (proposed) | Gap — create during migration |

---

## 5. Conflict / Duplicate / Missing Analysis

### Critical Issues

| Priority | Issue | Location | Fix |
|---|---|---|---|
| **Critical** | `shared/` directory referenced by `setup` script but **does not exist** | `.paperskills/paperskills/setup:22–23` | Create `assets/` as `shared/` symlink OR update all skill refs to `assets/` |
| **High** | `assets/report-template.md` path inconsistency | 6 skill files reference `assets/report-template.md` | Normalize to `skills/shared/report-template.md` after move |
| **High** | `lit-search` ↔ `paper-orchestra/literature-review` overlap | Both search literature via Semantic Scholar | MERGE — designate lit-search as entry point, literature-review as internal |
| **Medium** | English docs missing | `docs/en/skills/*.mdx` — only Chinese docs exist | Generate EN docs or mark as out-of-scope |
| **Medium** | Output path inconsistency | `artifacts/` vs `reports/` vs in-chat | Standardize to `reports/` |
| **Low** | Architecture v2 doc proposes new skills | `docs/zh/architecture-v2.mdx` | Decide scope before migration |

### Frontmatter: No Conflict

All legacy skills use `name:` + `description:` frontmatter. Current repo skills use the same format. **No renaming needed.**

### No Circular Dependencies

All skill-to-skill references are acyclic (routing only, no mutual invocation).

---

## 6. Dependency Graph

```
Self-routing skills (paperskills orchestrator ARCHIVED 2026-04-17)
  ├──► abstract
  ├──► topic-framing ──────────► Semantic Scholar API
  ├──► literature-review ──────► Semantic Scholar, OpenAlex, PubMed, arXiv  (merged from lit-search)
  │      └── symlink: skills/literature-review → paper-orchestra/skills/literature-review
  ├──► citation_tool.py ───────► CrossRef, Semantic Scholar, OpenAlex  (merged from cite-verify + orphan_cite_gate)
  ├──► citation-network ───────► Semantic Scholar, OpenCitations
  ├──► research-gap ───────────► Semantic Scholar, OpenAlex
  ├──► peer-review ────────────► Semantic Scholar, OpenAlex, CrossRef
  ├──► paper-tracker ──────────► OpenAlex, Semantic Scholar, CrossRef
  └──► journal-match ──────────► Semantic Scholar, OpenAlex, CrossRef

assets/report-template.md
  ◄─── citation-network, journal-match,
         research-gap, peer-review, paper-tracker  (5 skills)
```

**Single points of failure:** `topic-framing` and `citation-network` depend solely on Semantic Scholar.

**Over-coupled skills (≥3 APIs):** citation_tool.py (3), literature-review (4), peer-review (3), paper-tracker (3).

**Orphan skills (no dependencies):** `abstract` (pure LLM), `topic-framing` (minimal).

---

## 7. Draft Skill Upgrades

Three skills were drafted with improved structure using skill-creator methodology (11 files created by parallel agents):

### `lit-search` → `skills/lit-search/`
- `SKILL.md` (~95 lines): pushy YAML frontmatter, progressive disclosure
- `references/api-reference.md` (~200 lines): full API docs, fallback chains
- `evals/evals.json`: 3 test prompts
- **Key improvement:** Beginner mode (simple search) vs advanced (API filters with rate-limit handling)

### `topic-framing` → `skills/topic-framing/`
- `SKILL.md` (~130 lines): orchestrator with 6 phases summarized
- `references/dialogue-protocol.md` (~350 lines): full phase details, question scripts
- `references/html-template.md` (~150 lines): framing card HTML template
- `evals/evals.json`: 3 test prompts
- **Key improvement:** Input validation ($ARGUMENTS check), literature scan robustness (OpenAlex fallback), token budget tracking

### `peer-review` → `skills/peer-review/`
- `SKILL.md` (~110 lines): orchestrator
- `skills/manuscript-evaluator/SKILL.md` (~100 lines): 8-criteria evaluation sub-skill
- `skills/missing-refs-detector/SKILL.md` (~80 lines): reference detection sub-skill
- `references/report-template.md` (~80 lines): design system excerpt
- `evals/evals.json`: 3 test prompts
- **Key improvement:** PaperOrchestra pattern (orchestrator + specialized sub-skills), ScholarPeer-inspired architecture

---

## 8. Reference Appendix: arXiv Papers

### Peer Review Automation

| arXiv ID | Title | Authors | Key Finding | Design Implication |
|---|---|---|---|---|
| [2601.22638](https://arxiv.org/abs/2601.22638) | ScholarPeer: Context-Aware Multi-Agent Framework for Automated Peer Review | Goyal et al. | Multi-agent with historiographer + baseline scout + Q&A verifier; significant win-rates vs SOTA on DeepReview-13K | Current `peer-review` should add baseline/missing-reference detection phase; aligns with paper-orchestra's AgentReview usage |
| [2502.12510](https://arxiv.org/abs/2502.12510) | Aspect-Guided Multi-Level Perturbation Analysis in LLM Peer Review | Li et al. | Identifies review conclusiveness bias, tone bias; negative rebuttals increase acceptance rates | Add bias detection for LLM-generated reviews; confidence calibration for scores |
| [2604.00248](https://arxiv.org/abs/2604.00248) | REM-CTX: Automated Peer Review via RL with Auxiliary Context | Taechoyotin et al. | RL (GRPO) with multi-aspect rewards; 8B model outperforms larger commercial models; criticism aspect negatively correlated with others | Consider figure/table analysis; multi-objective reward balancing |

### Literature Search & Review

| arXiv ID | Title | Authors | Key Finding | Design Implication |
|---|---|---|---|---|
| [2412.15404](https://arxiv.org/abs/2412.15404) | RAG Framework for Academic Literature Navigation in Data Science | Aytar et al. | RAG with GROBID extraction, fine-tuned embeddings; abstract-first retrieval improves context relevance | Consider semantic chunking for retrieved papers; RAG-style grounded generation for summaries |
| [2411.18583](https://arxiv.org/abs/2411.18583) | Automated Literature Review Using NLP and LLM RAG | Ali et al. | RAG with GPT-3.5-turbo best; ROUGE-1 0.364; multi-NLP strategy comparison | Add LLM-powered literature synthesis; generate structured narratives, not just lists |
| [2603.20235](https://arxiv.org/abs/2603.20235) | Writing Literature Reviews with AI: Principles, Hurdles | Lahlou et al. | 5 critical pitfalls: bias of ignorance, alignment, mainstreaming, lack of restructuring, lack of critical perspective | **CRITICAL** — Add anti-leakage/grounding prompts to `lit-search` and `literature-review` |
| [2410.17309](https://arxiv.org/abs/2410.17309) | Literature Meets Data: Synergistic Hypothesis Generation | Liu et al. | LLM-powered, literature + data-driven; outperforms baselines +8.97% (few-shot), +15.75% (lit-only) | Gap identification should combine literature gaps + empirical data patterns |

### Research Gap & Monitoring

| arXiv ID | Title | Authors | Key Finding | Design Implication |
|---|---|---|---|---|
| [1901.02660](https://arxiv.org/abs/1901.02660) | Change Detection and Notification of Webpages: A Survey | Mallawaarachchi et al. | CDN systems for monitoring; semantic change detection > date filtering; bursty = significant finding | Consider semantic change detection for abstracts; significance score based on citation velocity |

---

## 9. Phased Roadmap

### Phase Alpha (Week 1–2): Foundation

**Objective:** Move standalone skills, resolve critical conflicts, establish shared structure.

| Day | Actions | Dependencies |
|-----|---------|--------------|
| 1–2 | `git mv` abstract, paper-tracker, citation-network, journal-match → `skills/` | None |
| 3 | Update frontmatter in moved skills (remove `name:` field) | After moves |
| 3 | Fix `assets/report-template.md` → `skills/shared/report-template.md` | After moves |
| 4 | Deprecate `setup` script | After template move |
| 4–5 | Validate all 4 moved skills load correctly | After frontmatter updates |
| 6–7 | Create `skills/shared/api_utils.py`: SemanticScholarWrapper with OpenAlex fallback | After validation |
| 8–9 | Create `skills/shared/error_handling.py`: exponential backoff, circuit breaker, fallback chain | After api_utils |
| 10 | Run full skill validation suite | After shared infra |

**Exit criteria:** 4 skills moved and validated; shared template accessible; no breaking changes to paper-orchestra.

### Phase Beta (Week 3–4): Integration

**Objective:** Merge overlapping skills, enrich complex skills, restructure multi-agent skills.

| Day | Actions | Dependencies |
|-----|---------|--------------|
| 11–12 | Merge `lit-search` → `paper-orchestra/skills/literature-review/` | Phase Alpha |
| 13–14 | Move topic-framing + create `references/` subdirectory | Phase Alpha |
| 13–14 | Move research-gap + add `scripts/aggregate.py` | Phase Alpha |
| 15–16 | Merge cite-verify → `skills/paper-orchestra/scripts/cite_verify.py` | Phase Alpha |
| 17–18 | Restructure peer-review into orchestrator + 2 sub-skills | Phase Alpha |
| 19–20 | Build `skills/shared/budget_tracker.py` and `skills/shared/subagent_templates/` | Phase Beta |

**Exit criteria:** No conceptual overlap between lit-search and literature-review; all merged skills validated; shared API utilities tested.

### Phase Stable (Week 5–6): Polish

**Objective:** Eval infrastructure, CI/CD, documentation, deprecation.

| Day | Actions | Dependencies |
|-----|---------|--------------|
| 21–22 | Create `evaluation/evals/` for all 9 migrated skills | Phase Beta |
| 23–24 | Configure GitHub Actions: lint SKILL.md, run validation | Phase Beta |
| 25 | Update root `README.md` with migrated skill inventory | Phase Beta |
| 26–27 | Run regression tests across all skills | Phase Stable |
| 28 | Deprecate `.paperskills/paperskills/` — archive or remove | Phase Stable |
| 29–30 | Final validation: all triggers work end-to-end | After deprecation |

**Exit criteria:** `evaluation/evals/` exists for all skills; CI passes on all PRs; legacy archived; root README reflects current inventory.

---

## 10. Per-Skill Checklist

### `abstract` — MOVE ✅ DONE — IMPROVED ✅ — PAPERVIZAGENT UPGRADED ✅
- [x] Source: `.paperskills/paperskills/skills/abstract/SKILL.md`
- [x] Dest: `skills/abstract/SKILL.md`
- [x] Changes: Remove `name:` frontmatter; update relative paths
- [x] Improved: Pushy description, numbered imperative steps, scripts/word_count.py, scripts/quality_check.py, error handling section
- [x] PapervizAgent upgrade: Added STEP 0 Retriever→Planner few-shot — `scripts/find_similar_abstracts.py` finds 3-5 published abstracts from the same field via Semantic Scholar; used to match field conventions, terminology, and detail level
- [x] Breaking: None
- [x] Rollback: `git mv skills/abstract/ .paperskills/paperskills/skills/abstract/`

### `topic-framing` — MOVE + ENRICH ✅ DONE — IMPROVED ✅
- [x] Source: `.paperskills/paperskills/skills/topic-framing/`
- [x] Dest: `skills/topic-framing/` + `references/` + `scripts/` + `evals/`
- [x] Changes: Remove `name:`; split into orchestrator (134 lines) + `references/dialogue-protocol.md` + `references/html-template.md` + `evals/`; add input validation; add OpenAlex fallback
- [x] Improved: Trigger-optimized description (412 chars, negative triggers), Step 1-6 numbering with imperative verbs, 8-row error handling table, `scripts/slugify.py` (English + Chinese), dialogue-protocol enriched with 10 good/bad examples, html-template Chinese variant guidance (heading translations, CJK CSS)
- [x] Breaking: None
- [x] Rollback: `git mv skills/topic-framing/ .paperskills/paperskills/skills/topic-framing/`

### `research-gap` — MOVE + ENRICH ✅ DONE — IMPROVED ✅ — PAPERVIZAGENT UPGRADED ✅
- [x] Source: `.paperskills/paperskills/skills/research-gap/SKILL.md`
- [x] Dest: `skills/research-gap/` + `references/` + `scripts/` + `evals/`
- [x] Changes: Remove `name:`; split into orchestrator (127 lines) + `references/api-reference.md` + `references/gap-analysis-methodology.md` + `scripts/aggregate.py` + `evals/`
- [x] Improved: Trigger-optimized description (negative triggers), Step 1-4 numbering with imperative verbs, 10-row error handling table, token budget tracking Step 4, `aggregate.py` enhanced (--format json|text|html, --per-page, 429 backoff), api-reference rate limit section + fetch helper template, gap-analysis-methodology scoring rubric (Impact x Feasibility) + 6 concrete gap examples + prescriptive HTML class names
- [x] PapervizAgent upgrade: Added `references/veto-rules.md` with 5 Veto Rules for gap claims (unsupported gap, premature temporal, unanchored methodological, trivial thematic, overgeneralized population). Step 2 now applies veto checks before assigning priority — vetoed gaps forced to Priority 3
- [x] Breaking: None
- [x] Rollback: `git mv skills/research-gap/ .paperskills/paperskills/skills/research-gap/`

### `cite-verify` — MERGE ✅ DONE (2026-04-17)
- [x] Source: `.paperskills/paperskills/skills/cite-verify/SKILL.md`
- [x] Dest: `skills/paper-orchestra/scripts/citation_tool.py` (unified CLI)
- [x] Changes: Merged cite-verify + orphan_cite_gate.py → unified `citation_tool.py` with 3 subcommands:
  - `orphan-check` — drop-in replacement for orphan_cite_gate.py (same regex, same output)
  - `verify` — multi-backend citation resolution (crossref → semanticscholar → openalex, configurable)
  - `smoke-test` — 4 built-in tests for DOI normalization, BibTeX parsing, regex, backend config
- [x] Legacy `orphan_cite_gate.py` replaced with forwarding shim
- [x] Legacy `cite-verify/SKILL.md` archived to `.paperskills/legacy/cite-verify-SKILL.md`
- [x] All repo references updated to `citation_tool.py orphan-check`
- [x] Breaking: CLI changed from `orphan_cite_gate.py <args>` to `citation_tool.py orphan-check <args>` (shim provides backwards compat)
- [x] Rollback: `git checkout HEAD -- skills/paper-orchestra/scripts/orphan_cite_gate.py`

### `paper-tracker` — MOVE ✅ DONE — IMPROVED ✅ — PAPERVIZAGENT UPGRADED ✅
- [x] Source: `.paperskills/paperskills/skills/paper-tracker/SKILL.md`
- [x] Dest: `skills/paper-tracker/SKILL.md`
- [x] Changes: Remove `name:`; update asset path
- [x] Improved: Pushy description, API offloaded to references/api-reference.md, scripts/deduplicate.py, scripts/window_filter.py, expanded error handling
- [x] PapervizAgent upgrade: Added `scripts/batch_fetch.py` — async batch metadata enrichment with `asyncio.Semaphore(max_concurrent=10)` pattern. STEP 2 now offers batch mode (>10 papers) with concurrent OpenAlex/SS/CrossRef lookups
- [x] Breaking: None
- [x] Rollback: `git mv skills/paper-tracker/ .paperskills/paperskills/skills/paper-tracker/`

### `citation-network` — MOVE ✅ DONE — IMPROVED ✅ — PAPERVIZAGENT UPGRADED ✅
- [x] Source: `.paperskills/paperskills/skills/citation-network/SKILL.md`
- [x] Dest: `skills/citation-network/SKILL.md`
- [x] Changes: Remove `name:`; update asset path; use shared SemanticScholarWrapper
- [x] Improved: Pushy description, API offloaded to references/api-reference.md, subagent prompt to references/network-builder-prompt.md, scripts/resolve_seed.py, scripts/network_stats.py, vis.js HTML skeleton, expanded error handling
- [x] PapervizAgent upgrade: Added STEP 5 Critic validation loop (max 2 rounds) with `scripts/validate_network.py` — validates vis.js setup, seed paper inclusion, node/edge data, layout config, design system compliance
- [x] Breaking: None
- [x] Rollback: `git mv skills/citation-network/ .paperskills/paperskills/skills/citation-network/`

### `journal-match` — MOVE ✅ DONE — IMPROVED ✅ — PAPERVIZAGENT UPGRADED ✅
- [x] Source: `.paperskills/paperskills/skills/journal-match/SKILL.md`
- [x] Dest: `skills/journal-match/SKILL.md`
- [x] Changes: Remove `name:`; update asset path
- [x] Improved: Pushy description, API offloaded to references/api-reference.md, subagent prompt to references/similar-papers-prompt.md, assets/journal-report-template.md, scripts/venue_enrich.py, scripts/scope_score.py, expanded error handling
- [x] PapervizAgent upgrade: Added STEP 0 Retriever→Planner few-shot — finds 5-10 similar published papers via Semantic Scholar to guide journal matching; `references/journal-match-style-guide.md` with tier card styling and Chinese labels
- [x] Breaking: None
- [x] Rollback: `git mv skills/journal-match/ .paperskills/paperskills/skills/journal-match/`

### `lit-search` — MERGE ✅ DONE (2026-04-17)
- [x] Source: `.paperskills/paperskills/skills/lit-search/SKILL.md` + `skills/lit-search/SKILL.md`
- [x] Dest: `skills/paper-orchestra/skills/literature-review/SKILL.md` (canonical) + `skills/literature-review/` (symlink)
- [x] Changes:
  - Rewrote `literature-review/SKILL.md` merging lit-search's parallel multi-API pattern (4 APIs: SS, OpenAlex, PubMed, arXiv)
  - Added Phase 1 parallel WebFetch with per-API rate limits and concurrency controls
  - Added DOI deduplication, citation-count ranking, discipline-based API selection
  - Added standalone mode (ranked markdown table + next actions) alongside paper-orchestra mode (LaTeX)
  - Ported `references/api-reference.md` from lit-search to literature-review
  - Created symlink `skills/literature-review` → `paper-orchestra/skills/literature-review` for top-level discoverability
  - Replaced `skills/lit-search/SKILL.md` with redirect stub pointing to literature-review
- [x] Breaking: `lit-search` triggers now redirect to `literature-review`
- [x] Rollback: `git checkout HEAD -- skills/lit-search/SKILL.md`

### `peer-review` — RESTRUCTURE ✅ DONE — IMPROVED ✅
- [x] Source: `.paperskills/paperskills/skills/peer-review/SKILL.md`
- [x] Dest: `skills/peer-review/` (orchestrator) + 4-agent pipeline + `missing-refs-detector/`
- [x] Changes: Restructured into 4-agent PapervizAgent-inspired pipeline:
  - `evaluator-agent/` — K1-K8 scoring with structured JSON output + Veto Rules (replaces `manuscript-evaluator`)
  - `retriever-agent/` — Semantic Scholar few-shot similar review retrieval (NEW)
  - `reporter-agent/` — HTML report generation per style guide (NEW)
  - `critic-agent/` — iterative report quality validation, max 2 rounds (NEW)
  - `missing-refs-detector/` — reference gap detection (retained, frontmatter updated)
  - `references/veto-rules.md` — K1-K8 Veto Rules with absolute pass/fail conditions
  - `scripts/fetch_review_examples.py` — Semantic Scholar review retrieval
  - `scripts/validate_report.py` — HTML report structural validation
- [x] Breaking: Pipeline now: Retriever → Evaluator + MissingRefs (parallel) → Reporter → Critic
- [x] Rollback: `git checkout HEAD -- skills/peer-review/`

### `paperskills` (orchestrator) — DEPRECATE ✅ ARCHIVED (2026-04-17)
- [x] Source: `.paperskills/paperskills/SKILL.md` + `.paperskills/paperskills/setup`
- [x] Dest: `.paperskills/legacy/SKILL.md` + `.paperskills/legacy/setup`
- [x] Changes:
  - Archived orchestrator SKILL.md with routing table mapping old triggers to new skill locations
  - Archived setup script with error message if run
  - Created `.paperskills/legacy/README.md` with contents table and restore instructions
- [x] Breaking: `/paperskills` umbrella trigger no longer routes — all skills are self-routing
- [x] Rollback: See `.paperskills/legacy/README.md` for restore commands

---

## 11. Shared Infrastructure

| Component | Path | Skills | Priority |
|-----------|------|--------|----------|
| `api_utils.py` — SemanticScholarWrapper + OA fallback | `skills/shared/` | 7/9 | **HIGH** |
| `error_handling.py` — backoff, circuit breaker, fallback chain | `skills/shared/` | All | **HIGH** |
| `report-template.md` — HTML design system | `skills/shared/` | 6/9 | **HIGH** |
| `budget_tracker.py` — token monitoring | `skills/shared/` | All | MEDIUM |
| `subagent_templates/` — standardized sub-agent prompts | `skills/shared/` | 5/9 | MEDIUM |
| `report_components/` — reusable HTML snippets | `skills/shared/` | 6/9 | MEDIUM |
| ~~`i18n/labels.json`~~ | ~~`skills/shared/`~~ | — | REMOVED (English-only, 2026-04-17) |

---

## 12. CI / Tests Plan

### Skill Validation Script
```python
# skills/shared/validate_skill.py
def validate_skill(skill_path: str) -> dict:
    # Check SKILL.md exists and parses
    # Verify frontmatter has description field
    # Verify no broken internal references
    # Check scripts/ and references/ exist if declared
```

### Eval Infrastructure
- `evaluation/evals/<skill-name>/evals.json` per skill
- 3 test prompts per skill minimum
- Assertions for objectively verifiable outputs

### Linting Rules
- SKILL.md must have `description:` field
- No `name:` field (legacy conflict)
- All internal references must resolve
- Max 120 char line length

### GitHub Actions
```yaml
name: Skills CI
on: [pull_request, push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate all skills
        run: python skills/shared/validate_all_skills.py
      - name: Lint SKILL.md files
        run: python skills/shared/lint_skills.py
      - name: Run evals
        run: python -m pytest evaluation/ -v
```

---

## 13. Rollback Plan

### Phase Alpha Rollback
**Detection:** Any moved skill fails validation; paper-orchestra breaks.

```bash
# Restore all moves
for skill in abstract paper-tracker citation-network journal-match; do
  git mv skills/$skill .paperskills/paperskills/skills/$skill
done
git mv skills/shared/report-template.md .paperskills/paperskills/assets/report-template.md
```
**Verify:** `python skills/shared/validate_all_skills.py` passes.

### Phase Beta Rollback
**Detection:** Merge conflicts unresolved; API utilities cause errors.

```bash
git checkout HEAD~1 -- skills/lit-search/
git checkout HEAD~1 -- skills/paper-orchestra/scripts/citation_tool.py
rm -rf skills/topic-framing/references/
rm -rf skills/research-gap/scripts/
rm -rf skills/peer-review/skills/
```
**Verify:** Affected skills validate individually.

### Phase Stable Rollback
**Detection:** CI fails on merged main; eval infrastructure incomplete.

```bash
git mv .paperskills/legacy/SKILL.md .paperskills/paperskills/SKILL.md
git checkout HEAD~1 -- evaluation/evals/
git checkout HEAD~1 -- README.md
```
**Verify:** `python -m pytest evaluation/ -v` passes.

---

## 14. Prioritized Backlog

| # | Item | Effort (days) | Risk (1–5) | Priority | Phase |
|---|------|:-------------:|:-----------:|:--------:|:------:|
| 1 | Create `skills/shared/api_utils.py` (SS + OA wrapper) | 2 | 2 | **HIGH** | Alpha |
| 2 | Move `assets/report-template.md` → `skills/shared/` | 0.5 | 1 | **HIGH** | Alpha |
| 3 | Migrate abstract, paper-tracker, citation-network, journal-match | 2 | 1 | **HIGH** | Alpha |
| 4 | Deprecate `setup` script | 0.5 | 1 | **HIGH** | Alpha |
| 5 | Create `skills/shared/error_handling.py` | 1 | 2 | **HIGH** | Alpha |
| 6 | Merge lit-search → paper-orchestra/literature-review | 1 | 3 | **HIGH** | Beta |
| 7 | Create token budget tracker | 1.5 | 2 | **HIGH** | Beta |
| 8 | Merge cite-verify → paper-orchestra/scripts/ | 1 | 2 | MEDIUM | Beta |
| 9 | Enrich topic-framing with references/ | 1 | 1 | MEDIUM | Beta |
| 10 | Enrich research-gap with aggregation scripts | 1.5 | 2 | MEDIUM | Beta |
| 11 | Restructure peer-review into orchestrator + sub-skills | 2 | 3 | MEDIUM | Beta |
| 12 | Create `evaluation/evals/` for all 9 skills | 2 | 1 | LOW | Stable |
| 13 | Configure GitHub Actions CI pipeline | 1 | 1 | LOW | Stable |
| 14 | Update root README.md | 1 | 1 | LOW | Stable |
| 15 | Deprecate legacy `.paperskills/paperskills/` | 0.5 | 2 | LOW | Stable |
| 16 | Add progressive disclosure to lit-search | 1 | 1 | LOW | Stable |
| 17 | Generate EN documentation for all skills | 3 | 2 | LOW | Stable |

**Total effort:** ~21.5 days. Fits 6-week timeline with buffer.

---

## 15. Cross-Skill Patterns

### API Usage
Semantic Scholar (78%) and OpenAlex (67%) dominate. All 7 SS users should share a common wrapper with OA fallback.

### Subagent Usage
11 sub-agents across 5 skills (56%). Parallel for independent tasks (peer-review), sequential for pipelines. Standardized templates would reduce duplication.

### HTML Reports
6 skills generate HTML reports using `report-template.md` (Crimson Pro, CSS variables, English-only). Reusable component snippets (`metric-card.html`, `paper-row.html`) would benefit all.

### Token Budgets
Range 10K–85K, median ~35K. No centralized tracking. Budget tracker should be shared.

### Error Handling
Inconsistent — 44% handle rate limits, no exponential backoff, no circuit breaker, no partial-result standardization. Error handling utilities should be shared.

### Bilingual Support — REMOVED (2026-04-17)
Simplified to English-only. Prior Chinese/bilingual support documented in `.paperskills/legacy/atomic_language_support.md`.

---

*Generated 2026-04-16 by 5 parallel model agents (Big Pickle, Nemotron 3, Elephant, Gemma 4 31B, GLM-4.5-Air). Draft upgraded skills created by sub-agents. arXiv research via MCP server.*
