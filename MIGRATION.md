# PaperSkills Migration Plan

**Date:** 2026-04-16
**Scope:** Migrate 9 legacy PaperSkills from `.paperskills/paperskills/` to `skills/`
**Status:** Draft — pending review
**Models Used:** Big Pickle, Nemotron 3, Elephant (DeepSeek-V3), Gemma 4 31B, GLM-4.5-Air

---

## 1. Inventory: Legacy Skills

| # | Skill | Lines | Purpose | Token Budget | Architecture | APIs |
|---|-------|-------|---------|-------------|--------------|------|
| 1 | `abstract` | 90 | Generate IMRaD/thematic/extended/short abstracts; bilingual | 10–20K | Single agent | None |
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
| `cite-verify` | **MERGE** | Into `skills/paper-orchestra/scripts/` | Complements `orphan_cite_gate.py`. Convert to CLI tool, wrap as sub-skill |
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
paperskills (orchestrator)
  ├──► abstract
  ├──► topic-framing ──────────► Semantic Scholar API
  ├──► lit-search ─────────────► Semantic Scholar, OpenAlex, PubMed, arXiv
  ├──► cite-verify ───────────► CrossRef, Semantic Scholar, OpenAlex, Unpaywall
  ├──► citation-network ───────► Semantic Scholar, OpenCitations
  ├──► research-gap ───────────► Semantic Scholar, OpenAlex
  ├──► peer-review ────────────► Semantic Scholar, OpenAlex, CrossRef
  ├──► paper-tracker ──────────► OpenAlex, Semantic Scholar, CrossRef
  └──► journal-match ──────────► Semantic Scholar, OpenAlex, CrossRef

assets/report-template.md
  ◄─── cite-verify, citation-network, journal-match,
         research-gap, peer-review, paper-tracker  (6 skills)
