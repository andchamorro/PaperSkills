# Content Refinement Halt Rules

> **Source**: Song et al. (2026), PaperOrchestra, §Method Step 5

The Content Refinement Agent implements a score-driven iterative loop with strict halt conditions to prevent over-refinement and reward hacking.

---

## Default Configuration

| Parameter | Value |
|-----------|-------|
| Max iterations | 3 |
| Reviewer system | AgentReview (Jin et al., 2024) |
| Calls per iteration | ~2-3 (review + revision + optional re-review) |

---

## Halt Conditions

The refinement loop stops and accepts the current best snapshot when **ANY** of these conditions is met:

### 1. Iteration Cap Reached

```
if iteration_count >= MAX_ITERATIONS:
    halt(accept_current)
```

Default: `MAX_ITERATIONS = 3`

### 2. Overall Score Decrease

```
if current_overall_score < previous_overall_score:
    halt(revert_to_previous)
```

If the overall review score decreases compared to the previous iteration, immediately revert to the previous snapshot and halt.

### 3. Tie with Negative Net Sub-Axis Change

```
if current_overall_score == previous_overall_score:
    net_change = sum(current_sub_scores) - sum(previous_sub_scores)
    if net_change < 0:
        halt(revert_to_previous)
```

If the overall score ties but the net sum of sub-axis scores is negative (at least one sub-axis decreased without compensating gains elsewhere), revert to the previous snapshot and halt.

### 4. No New Actionable Weaknesses

```
if len(new_actionable_weaknesses) == 0:
    halt(accept_current)
```

If the reviewer issues no new actionable weaknesses, the manuscript has reached a quality plateau. Accept and halt.

---

## Acceptance Logic

```python
def should_accept_revision(current, previous):
    # Overall score increased → accept
    if current.overall_score > previous.overall_score:
        return True

    # Overall score tied → check sub-axes
    if current.overall_score == previous.overall_score:
        net_sub_change = sum(current.sub_scores) - sum(previous.sub_scores)
        if net_sub_change >= 0:
            return True  # Tie with non-negative net gain
        else:
            return False  # Tie with negative net gain → revert

    # Overall score decreased → revert
    return False
```

---

## Worklog Format

The refinement agent maintains `desk/refin/worklog.json`:

```json
{
  "iterations": [
    {
      "iteration": 1,
      "timestamp": "ISO-8601",
      "input_snapshot": "drafts/manuscript.md",
      "output_snapshot": "refin/iter1/manuscript.md",
      "reviewer_feedback": {
        "overall_score": 5.5,
        "sub_scores": {
          "clarity": 6,
          "novelty": 5,
          "soundness": 5,
          "significance": 6
        },
        "strengths": ["...", "..."],
        "weaknesses": ["...", "..."],
        "questions": ["...", "..."]
      },
      "addressed_weaknesses": ["...", "..."],
      "integrated_answers": ["...", "..."],
      "actions_taken": ["...", "..."],
      "accepted": true
    },
    {
      "iteration": 2,
      "timestamp": "ISO-8601",
      "input_snapshot": "refin/iter1/manuscript.md",
      "output_snapshot": "refin/iter2/manuscript.md",
      "reviewer_feedback": {
        "overall_score": 5.5,
        "sub_scores": {
          "clarity": 7,
          "novelty": 5,
          "soundness": 4,
          "significance": 6
        }
      },
      "halt_reason": "tie_negative_net_change",
      "accepted": false,
      "reverted_to": "refin/iter1/manuscript.md"
    }
  ],
  "final_accepted": "refin/iter1/manuscript.md",
  "total_iterations": 2,
  "halt_reason": "tie_negative_net_change"
}
```

---

## Critical Constraints During Refinement

### 1. No Fabricated Experiments

The agent **MUST ignore** reviewer requests for:
- Additional experiments
- New ablations
- New baselines
- Metrics not in `experimental_log.md`

The agent is a **manuscript synthesizer**, not an experiment executor.

### 2. No Explicit Limitations

The agent **MUST NOT** explicitly list missing baselines, datasets, or experiments as limitations.

**Rationale**: During early testing, the agent exploited the automated reviewer's scoring function by superficially listing missing baselines as limitations to artificially inflate acceptance scores. Banning this behavior forces genuine improvement in presentation and clarity.

### 3. Data Integrity

All numerical claims **MUST** be verified against `experimental_log.md`:
- Accuracy values
- Parameter counts
- Training hours
- Latency measurements
- Any quantitative result

---

## Halt Reason Codes

| Code | Description |
|------|-------------|
| `max_iterations` | Reached iteration cap |
| `score_decrease` | Overall score decreased |
| `tie_negative_net_change` | Overall score tied but net sub-axis change negative |
| `no_actionable_weaknesses` | Reviewer issued no new actionable feedback |
