---
name: synthetic-peer-review
description: >
  Run a mock/synthetic peer-review panel on one or more manuscripts before
  submission. Crafts 3 (configurable) independent expert reviewers with distinct,
  complementary personas, each briefed on the correct framing (e.g. AI-generated,
  in-silico, wet-lab out of scope), then synthesizes their reviews into a handling-
  editor decision letter with a per-manuscript decision and a prioritized,
  convergent Essential-Revisions list. Use when the ask is "review our paper(s)
  like a journal would", "run a mock peer review", "critique before submission",
  or "referee this manuscript". Produces a full report (md + DOCX) and returns the
  structured reviews + editor letter for downstream revision work.
---

# Synthetic peer-review panel

A rigorous, honest mock review — a rehearsal of the journal process, not a
rubber stamp. The value is in (a) distinct expert personas that catch different
classes of problem, (b) a correct framing brief so reviewers don't penalize the
paper for things that are out of scope, and (c) an editor synthesis that turns
three overlapping reviews into an actionable, deduplicated revision list.

## When to use / not use

- **Use:** pre-submission self-review, catching over-claiming / weak stats /
  scope inflation, generating a revision to-do list, stress-testing a narrative.
- **Not a substitute** for real peer review, and reviewers are LLM instances —
  treat every specific factual claim they make (a p-value is wrong, a paper says
  X) as a *lead to verify*, not a finding. The panel's strength is calibration
  and structure, not ground-truth adjudication.

## The process (what the kernel helper does)

```python
run_peer_review_panel(
    host,
    manuscripts,                 # list of (label, text) tuples
    shared_frame,                # required: the framing brief (build with build_shared_frame)
    personas=None,               # dict {1: text, ...}; defaults to DEFAULT_PERSONAS
    max_tokens=8000,             # per-reviewer budget; auto-retries any that truncate
    editor_max_tokens=5000,
    write_report=True,           # writes peer_review_report.md (+ .docx)
    report_title="Mock Peer-Review Report",
) -> {"reviews": [...], "editor": str, "recommendations": [...]}
```

Two companion helpers: `build_shared_frame(work_description, in_scope,
out_of_scope, manuscript_blurbs)` assembles the framing brief, and
`write_peer_review_report(...)` (called internally when `write_report=True`)
assembles the md + DOCX.

1. **Framing brief (shared_frame).** One system-prompt preamble every reviewer
   receives. This is the single most important input. State plainly: what the
   work is, what is IN scope, and what is OUT of scope, so reviewers don't make
   their recommendation contingent on impossible revisions. For an AI/in-silico
   campaign the brief must say: AI authorship is disclosed and part of the
   contribution (not a defect); the work is in silico; wet-bench/clinical
   experimentation is out of scope; **every requested revision must be
   achievable in silico or by editing** (more analysis, stats robustness,
   clarifications, tempering claims, better caveats). Tell them to be genuinely
   critical — reward honesty about limits, penalize over-claiming.

2. **Reviewer personas (2–4).** Each a distinct, complementary expert lens.
   For a comp-bio therapeutics paper the tested triad was: (1) domain clinician-
   scientist (biological plausibility, clinical framing, hedging), (2)
   computational biologist / biostatistician (multiple testing, cohort
   independence, single-cohort claims, prediction validity, reproducibility),
   (3) methodologist / research-ethics reviewer (over-claiming on
   autonomy/novelty, cherry-picking, equity, disclosure norms). Swap personas to
   fit the field, but keep the clinical/quantitative/meta split — it maximizes
   non-overlapping coverage.

3. **Review structure.** Each reviewer returns, PER manuscript: brief summary
   (proves they read it), strengths, **major concerns** (numbered), minor
   concerns, **feasible revisions** (numbered, in-scope only), and a
   **recommendation** (Accept / Minor / Major / Reject) appropriate to that
   manuscript's venue; then a cross-cutting comment on the set.

4. **Editor synthesis.** A separate call, given all reviews, acting as handling
   editor: per-manuscript decision; convergent Essential Revisions (issues ≥2
   reviewers raised, deduplicated and prioritized, naming which reviewers);
   noted disagreements + how to adjudicate; a path-to-acceptance paragraph.

5. **Report + DOCX.** Assemble `peer_review_report.md` (headline outcome →
   editor letter → full reviews) and render to `.docx`. If the
   `agentic-campaign-manuscript` skill is available its `render_manuscript_docx`
   / `verify_docx` helpers are reused; otherwise pypandoc is used directly.

## Model + token notes

- Run reviewers with `model=host.reasoning_model()` (Sonnet-class) — utility
  models under-review. Fan out in one `host.llm([...], max_concurrency=n)` call.
- Reviews are long: set `max_tokens` ≥ 8000 per reviewer or they truncate mid-
  paper (a 2-manuscript review needs the full budget). The helper defaults to
  8000 and checks `stop_reason` — if any come back `max_tokens`, re-run that
  index with a higher cap.
- Editor synthesis: `max_tokens` ≥ 5000.

## Honesty discipline (carried from the campaign)

- The panel is advisory. Do NOT let a reviewer's asserted fact (wrong p-value,
  "paper X shows Y") enter a revision unchecked — verify against the source
  artifact/data first, exactly as you would any claim you write yourself.
- Convergence across ≥2 independent personas is the signal to prioritize a
  revision; a lone-reviewer idiosyncratic ask is lower priority and can be
  adjudicated by the editor step.
- Record the panel's own denominator: how many manuscripts, how many reviewers,
  what framing — so the report is auditable.

## Output

`run_peer_review_panel` returns `{reviews: [str,...], editor: str,
recommendations: [[per-manuscript strings], ...]}` and, if `write_report=True`,
writes `peer_review_report.md` (+ `.docx`). Embed nothing from the reviews into
a manuscript without verifying it first.
