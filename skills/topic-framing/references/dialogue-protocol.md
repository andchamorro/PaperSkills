# Dialogue Protocol

Detailed protocol for each phase of the topic-framing dialogue.

## Phase 1: Seed Capture

### Goal
Parse the user's raw input and restate it as an academic research interest.

### Process
1. Parse "$ARGUMENTS" — may be keyword, topic, question, or paragraph
2. Extract language preference (explicit request or inferred)
3. Extract output format preference (HTML card, markdown, or in-chat)

### Restatement Rules
Turn the input into 2-3 sentences that:
- Use academic language (not business/product/startup language)
- Frame as: phenomenon, debate, or literature extension

**Good:**
- "Understanding how platform algorithms shape advertiser behavior in search markets"
- "The tension between open access mandates and research quality in scholarly publishing"

**Bad:**
- "Building a better ad platform"
- "Making journals more open"

### User Stage Assessment

After restatement, ask:

> I understand your current research interest roughly as: "{restatement}".
> Which of these best describes where you are now?
> A) I only have a broad topic or phenomenon
> B) I have a tentative research question
> C) I have several possible academic angles
> D) I mostly need help sharpening the title

**Smart-skip:**
- A → ask all six questions in Phase 2
- B → focus on Q2-Q6
- C → collect angles first, then Q2-Q6 on strongest
- D → verify Q3-Q6 before titles

---

## Phase 2: Academic Sharpening — Six Questions

### Q1: Research Puzzle

**Ask:** "What is the specific phenomenon, inconsistency, tension, or underexplored pattern that makes this worth studying?"

**Push until you hear:** genuine scholarly puzzle such as:
- Something the literature assumes but may not fully explain
- Two findings, concepts, or trends that don't fit together
- Recurring empirical pattern without satisfying explanation

**Reject:** answers that only name a field or topic area

**Good answers:**
- "Advertisers on search platforms face an information asymmetry — they can't observe how the algorithm scores their bids, so they over-invest in broad keywords as a hedge."
- "There's a tension between open-access mandates and the signaling value of prestige journals for early-career researchers."

**Bad answers:**
- "I want to study AI." (too broad — just names a field)
- "Platform advertising is interesting." (no puzzle, just a topic label)

### Q2: Literature Location

**Ask:** "Which literature or conversation should this paper enter? If you had to place it into 1-2 scholarly conversations, what are they?"

**Push until you hear:** identifiable academic terrain

**Good answers:**
- "platform governance and algorithmic management"
- "comparative political economy of industrial policy"
- "second-language writing assessment and feedback research"

**If user cannot answer:** infer likely literatures and ask for confirmation

### Q3: Gap or Tension

**Ask:** "Within that literature, what is missing, unresolved, conflated, or insufficiently explained?"

**Push until you hear one of:**
- **Empirical gap**: context, case, population, or period not studied
- **Theoretical gap**: concepts underspecified, in tension, or poorly integrated
- **Methodological gap**: existing approaches obscure an important aspect
- **Debate gap**: field has competing claims without clear adjudication

**Reject:** weak "few people studied this" unless user explains why that absence matters

**Good answers:**
- "Most studies of algorithmic management focus on workers; almost none examine how platform algorithms reshape advertiser decision-making." (empirical gap)
- "The literature on open access conflates two distinct mechanisms — cost removal and prestige signaling — but hasn't disentangled their effects." (theoretical gap)

**Bad answers:**
- "Not many people have studied this." (no explanation of why the absence matters)
- "There's a gap in the research." (empty claim — which gap, specifically?)

### Q4: Core Contribution

**Ask:** "What should this paper contribute to scholarship? Pick the closest:"
> A) Explain a phenomenon more convincingly
> B) Clarify or refine a concept
> C) Reconcile or challenge existing theories
> D) Extend a literature to a new case, context, or body of evidence
> E) Compare competing explanations
> F) Synthesize scattered work into a clearer framework
> G) Not sure yet

**If G:** proceed and infer provisionally after Phase 3

### Q5: Unit of Analysis and Evidence

**Ask:** "What is the actual object of study here? What will the paper analyze: texts, cases, organizations, policies, experiments, interviews, archives, datasets, or something else?"

**Push until you hear:** concrete unit and plausible evidence base

This is a sanity check — not full method design.

**Good answers:**
- "I'd analyze advertiser bid histories and keyword portfolios from a search platform dataset (2020-2024)."
- "Semi-structured interviews with 20-30 early-career researchers who have published under both OA and non-OA models."

**Bad answers:**
- "I'll look at data." (too vague — what data, from where?)
- "Maybe surveys or something." (no concrete unit of analysis)

### Q6: Boundaries of the Claim

**Ask:** "What should this paper explicitly NOT claim, cover, or try to solve?"

**Push until you hear scope boundaries:**
- Time period
- Geography or case selection
- Disciplinary boundary
- Level of explanation
- What causal or normative claim the paper won't make

**Good answers:**
- "This paper only covers US search platforms 2020-2024; it won't make claims about social media or non-US markets."
- "I'm not trying to prove causation — just identifying the pattern and testing whether the theoretical mechanism is plausible."

