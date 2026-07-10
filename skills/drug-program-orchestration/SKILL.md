---
name: drug-program-orchestration
description: Orchestrate an end-to-end therapeutic drug program for ANY disease — common OR genetic/rare — from unmet need and patient priorities, through data/literature/genetics-mined target and modality selection, AI/ML design and in-silico pressure-testing, to scientific, regulatory, and commercial strategy and deliverables. A conductor that composes catalog skills stage by stage, threads a program dossier through them, classifies the disease archetype up front (monogenic/mechanism-driven vs polygenic/data-rich), and stops for human validation at every fork (archetype lock, target/modality lock, design go/no-go, financing). Use when the ask is to "build/run a drug program", "take disease X from data to a fundable plan", or "design a therapeutic for X end to end". Disease-, modality-, and archetype-agnostic. NOT for a single stage — target mining use omics-target-mining, market report use patient-centered-market-and-survey, binder design use protein-design skills.
---

# Drug-program orchestration

A **conductor** for running a complete therapeutic program on any indication. It does not
re-implement analysis — it **sequences existing skills**, threads one state object (the
*program dossier*) through them, and **stops for human validation at every consequential fork**.

This skill was generalized from the EoE **Project Tolera** program (a personalized pMHC-II
tolerizing-vaccine biotech taken from "what data exist" to "how we raise $8M"). The stage
sequence and the decision/gate structure are what actually worked there, abstracted so the
disease, target, and modality are swappable parameters.

## Core idea

- **Compose, don't reimplement.** Each stage loads a sub-skill or connector and delegates.
  The orchestrator owns sequencing, state, and gating only.
- **The dossier is the spine.** `program_dossier.json` records disease, scope, decisions,
  per-stage artifacts, gate status, and open questions. Read it on stage entry; update on exit.
  It is the source of truth — chat prose is a view of it.
- **Human validation at every fork.** Never silently pick a target, modality, endpoint, price,
  or go/no-go. Surface those as structured `ask_user` checkpoints. See `checkpoint_protocol.md`
  and `assets/checkpoint_map.csv`.
- **Modality-agnostic.** Stage 5 chooses the modality from the biology (antibody, ligand-trap/
  binder, small molecule, ASO/RNA, cell therapy, vaccine, enzyme, gene therapy, peptide).
  Stage 6 branches design on that choice.
- **Evidence-graded, never fabricated.** Claims trace to retrieved sources; confidence is
  stated; gaps become open questions, not invented numbers.
