# Checkpoint Protocol — Human-in-the-Loop for the Drug-Program Pipeline

This defines **when the orchestrator acts alone vs. when it must stop and ask**, and how it
turns a decision into a structured `ask_user` checkpoint. The goal: full autonomy *within* a
stage, mandatory human validation *at forks that are expensive, irreversible, or judgment-laden*.

## 1. Autonomy vs. checkpoint — the decision rule

Act autonomously when **all** hold:
- The step is analytical/mechanical (fetch, compute, harmonize, render, tabulate).
- Inputs are already confirmed (in the dossier) and the method is prescribed by a sub-skill.
- No business/clinical commitment is being made and nothing costly-irreversible follows.

Stop and open a checkpoint when **any** hold:
- **Named gate** — the step is one of the gates in `assets/checkpoint_map.csv`.
- **Fork with consequence** — choosing a target, modality, endpoint, price, or round size.
- **Spend gate** — the next step burns significant GPU/time (design compute, large review).
- **Low confidence** — evidence is thin, sources conflict, or the model is extrapolating.
- **Needs clinical/human judgment** — a claim about safety, efficacy, or patient benefit that
  a professional must own; the orchestrator must not assert it as established fact.
- **User-supplied ground truth exists** — the user has data, house conventions, or a decision
  that should override a computed default.

Default bias: **when uncertain whether to ask, ask** — but batch related questions into one
checkpoint so the user answers a coherent decision, not a stream of micro-prompts.

## 2. Gate types

- **Hard gate** — pipeline **blocks** until the user answers. Used where proceeding wrong is
  expensive or irreversible: SCOPE LOCK, **ARCHETYPE LOCK**, WHITESPACE CONFIRM,
  TARGET/MODALITY LOCK, DESIGN GO/NO-GO, FINANCING ASSUMPTIONS, FINAL REVIEW.
- **Soft gate** — orchestrator presents its recommendation and proceeds with the default after
  surfacing it, unless the user redirects. Used where a sensible default is safe and reversible:
  PRIORITY RANK, DATA SUFFICIENCY, TARGET EVIDENCE, REG ASSUMPTIONS, and any LOW-CONFIDENCE flag.

A hard gate always maps to an `ask_user` call and the stage does not advance until answered.
A soft gate may use `ask_user` or may state the assumption inline and continue; either way the
choice and its rationale are recorded in the dossier so it is auditable and reversible.

## 3. Anatomy of a checkpoint

Every checkpoint the orchestrator raises carries five things:
1. **What was found / computed** — the evidence, in domain terms (not tool mechanics).
2. **The decision to make** — one sentence.
3. **The recommendation** — the orchestrator's pick + why (confidence stated).
4. **The options** — 2–4 concrete, mutually distinct choices (never "not sure"/"other" —
   the UI already provides free-text + "let the agent decide").
5. **The consequence** — what each choice sets in motion (esp. spend / irreversibility).

The `format_checkpoint()` helper in `kernel.py` assembles these into the argument dict for an
`ask_user` call. The orchestrator makes the actual `ask_user` tool call (helpers can't call
tools); on the answer it calls `record_decision()` to write the choice + rationale into the
dossier and `set_gate()` to mark the gate resolved.

## 4. Confidence → checkpoint mapping

The orchestrator self-rates confidence at each stage exit (high / medium / low):
- **high** — proceed; note the basis in the dossier.
- **medium** — proceed but surface the assumption (soft gate) so the user can veto.
- **low** — hard stop; open a LOW CONFIDENCE checkpoint, record the gap as an open question,
  and never launder the uncertainty into a confident-sounding claim.

## 5. What is NEVER autonomous

These always require explicit user confirmation regardless of confidence:
- Committing the **disease archetype** and **mechanism of pathogenesis** (Stage 1b / ARCHETYPE
  LOCK). Genetic diagnosis and mechanism-of-mutation are clinical claims — propose from
  ClinGen/gnomAD/ClinVar/OMIM evidence, never assert autonomously; an unconfirmed mechanism is an
  open question, not a fact that drives modality choice.