**Bad answers:**
- "I'll keep it focused." (no specific boundaries stated)
- "I won't go off-topic." (says nothing about what is excluded)

---

### Smart-Skip Rules

If "$ARGUMENTS" or earlier answers already cover a question clearly → skip it.

**Example:** If the user's input is "I want to study how search platform algorithms affect advertiser bidding strategy, using Google Ads bid data from 2020-2024", then:
- Q1 (Research Puzzle): partially covered → ask for the specific tension
- Q2 (Literature Location): not covered → ask
- Q5 (Unit of Analysis): already covered (bid data, 2020-2024) → skip
- Q6 (Boundaries): partially covered (time + platform) → ask only about disciplinary scope

### Follow-Up Rule

If user answers vaguely, ask tighter follow-up:
- "Can you name the exact debate?"
- "What kind of gap is that, theoretically or empirically?"
- "What is the paper actually explaining?"

### Escape Hatch

If user becomes impatient:
- "We can compress this. I only need the puzzle, the literature, and the contribution to make the title academically sharp."
- Ask most critical remaining questions, then proceed

---

## Phase 3: Literature Positioning

### Goal
Quick scan to test whether the framing is academically viable. NOT a full review.

### 3a. Generate Search Queries

Create 3 queries from sharpened idea:
1. Direct formulation of the research question
2. Literature-level formulation using main scholarly conversation
3. Gap-focused query with terms like "review", "debate", "framework", "meta-analysis", or key theoretical concepts

### 3b. Semantic Scholar Scan

For each query:
```
GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=10&fields=title,authors,year,citationCount,abstract&year=2020-2026
```

### 3c. Interpret Positioning

Classify:
- **Saturated**: many recent papers answer essentially the same question
- **Active but open**: established conversation, gap still defensible
- **Fragmented**: related work exists but concepts/cases disconnected
- **Emerging**: small body of directly relevant work
- **Poorly framed**: question too vague or wrong vocabulary

### Report Format

> **Literature snapshot:**
> - Found {N} closely related papers (2020-2026)
> - Most relevant anchor paper: "{title}" ({year}, {citations} citations)
> - Positioning: {classification}
> - Initial judgment: {1-2 sentences on whether gap framing holds}

### Revision Trigger

If framing looks weak or saturated → revise before moving on:
- Narrow the phenomenon
- Shift from broad topic to specific debate
- Move from "study X" to "explain Y in X"
- Replace generic novelty with precise contribution

### Fallback

If Semantic Scholar API fails:
1. Try OpenAlex: `https://api.openalex.org/works?search={query}&per_page=10&mailto=paperskills@example.com`
2. If both fail: note "Literature positioning unavailable — manual verification recommended" and proceed

---

## Phase 4: Framing Synthesis

### Goal
Present compact framing for confirmation

### Output Format

```
ACADEMIC FRAMING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Working Question:    {one clear research question}
Research Puzzle:     {what is puzzling or unresolved}
Primary Literature:  {the conversation this paper enters}
Gap / Tension:       {what is missing, unclear, or contested}
Contribution Claim:  {what the paper contributes to scholarship}
Unit of Analysis:    {what is being analyzed}
Scope:               {what is IN}
Non-scope:           {what is OUT}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Confirmation Ask

> Does this capture the paper you actually want to write?
> A) Yes — move to title options
> B) The question needs adjustment
> C) The literature positioning is off
> D) The contribution claim is not right yet
> E) The scope is too broad or too narrow

If B/C/D/E → revise and re-present until confirmed

---

## Phase 5: Title Workshop

### Generation Rules

Generate 5 title candidates, each:
- Reflects confirmed question and contribution
- Signals intellectual center, not just topic
- Avoids startup/consulting/product language
- Concise and credible as journal/conference title

### Title Styles

1. **Direct descriptive** — states subject and contribution plainly
2. **Question-driven** — foregrounds research question
3. **Concept-first** — highlights theoretical concept or debate
4. **Case-and-claim** — ties empirical site to broader contribution
5. **Two-part academic subtitle** — short lead + precise explanatory subtitle

### User Selection

> Here are 5 candidate titles. Which direction is closest?
> 1. {title}
> 2. {title}
> 3. {title}
> 4. {title}
> 5. {title}
> F) None of these — I want a different emphasis

If F → ask what emphasis is missing:
- Stronger theory signal
- Sharper empirical focus
- Clearer comparative angle
- Less ambitious claim
- More conventional journal style

Generate 3 revised options, repeat until user picks one.

### Final Refinement

> Final title: "{selected title}"
> Should we tighten wording further, or lock this in?

---

## Phase 6: Output Framing Card

### Default: HTML Output

Filename: `artifacts/{date}-topic-framing-{topic-slug}.html`

Fields to include:
- Confirmed title
- Working question
- Research puzzle
- Primary literature
- Gap / tension
- Contribution claim
- Unit of analysis
- Scope
- Non-scope
- Literature snapshot
- Candidate titles considered (with selected marked)

### Alternative: Markdown

If user explicitly asks for Markdown:
Filename: `artifacts/{date}-topic-framing-{topic-slug}.md`

### Post-Output

After writing file:
1. Return exact absolute file path to user
2. Ask whether they want it opened
3. Only run `open {file_path}` after user confirms