- **People-first language, cold analysis.** These are separate and both non-negotiable. The
  *analysis* — feasibility, target evidence, financials, go/no-go — stays quantitative and
  unbiased; a weak program is scored and named weak, never dressed up. The *language* facing the
  user and any patient community is people-first ("people living with X", not "X sufferers/
  victims"): run `people_first_language()` over user-facing prose as an advisory check, and
  confirm the community's own preferred framing (person-first vs identity-first) rather than
  assuming. Deliver dignity in words; deliver honesty in numbers.
- **The goal is the best HONEST solution, not a drug at any cost.** When the therapeutic path is
  weak or not yet tractable, the most valuable deliverable for the community is often not a
  program — it is a natural-history study, a patient registry, biomarker/endpoint development, a
  repurposing screen, or a frank "not tractable yet, here is what would change that."
  `program_verdict()` derives a transparent tier (tractable / conditional / weak /
  not_yet_tractable) from recorded evidence and pairs it with a patient-useful best-next-step.
  It is presented at FINAL REVIEW (and early kill-or-pivot gates), never an autonomous decision.

`kernel.py` ships pure-compute helpers (dossier init/load/save/update, gate tracking,
checkpoint formatting, modality→design-skill routing, archetype/mechanism classification, the
people-first language check, the honest program verdict, deliverable manifest). Load this skill
and they auto-register into the kernel. The full stage blueprint is in `stage_spec.md`; read it
when you need the inputs/outputs/gate detail for a stage.

## When to use
- "Build a drug program for <disease>", "take <disease> from data to a fundable plan",
  "run the whole pipeline: unmet need → targets → design → regulatory → business plan".
- Generalizing a therapeutic-development workflow across indications.
- **Not** for a single stage — those have dedicated skills (see the map below). If the user
  wants only target mining, only a market report, or only binder design, load that skill directly.

## How to run it

### 0. Initialize
```python
d = init_dossier(disease="<name>")          # creates program_dossier.json in the workspace
save_dossier(d)
```
Then open the pipeline with a **SCOPE LOCK** checkpoint (Stage 1 gate), immediately followed by
**Stage 1b ARCHETYPE LOCK** — classify genetic architecture, mechanism of pathogenesis, and data
density (`classify_archetype()` / `data_triage()`) before spending any landscape or data compute.
This one classification reshapes Stages 3/4/5/8/9.

### The stage loop
For each stage in order: `load_dossier()` → check if already done (idempotent) → load the
sub-skill / call the connector → produce artifacts → `save_artifacts(...)` → `update_stage(...)`
with status/artifacts/confidence/open-questions → if the stage has a gate, raise it and
`set_gate(...)` on the answer → `save_dossier()`.

Confidence rating drives gating: `high` → proceed; `medium` → surface the assumption (soft gate);
`low` → hard stop with a LOW CONFIDENCE checkpoint. Details in `checkpoint_protocol.md`.

## The 10 stages (composition map)

| # | Stage | Load / call | Gate |
|--:|-------|-------------|------|
| 1 | Indication & unmet need | `indication-dossier`; connectors `mcp-clinical-genomics`, `mcp-drug-regulatory` | **SCOPE LOCK** (hard) |
| 1b | **Disease-archetype classification** | `classify_archetype()`/`data_triage()` (this skill); connectors `mcp-clinical-genomics`, `mcp-variants`, `mcp-human-genetics`, `mcp-genes-ontologies` | **ARCHETYPE LOCK** (hard) |
| 2 | Patient priorities / PFDD | `patient-centered-market-and-survey` | PRIORITY RANK (soft) |
| 3 | Literature + pipeline map | `systematic-review-orchestration` (or `literature-review`); connectors `mcp-clinical-trials`, `mcp-clinical-genomics`, `mcp-drug-regulatory`, `mcp-human-genetics` | **WHITESPACE CONFIRM** (hard) · DATA SUFFICIENCY (soft) |
| 4 | Data mining → targets *(rich)* / mechanism confirmation *(sparse)* | `omics-target-mining`; connectors `mcp-omics-archives`, `mcp-clinical-genomics`, `mcp-variants`, `mcp-genes-ontologies`, `mcp-expression` | TARGET EVIDENCE (soft) |
| 5 | Target & modality selection | *(rubric + `genetic_modality_tree` — this skill)*; connectors `mcp-clinical-genomics`, `mcp-variants`, `mcp-chembl` | **TARGET/MODALITY LOCK** (hard) |
| 6 | Design & pressure-test | modality-routed (see below); GPU via `remote-compute-modal`/`remote-compute-ssh`, `compute-env-setup` | **DESIGN GO/NO-GO** (hard) |
| 7 | Scientific development plan | *(template — this skill)* | — |
| 8 | Regulatory strategy *(+ rare-disease toolkit)* | `indication-dossier`; connector `mcp-drug-regulatory` | REG ASSUMPTIONS (soft) |
| 9 | Commercial & financing *(+ ultra-rare economics)* | `patient-centered-market-and-survey`; connector `mcp-drug-regulatory` | **FINANCING ASSUMPTIONS** (hard) |
| 10 | Deliverables & synthesis | `figure-composer`, `paper-narrative`/`agentic-campaign-manuscript`, `scientific-poster`, `synthetic-peer-review` | **FINAL REVIEW** (hard) |

Full per-stage goal/inputs/outputs/gate detail: `stage_spec.md`. Gate questions, go-criteria,
and no-go actions: `assets/checkpoint_map.csv`.

### Stage 1b — disease-archetype classification (the archetype-adaptive branch point)
`classify_archetype(facts)` proposes a genetic architecture (monogenic / oligogenic / polygenic-
complex / chromosomal / mitochondrial / somatic) and `data_triage(...)` a data-density tier
(rich / moderate / sparse), grounded in ClinGen validity + dosage (`mcp-clinical-genomics`),
gnomAD constraint + ClinVar (`mcp-variants`), inheritance/OMIM (`mcp-genes-ontologies`), and
GWAS/PheWAS for complex disease (`mcp-human-genetics`). For monogenic disease also establish the
**mechanism of pathogenesis** — the axis that drives modality at Stage 5. Present all of it at the
**ARCHETYPE LOCK** hard gate; the user confirms/corrects. **Mechanism is a clinical claim** — if
it can't be confirmed, record it as an open question and use Stage 4 to confirm before Stage 5.
This is what makes the pipeline work for the rare/monogenic majority, where the target is already
known, data are sparse, and there are no prior trials. Record `disease_archetype`,
`mechanism_of_pathogenesis`, `causal_gene`, `data_density` in the dossier. Detail: `stage_spec.md`
Stage 1b + `checkpoint_protocol.md` §5b.

### Stage 5 — target & modality selection (this skill's first gap-filler; two routers)
Which router fires depends on the archetype set at Stage 1b:
- **Common / polygenic / target-discovery** → `recommend_modality(target_facts)`: score
  candidates on `assets/target_modality_rubric.csv` and route from **protein biology** (secreted
  ligand → trap/antibody; surface receptor → antibody; intracellular driver → small molecule/ASO;
  antigen-specific tolerance → vaccine; enzyme deficiency → enzyme/gene therapy).
- **Monogenic / genetic** → `recommend_modality_genetic(mechanism, constraint, target_facts)`:
  route from the **confirmed mechanism of pathogenesis** via `assets/genetic_modality_tree.md`
  (LoF → replacement/upregulation; nonsense → read-through; GoF/toxic-RNA/repeat-expansion →
  knockdown; dominant-negative → allele-selective knockdown/editing; splice → splice-switching
  ASO). gnomAD LOEUF/pLI informs dosage-driven calls; the helper returns
  `(modality, rationale, alternatives)`. Name the **delivery vehicle** here (AAV/LNP/GalNAc/
  intrathecal) — it is usually the crux.
Use `mcp-clinical-genomics` (tractability), `mcp-variants` (constraint), `mcp-chembl` (chemical
matter). Present the recommendation + alternatives; **the user must confirm or override target,
modality, and (genetic) delivery vehicle** before design. For genetic disease this requires a
**human-confirmed mechanism** — an unconfirmed mechanism blocks the lock.

### Stage 6 — design, routed by modality (`design_skills_for(modality)` in `kernel.py`)
- **antibody / ligand_trap_binder:** fetch target structure (RCSB/AlphaFold) → backbones
  (RFdiffusion on GPU) → inverse-fold (`proteinmpnn`/`solublempnn`/`ligandmpnn`) → fold-back
  validation (`boltz`/`chai1`/`esmfold2`/`alphafold2`/`openfold3`) → interface metrics
  (ipTM/pLDDT/pAE) → lead selection → optional 3D render. `fair-esm2` for embeddings/mutation
  scoring.
- **vaccine / peptide:** `antigen-epitope-pipeline` for epitope selection → construct assembly →
  complex validation.
- **small_molecule / readthrough:** `mcp-chembl` for chemical matter → `diffdock` docking.
- **genetic modalities** (`gene_replacement`, `enzyme_replacement`, `aso_knockdown`,
  `sirna_knockdown`, `splice_switching_aso`, `base_prime_editing`, `crispr_nuclease`): design the
  construct/oligo/guide with `evo2`/`borzoi` (+ `proteinmpnn`/fold validation for replacement-
  protein products); run the modality-appropriate in-silico screen (off-target/bystander for
  editing & knockdown, splice-outcome for SSOs); record the **delivery vehicle + route** (from the
  route's `delivery` field) as a first-class output and program risk. Pass/fail is on-/off-target
  + delivery feasibility, not interface ipTM.
Present leads vs. modality-appropriate thresholds at DESIGN GO/NO-GO; a no-go loops to Stage 5
(re-pick) or iterates optimization within Stage 6 (cap the loop; surface it).

### Stage 7 — scientific development plan (this skill's second gap-filler)
Assemble `assets/scientific_plan_template.md`, filled from Stages 4–6: computational design
engine, in-vitro assay cascade (expression/QC → biophysics → functional/cellular), delivery/
formulation, preclinical package, CMC & IND strategy, companion diagnostic (if relevant),
translational PD/biomarker strategy with explicit go/no-go gates.

## Ordering & loops
- **1b ARCHETYPE LOCK runs right after SCOPE LOCK** and sets the branch (data_density, archetype,
  mechanism) that Stages 3/4/5/8/9 read — do it before any landscape/data spend.
- 1–3 build context (sequential); 4–6 are the scientific core (4→5 gate→6); 7–9 are strategy
  (parallelizable once leads+modality lock); 10 assembles.
- **Monogenic shortcut:** causal gene known+confirmed → Stage 4 is confirmation not discovery, so
  1→1b→4 (mechanism)→5 (modality tree) is the critical path.
- Redesign loop: DESIGN NO-GO → Stage 5 or Stage-6 optimization, capped.
- Early exit: weak Stage-3 whitespace/precedent, thin data (DATA SUFFICIENCY), or weak Stage-4
  evidence → "kill or pivot" checkpoint before design spend.

## Guardrails
- Never assert a clinical efficacy/safety or patient-benefit claim as established — flag it as an
  open question needing clinical validation.
- Never commit target, modality, design lead, or any financial number without explicit user
  confirmation (see `checkpoint_protocol.md` §5).
- GPU-heavy Stage 6 requires a configured compute target — check `list_compute` first; if none,
  tell the user and either run the CPU-feasible parts or defer design.
- Connector (`mcp-*`) calls run only in the `repl` tool; pass results to analysis kernels via
  `./handoff/*.json`.