- Committing a **lead target** or **therapeutic modality** (Stage 5).
- Advancing a **design lead** past validation into the development plan (Stage 6).
- Any **financial commitment**: round size, price, use-of-proceeds, the Ask (Stage 9).
- Any **patient-facing or clinical efficacy/safety claim** presented as established.
- Shipping the **final external package** (Stage 10).

## 5b. Disease-archetype classification (Stage 1b)

Immediately after SCOPE LOCK, classify the indication before any landscape or data work, because
it reshapes Stages 3/4/5/8/9:
- **Genetic architecture** — monogenic / oligogenic / polygenic-complex / chromosomal /
  mitochondrial / somatic. Grounded in ClinGen gene–disease validity + dosage, inheritance from
  OMIM/Orphanet, and the count of causal genes.
- **Mechanism of pathogenesis** (if monogenic) — LoF (haploinsufficient vs recessive-null),
  gain-of-function, dominant-negative, splice, repeat-expansion, nonsense, toxic-RNA. Grounded in
  ClinVar variant interpretation + gnomAD constraint (LOEUF/pLI) + primary literature. **This is
  the axis that drives modality** (see `assets/genetic_modality_tree.md`).
- **Data density** — rich / moderate / sparse, from omics-cohort count, registered-trial count,
  and key-paper count. Drives the Stage-3/4 branch: rich → omics DE meta-analysis + full
  competitive review; sparse → genetics-led target/mechanism confirmation + natural-history &
  analogous-modality precedent.

`classify_archetype()` and `data_triage()` in `kernel.py` propose these; the user confirms them
at the ARCHETYPE LOCK hard gate. Record `disease_archetype`, `mechanism_of_pathogenesis`,
`causal_gene`, and `data_density` in the dossier.

## 6. State-threading contract

- On stage **entry**: `load_dossier()`; read prior decisions + open questions; skip work already
  done (idempotent re-entry).
- On stage **exit**: `update_stage()` with status, artifacts produced, confidence, and any new
  open questions; `save_dossier()`.
- Gates: `set_gate(name, status, resolution)` — status ∈ {pending, passed, failed, skipped}.
- The dossier is the single source of truth; chat prose is a view of it, never the store.

## 7. Patient-centered conduct (cross-cutting, every stage)

Two rules apply to *every* stage and never trade against each other.

### 7a. People-first language, unbiased analysis
- **Analysis is cold and quantitative.** Feasibility scores, target-evidence grades, interface
  metrics, financials, and go/no-go calls are computed from recorded evidence and reported
  straight. A weak program is scored and named weak. Never soften a number, inflate a confidence,
  or bury a failed gate to make a program look more fundable than it is.
- **User- and patient-facing language is people-first.** Say "people living with <condition>",
  not "sufferers/victims/the afflicted"; describe support needs specifically rather than
  "high-/low-functioning". Run `people_first_language(text)` over any prose that will reach the
  user, a patient community, a survey instrument, or an external deliverable — it flags terms
  **advisorily** and never rewrites. Some communities prefer **identity-first** language; treat
  every flag as a prompt to confirm the community's own preference (via patient-org input from
  Stage 2), not a rule to apply blindly. Dignity in words, honesty in numbers — both, always.

### 7b. The honest verdict and the best next step
- At **FINAL REVIEW**, and at any **kill-or-pivot** gate (Stage 3 whitespace/DATA SUFFICIENCY,
  Stage 4 TARGET EVIDENCE, Stage 6 DESIGN GO/NO-GO), compute `program_verdict(dossier)` and
  present its tier + rationale + best-next-step to the user. It is a **recommendation**, never an
  autonomous decision (`requires_human_confirmation` is always true).
- **When the therapeutic path is weak or not-yet-tractable, that is a finding, not a failure.**
  The mandate is the best *honest* solution for the community. If a drug program is not justified,
  the most valuable deliverable is the frank verdict paired with the highest-value alternative
  investment — a natural-history study, a patient registry, biomarker/endpoint development, a
  drug-repurposing screen, or a precise statement of what evidence would change the verdict.
  Present that as the recommended path; do not manufacture a speculative program to have a
  "positive" answer. Overselling a weak program is a disservice to the patients it claims to
  serve.
- Record the verdict, its rationale, and the chosen next step in the dossier `decisions` so the
  package (Stage 10) and any external audience see the same honest assessment.