```

**Single points of failure:** `topic-framing` and `citation-network` depend solely on Semantic Scholar.

**Over-coupled skills (≥3 APIs):** cite-verify (4), lit-search (4), peer-review (3), paper-tracker (3).

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

### `abstract` — MOVE ✅ DONE — IMPROVED ✅
- [x] Source: `.paperskills/paperskills/skills/abstract/SKILL.md`
- [x] Dest: `skills/abstract/SKILL.md`
- [x] Changes: Remove `name:` frontmatter; update relative paths
- [x] Improved: Pushy description, numbered imperative steps, scripts/word_count.py, scripts/quality_check.py, error handling section
- [x] Breaking: None
- [x] Rollback: `git mv skills/abstract/ .paperskills/paperskills/skills/abstract/`

### `topic-framing` — MOVE + ENRICH
- [ ] Source: `.paperskills/paperskills/skills/topic-framing/`
- [ ] Dest: `skills/topic-framing/` + `references/` + `evals/`
- [ ] Changes: Remove `name:`; split into orchestrator + references; update asset path; add input validation; add OpenAlex fallback
- [ ] Breaking: New bilingual default behavior
- [ ] Rollback: `git mv skills/topic-framing/ .paperskills/paperskills/skills/topic-framing/`

### `research-gap` — MOVE + ENRICH
- [ ] Source: `.paperskills/paperskills/skills/research-gap/SKILL.md`
- [ ] Dest: `skills/research-gap/`
- [ ] Changes: Remove `name:`; add `scripts/aggregate.py`; use shared API utils
- [ ] Breaking: New `--output-format` option
- [ ] Rollback: `git mv skills/research-gap/ .paperskills/paperskills/skills/research-gap/`

### `cite-verify` — MERGE
- [ ] Source: `.paperskills/paperskills/skills/cite-verify/SKILL.md`
- [ ] Dest: `skills/paper-orchestra/scripts/cite_verify.py` + `skills/cite-verify/SKILL.md` (wrapper)
- [ ] Changes: Convert to Python CLI; create wrapper skill; add to shared API utils
- [ ] Breaking: New CLI `python scripts/cite_verify.py --doi <DOI>`
- [ ] Rollback: `git checkout HEAD -- skills/paper-orchestra/scripts/cite_verify.py; rm skills/cite-verify/`

### `paper-tracker` — MOVE ✅ DONE — IMPROVED ✅
- [x] Source: `.paperskills/paperskills/skills/paper-tracker/SKILL.md`
- [x] Dest: `skills/paper-tracker/SKILL.md`
- [x] Changes: Remove `name:`; update asset path
- [x] Improved: Pushy description, API offloaded to references/api-reference.md, scripts/deduplicate.py, scripts/window_filter.py, expanded error handling
- [x] Breaking: None
- [x] Rollback: `git mv skills/paper-tracker/ .paperskills/paperskills/skills/paper-tracker/`

### `citation-network` — MOVE ✅ DONE — IMPROVED ✅
- [x] Source: `.paperskills/paperskills/skills/citation-network/SKILL.md`
- [x] Dest: `skills/citation-network/SKILL.md`
- [x] Changes: Remove `name:`; update asset path; use shared SemanticScholarWrapper
- [x] Improved: Pushy description, API offloaded to references/api-reference.md, subagent prompt to references/network-builder-prompt.md, scripts/resolve_seed.py, scripts/network_stats.py, vis.js HTML skeleton, expanded error handling
- [x] Breaking: None
- [x] Rollback: `git mv skills/citation-network/ .paperskills/paperskills/skills/citation-network/`

### `journal-match` — MOVE ✅ DONE — IMPROVED ✅
- [x] Source: `.paperskills/paperskills/skills/journal-match/SKILL.md`
- [x] Dest: `skills/journal-match/SKILL.md`
- [x] Changes: Remove `name:`; update asset path
- [x] Improved: Pushy description, API offloaded to references/api-reference.md, subagent prompt to references/similar-papers-prompt.md, assets/journal-report-template.md, scripts/venue_enrich.py, scripts/scope_score.py, expanded error handling
- [x] Breaking: None
- [x] Rollback: `git mv skills/journal-match/ .paperskills/paperskills/skills/journal-match/`

### `lit-search` — MERGE (deprecate standalone)
- [ ] Source: `.paperskills/paperskills/skills/lit-search/SKILL.md`
- [ ] Dest: Deprecate; content merged into `paper-orchestra/skills/literature-review/`
- [ ] Changes: Mark deprecated; redirect triggers; merge API logic
- [ ] Breaking: `/lit-search` redirect to paper-orchestra
- [ ] Rollback: Restore archived SKILL.md

### `peer-review` — RESTRUCTURE
- [ ] Source: `.paperskills/paperskills/skills/peer-review/SKILL.md`
- [ ] Dest: `skills/peer-review/` (orchestrator) + `manuscript-evaluator/` + `missing-refs-detector/`
- [ ] Changes: Decompose into sub-skills; add baseline scout from ScholarPeer; bilingual K-criteria
- [ ] Breaking: New sub-triggers `/peer-review evaluate`, `/peer-review missing-refs`
- [ ] Rollback: Restore original SKILL.md; remove sub-skill dirs

### `paperskills` (orchestrator) — DEPRECATE
- [ ] Source: `.paperskills/paperskills/SKILL.md`
- [ ] Dest: Archive to `.paperskills/legacy/SKILL.md`
- [ ] Changes: Deprecation notice; all skills become self-routing
- [ ] Breaking: `/paperskills` umbrella trigger no longer routes
- [ ] Rollback: Restore from archive

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
| `i18n/labels.json` — bilingual label translations | `skills/shared/` | 8/9 | MEDIUM |

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
git checkout HEAD~1 -- skills/paper-orchestra/scripts/orphan_cite_gate.py
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
6 skills generate HTML reports using `report-template.md` (Crimson Pro, CSS variables, bilingual). Reusable component snippets (`metric-card.html`, `paper-row.html`) would benefit all.

### Token Budgets
Range 10K–85K, median ~35K. No centralized tracking. Budget tracker should be shared.

### Error Handling
Inconsistent — 44% handle rate limits, no exponential backoff, no circuit breaker, no partial-result standardization. Error handling utilities should be shared.

### Bilingual Support
8/9 skills support Chinese. `lit-search` is weakest (transliteration only). Full i18n system would benefit all.

---

*Generated 2026-04-16 by 5 parallel model agents (Big Pickle, Nemotron 3, Elephant, Gemma 4 31B, GLM-4.5-Air). Draft upgraded skills created by sub-agents. arXiv research via MCP server.*
