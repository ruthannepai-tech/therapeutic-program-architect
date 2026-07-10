# Stage Spec — Disease-Agnostic Drug-Program Pipeline

> Generalized blueprint reverse-engineered from the **Project Tolera (EoE)** program in this
> project. Every stage below was actually executed for EoE across the plan set
> (patient-centered landscape, company/regulatory build, business+scientific plans,
> CCL26/POSTN binder design, sequence/NP optimization, binder manuscript, structured peer
> review). The abstraction keeps the *sequence and decision structure* that worked and strips
> the EoE-specific content (pMHC-II, food antigens, HLA menu) into swappable parameters.

## Design principles

1. **Compose, don't reimplement.** Each stage delegates to an existing catalog skill or MCP
   connector. The orchestrator's job is sequencing, state-threading, and gating — not
   re-deriving analysis logic that already lives in a sub-skill.
2. **The program dossier is the spine.** One JSON state object (`program_dossier.json`)
   threads through all stages: disease, decisions made, artifacts per stage, open questions,
   gate status. Every stage reads it on entry and updates it on exit.
3. **Human validation at every fork.** The pipeline never silently picks a target, modality,
   spend assumption, or go/no-go. It surfaces those as structured `ask_user` checkpoints
   (see `checkpoint_map.csv`). Autonomy is the default *within* a stage; human input is
   required *between* stages at named gates and whenever confidence is low.
4. **Modality-agnostic.** EoE landed on a pMHC-II tolerizing vaccine, but Stage 5 chooses the
   modality from the biology. Two routers: common/polygenic disease routes from protein biology
   (antibody, ligand-trap, small molecule, vaccine, enzyme); monogenic disease routes from the
   confirmed mechanism of pathogenesis (gene replacement, ERT, ASO/siRNA knockdown, splice-
   switching, base/prime editing, CRISPR, read-through). Downstream design branches on the choice.
5. **Archetype-adaptive.** EoE is a common, immune-mediated, data-rich, target-*discovery*
   disease. Thousands of genetic diseases are the opposite: the target (causal gene) is known,
   data are sparse, there are no prior trials, and the hard question is modality + delivery. A
   **Stage 1b ARCHETYPE LOCK** classifies genetic architecture, mechanism, and data density up
   front, and Stages 3/4/5/8/9 each carry a data-rich branch and a sparse/genetic branch. The
   archetype is a resolved parameter, not a separate tool — "any disease" stays one pipeline.
6. **Evidence-graded, never fabricated.** Claims trace to retrieved sources (literature/omics/
   genetics/trials/regulatory databases). Confidence is stated; gaps are surfaced as open
   questions, not filled with plausible numbers. Genetic diagnosis and mechanism-of-pathogenesis
   are clinical claims requiring human validation, never autonomous assertion.

## The 10 stages

Each stage lists: **Goal · Composes (skill/connector) · Inputs · Outputs · Gate**.

### Stage 1 — Indication & unmet need
- **Goal:** Establish the disease: epidemiology, biology, standard of care, patient journey,
  regulatory precedent, landmark trials. The shared factual foundation for everything after.
- **Composes:** `indication-dossier`; connectors `mcp-clinical-genomics` (Open Targets disease
  associations), `mcp-drug-regulatory` (approved drugs / precedent).
- **Inputs:** disease name (± subtype/population scope).
- **Outputs:** `indication_dossier.md`, epidemiology table, SoC table, precedent list.
- **Gate — SCOPE LOCK:** confirm disease definition, population/subtype scope, and geography
  with the user before spending compute downstream.

### Stage 1b — Disease-archetype classification  *(archetype-adaptive branch point)*
- **Goal:** Classify the indication before any landscape/data work, because it reshapes Stages
  3/4/5/8/9. Three axes: (1) **genetic architecture** — monogenic / oligogenic / polygenic-
  complex / chromosomal / mitochondrial / somatic; (2) **mechanism of pathogenesis** (if
  monogenic) — LoF (haploinsufficient vs recessive-null) / gain-of-function / dominant-negative /
  splice / repeat-expansion / nonsense / toxic-RNA; (3) **data density** — rich / moderate /
  sparse (omics cohorts, registered trials, key papers).
- **Composes:** `classify_archetype()` + `data_triage()` (this skill's `kernel.py`); connectors
  `mcp-clinical-genomics` (ClinGen gene–disease validity + dosage), `mcp-variants` (ClinVar
  pathogenicity, gnomAD LOEUF/pLI constraint), `mcp-human-genetics` (GWAS/PheWAS for complex
  disease), `mcp-genes-ontologies` (OMIM/UniProt/GO, inheritance).
- **Inputs:** disease, indication dossier.
- **Outputs:** `disease_archetype`, `mechanism_of_pathogenesis`, `causal_gene`, `data_density`
  recorded in the dossier; a short `archetype_classification.md`.
- **Gate — ARCHETYPE LOCK (hard human gate):** the orchestrator presents the proposed archetype +
  mechanism + data density with its genetics evidence; the **user confirms or corrects**.
  Mechanism of pathogenesis is a clinical claim — if it cannot be confirmed from ClinVar/ClinGen/
  literature, it is recorded as an open question and Stage 4 is used to confirm it before a
  modality is chosen. **This gate is what makes the pipeline work for genetic disease.**
- **How it reshapes downstream:** *monogenic* → the causal gene often IS the target, so Stage 4
  collapses from discovery to confirmation, and Stage 5 routes through the mechanism→modality
  tree. *sparse data* → Stage 3 pivots to natural-history + analogous precedent and Stage 4 goes
  genetics-led. *polygenic/complex, data-rich* → the original EoE-style omics-discovery path.

### Stage 2 — Patient priorities / PFDD
- **Goal:** Surface what patients actually want fixed — symptom burden, quality-of-life,
  treatment-burden priorities — from PFDD Voice-of-the-Patient reports, PRO instruments, and
  patient-org positions. Optionally design a patient-community survey.
- **Composes:** `patient-centered-market-and-survey` (PFDD inventory + patient voice + optional
  survey design).
- **Inputs:** disease, indication dossier.
- **Outputs:** `patient_voice.md`, `pfdd_inventory.csv`, PRO instrument table, (optional)
  survey plan + instrument blueprint.
- **Gate — PRIORITY RANK:** have the user confirm/re-rank the top patient priorities; these
  become design requirements threaded into Stages 5, 7, and 9.

### Stage 3 — Literature + competitive-pipeline map  *(archetype-adaptive)*
- **Goal — branches on `data_density` from Stage 1b:**
  - **Data-rich (`full_competitive_review`):** map the mechanistic literature AND the competitive
    program landscape — who is developing what, by what mechanism, at what stage, with what
    outcomes and documented reasons for success/failure; trial-architecture harvest + precedent
    post-market deep-dive. (The original EoE path.)
  - **Sparse / ultra-rare (`natural_history_plus_analogous_precedent`):** there is often **no**
    competitive pipeline and **no** prior trials. Pivot to (a) **natural-history**: disease
    course, genotype–phenotype correlations, existing registries/patient-org data; (b)
    **analogous-modality precedent**: programs that succeeded with the *same modality on a
    mechanistically similar gene* (e.g. splice-switching ASO precedent for a new splice variant),
    not same-disease competitors. "Whitespace" here is usually "first mover" — the strategic
    question becomes feasibility-by-analogy, not differentiation.
- **Composes:** `systematic-review-orchestration` (or `literature-review` for lighter scope);
  connectors `mcp-clinical-trials` (registered trials), `mcp-clinical-genomics`,
  `mcp-drug-regulatory` (approved-precedent programs), `mcp-human-genetics` (natural-history /
  genotype–phenotype for genetic disease), OpenAlex/CrossRef/PubMed via literature skills.
- **Inputs:** disease, indication dossier, patient priorities, archetype + data_density.
- **Outputs (rich):** `program_roster.csv`, `trials_master.csv`, per-program origin/preclinical
  synthesis, `outcomes_analysis.md`, competitive landscape matrix figure.
  **Outputs (sparse):** `natural_history.md`, `analogous_precedent.csv` (modality × similar-gene
  successes), registry inventory.
- **Gate — WHITESPACE CONFIRM (hard):** rich → user confirms the competitive whitespace to
  pursue; sparse → user confirms the natural-history + analogous-precedent framing and first-mover
  thesis.
- **Gate — DATA SUFFICIENCY (soft):** if omics/trials/natural-history are all thin, surface a
  kill-or-pivot (e.g. "a natural-history study may be a prerequisite") before design spend.

### Stage 4 — Data mining → target nomination  *(archetype-adaptive)*
- **Goal — branches on `stage4_path` from `data_triage()`:**
  - **`omics_de_meta_analysis` (data-rich):** mine public omics (bulk + single-cell) for
    reproducibly dysregulated, cell-of-origin-resolved, druggable targets; cross-reference the
    literature signal. The center of gravity is "which target." (The original EoE path.)
  - **`single_study_de_plus_genetics` (moderate):** the one available cohort's DE plus genetic
    causality evidence, used together to confirm a target.
  - **`genetics_led_confirmation` (sparse / monogenic):** the causal gene is usually **already
    known** — so this stage **confirms mechanism**, it does not discover a target. Assemble
    gnomAD constraint (LOEUF/pLI → haploinsufficiency), ClinVar variant spectrum + pathogenicity,
    ClinGen dosage-sensitivity and gene–disease validity, and expression/tissue context. The
    output is a *confirmed mechanism of pathogenesis*, which feeds the Stage-5 modality tree.
- **Composes:** `omics-target-mining` (rich path: GEO/ArrayExpress/PRIDE/CELLxGENE → cross-study
  DE meta-analysis → single-cell validation → enrichment → Open Targets druggability); connectors
  `mcp-omics-archives`, `mcp-clinical-genomics` (Open Targets, ClinGen), `mcp-variants` (ClinVar,
  gnomAD constraint), `mcp-genes-ontologies` (UniProt/GO context), `mcp-expression` (GTEx tissue).
- **Inputs:** disease, archetype + mechanism (proposed), literature/natural-history from Stage 3.
- **Outputs (rich):** `meta_signature.csv`, `target_shortlist.csv` (ranked, druggability),
  single-cell cell-of-origin evidence, lit-vs-omics concordance.
  **Outputs (sparse):** `mechanism_confirmation.md` (constraint + ClinVar + ClinGen evidence for
  the causal gene), confirmed `mechanism_of_pathogenesis`.
- **Gate — TARGET EVIDENCE (soft):** rich → shortlist with concordant omics+lit+druggability;
  sparse → causal gene with ClinGen validity + ClinVar/gnomAD support and a confirmed mechanism.
  Thin evidence raises a kill-or-pivot before design spend; otherwise proceed to Stage 5.

### Stage 5 — Target & modality selection  *(gap stage — archetype-adaptive router)*
- **Goal:** Choose the lead target(s) AND the therapeutic modality — the pivotal scientific fork.
  **Two routers depending on archetype:**
  - **Common / polygenic / target-discovery (`recommend_modality`):** score candidates on the
    rubric (`assets/target_modality_rubric.csv`) and route from **protein biology** — secreted
    ligand → trap/antibody; surface receptor → antibody; intracellular driver → small molecule/
    ASO; antigen-specific tolerance → vaccine.
  - **Monogenic / genetic (`recommend_modality_genetic`):** route from the **confirmed mechanism
    of pathogenesis** via the decision tree (`assets/genetic_modality_tree.md` / `.csv`) — LoF →
    replacement (gene therapy / ERT) or upregulation; nonsense → read-through; gain-of-function /
    toxic-RNA / repeat-expansion → knockdown (ASO/siRNA); dominant-negative → allele-selective
    knockdown/editing; splice → splice-switching ASO. gnomAD constraint (LOEUF/pLI) informs
    dosage-driven calls. The **delivery vehicle** (AAV serotype, LNP, GalNAc, intrathecal) is
    named here — it is usually the crux, not the payload sequence.
- **Composes:** the rubric + the genetic tree; connectors `mcp-clinical-genomics` (Open Targets
  tractability, ClinGen), `mcp-variants` (constraint), `mcp-chembl` (chemical matter for
  small-molecule/read-through).
- **Inputs:** `target_shortlist.csv` **or** confirmed causal gene + mechanism, patient priorities,
  whitespace/precedent.
- **Outputs:** `target_modality_decision.md` (scored rubric or mechanism-tree rationale +
  alternatives), lead target(s) + chosen modality (+ delivery vehicle) recorded in the dossier.
- **Gate — TARGET/MODALITY LOCK (hard human gate):** the orchestrator presents the recommendation
  (rubric score or mechanism-tree call, with alternatives); the **user must confirm or override**
  target, modality, and — for genetic modalities — the delivery vehicle, before any design
  compute. The single most consequential checkpoint. For genetic disease this depends on a
  **human-confirmed mechanism** (Stage 1b / Stage 4); an unconfirmed mechanism blocks the lock.

### Stage 6 — Design & computational pressure-test  *(modality-routed via `design_skills_for`)*
- **Goal:** Design the candidate for the chosen modality and pressure-test it in silico. The
  route is looked up from `design_skills_for(modality)`:
  - **binder / ligand-trap / antibody:** structure fetch (RCSB/AlphaFold) → RFdiffusion backbones
    (GPU) → inverse-fold → co-fold-back validation → interface metrics → lead selection.
  - **vaccine / peptide:** epitope selection → construct assembly → complex/groove validation.
  - **small molecule / read-through:** `mcp-chembl` chemical matter → `diffdock` docking → co-fold.
  - **genetic modalities** (gene_replacement, enzyme_replacement, aso_knockdown, sirna_knockdown,
    splice_switching_aso, base_prime_editing, crispr_nuclease): design the **construct/oligo/
    guide** with `evo2`/`borzoi` sequence modeling (+ `proteinmpnn`/fold validation for
    replacement-protein products), run the modality-appropriate **in-silico screen** — off-target
    / bystander-edit prediction for editing and knockdown, splice-outcome prediction for SSOs —
    and record the **delivery vehicle + route** (from the route's `delivery` field) as a
    first-class design output and program risk. For genetic modalities the pass/fail bar is
    on-/off-target and delivery feasibility, not interface ipTM.
- **Composes:** structure fetch; `proteinmpnn`/`solublempnn`/`ligandmpnn`; `boltz`/`chai1`/
  `esmfold2`/`alphafold2`/`openfold3`; `fair-esm2`; `diffdock`; `antigen-epitope-pipeline`;
  `evo2`/`borzoi`. GPU via `remote-compute-modal`/`remote-compute-ssh` + `compute-env-setup`.
- **Inputs:** lead target(s) / causal gene, chosen modality + delivery vehicle, target structure
  or sequence.
- **Outputs:** designed sequences/constructs/guides, validation metrics (interface metrics for
  binders; on/off-target + splice/edit-outcome for genetic modalities), ranked leads, delivery
  spec, (optional) 3D render.
- **Gate — DESIGN GO/NO-GO:** present lead(s) with modality-appropriate metrics vs. thresholds
  (binders: e.g. ipTM ≥ 0.85; genetic: on-target efficacy + acceptable off-target + feasible
  delivery) and honest caveats; user approves leads or requests a redesign/optimization loop.

### Stage 7 — Scientific development plan  *(gap stage — assembly template)*
- **Goal:** Stage the path from AI/ML design to first-in-human: (a) computational design engine
  recap, (b) in vitro assay cascade (expression/QC → binding/biophysics → functional/cellular),
  (c) delivery/formulation, (d) preclinical package (PoC → GLP tox → biodistribution),
  (e) CMC & platform/IND strategy, (f) companion diagnostic if relevant, (g) translational
  PD/biomarker strategy with explicit go/no-go gates.
- **Composes:** `assets/scientific_plan_template.md` + evidence from Stages 4–6.
- **Inputs:** leads, modality, target biology, patient priorities.
- **Outputs:** `scientific_plan.md` (+ branded PDF).
- **Gate — none internal; feeds regulatory + commercial.**

### Stage 8 — Regulatory strategy  *(archetype-adaptive)*
- **Goal:** Define the FDA (± EMA) pathway. **Common-disease baseline:** designation eligibility
  (orphan, Fast Track, Breakthrough, RMAT), platform-vs-individualized framing, precedent-anchored
  IND path, endpoints/trial design implied by the patient-priority PROs.
  **Rare / genetic add-ons (fire when archetype is genetic or the population is small):**
  - **Rare Pediatric Disease designation + Priority Review Voucher** (a monetizable asset that
    reshapes the financial model in Stage 9).
  - **Accelerated approval on a surrogate biomarker** (common where clinical endpoints are slow or
    the population too small for a classic RCT — e.g. dystrophin, biomarker-based approvals).
  - **Natural-history studies as external/synthetic controls** — often the only viable comparator
    for ultra-rare N; ties back to the Stage-3 natural-history work.
  - **Platform IND for gene/AAV programs** and the **individualized N-of-1 ASO path** (the
    *Milasen* / n-Lorem model) for ultra-rare or private variants.
  - Cell/gene-therapy-specific CMC and long-term-follow-up expectations.
- **Composes:** `indication-dossier` (regulatory precedent) + `mcp-drug-regulatory` (Drugs@FDA,
  approval basis, labels — incl. rare-disease and gene-therapy precedents) + precedent case study
  from Stage 3.
- **Inputs:** archetype/modality, indication, precedent, scientific plan.
- **Outputs:** `regulatory_strategy.md` (with the rare-disease toolkit section when applicable).
- **Gate — REG ASSUMPTIONS:** confirm designation assumptions, endpoint/surrogate choices, and
  (for rare) the RPD-PRV / accelerated-approval / natural-history-control framing with the user
  (these drive timeline/cost/asset value in Stage 9).

### Stage 9 — Commercial & financing  *(archetype-adaptive)*
- **Goal — the economic model is archetype-shaped:**
  - **Common / sizeable population:** the classic **TAM/SAM/SOM funnel** (prevalence → diagnosed →
    eligible → serviceable), chronic dosing, competitive positioning vs. the Stage-3 landscape.
    (The original EoE path.)
  - **Ultra-rare / genetic:** the funnel math breaks. Model instead on **tiny, well-defined N**
    (often a registry headcount, not a prevalence estimate), **one-time / curative pricing**
    (gene & editing therapies price per-patient in the high six-to-seven figures), **value-based
    or annuity contracting** (outcomes-linked payments amortizing a one-time cure), **registry-
    based launch** rather than a sales force, and the **RPD Priority Review Voucher** (from Stage
    8) as a monetizable balance-sheet asset. Diagnosis rate and newborn-screening status are often
    the true market-size levers.
- **Composes:** `patient-centered-market-and-survey` (market report, sizing, whitespace,
  patient-centered differentiation); connector `mcp-drug-regulatory` for comparator/precedent
  pricing context (incl. approved gene-therapy list prices).
- **Inputs:** epidemiology (Stage 1), archetype + data_density, whitespace/precedent (Stage 3),
  modality/leads, reg timeline + designations (Stage 8).
- **Outputs:** `market_analysis.md` + `market_model.csv`, `financial_model.csv`, market-size
  figure (funnel *or* registry-N build), competitive/positioning figure, use-of-proceeds +
  milestone-timeline figures; for ultra-rare, a pricing/annuity + PRV-value schematic.
- **Gate — FINANCING ASSUMPTIONS (hard human gate):** round sizes, pricing model (chronic vs.
  one-time/annuity), and use-of-proceeds are business commitments — the user must confirm the
  financial assumptions and "the Ask."

### Stage 10 — Deliverables & synthesis
- **Goal:** Assemble the outward-facing package: business plan, scientific plan, VC pitch deck,
  executive one-pager, optional manuscript/poster, and figures — all in a consistent brand and
  cross-checked for numeric consistency. Run a structured multi-perspective peer review.
- **Composes:** `figure-composer`/`figure-style` (figures); `paper-narrative`/
  `agentic-campaign-manuscript` (manuscript); `scientific-poster`; `synthetic-peer-review`
  (technical + biotech + regulatory reviewer synthesis).
- **Inputs:** all prior stage outputs + dossier.
- **Outputs:** `business_plan.(md|pdf)`, `scientific_plan.(md|pdf)`, `<Company>_pitch_deck.pptx`,
  `executive_onepager.md`, optional manuscript/poster, `peer_review_report.md`,
  `program_summary.md`, and a bundled deliverable manifest.
- **Patient-centered pass (required before FINAL REVIEW):** (1) compute `program_verdict(dossier)`
  and state the honest feasibility tier + rationale up front in the summary/exec one-pager — if
  the program is weak or not-yet-tractable, lead with the frank verdict and the best next step for
  the community (natural-history study, registry, biomarker/endpoint work, repurposing), not an
  oversold plan; (2) run `people_first_language()` over every user- and patient-facing document
  and resolve flags with the Stage-2 patient-org framing (person-first vs identity-first).
- **Gate — FINAL REVIEW:** present the full package + peer-review risk/feasibility matrix + the
  `program_verdict` tier; user signs off or requests revisions.

## Stage → sub-skill quick map

| Stage | Primary skill(s) | Connectors |
|------:|------------------|------------|
| 1 | indication-dossier | clinical-genomics, drug-regulatory |
| 1b | *(classify_archetype / data_triage — this skill)* | clinical-genomics, variants, human-genetics, genes-ontologies |
| 2 | patient-centered-market-and-survey | — |
| 3 | systematic-review-orchestration / literature-review | clinical-trials, clinical-genomics, drug-regulatory, human-genetics |
| 4 | omics-target-mining (rich) / genetics-led confirmation (sparse) | omics-archives, clinical-genomics, variants, genes-ontologies, expression |
| 5 | *(rubric + genetic_modality_tree — this skill)* | clinical-genomics, variants, chembl |
| 6 | proteinmpnn/solublempnn/ligandmpnn, boltz/chai1/esmfold2/alphafold2/openfold3, fair-esm2, diffdock, antigen-epitope-pipeline, evo2/borzoi | (GPU: remote-compute-*, compute-env-setup) |
| 7 | *(template — this skill)* | — |
| 8 | indication-dossier | drug-regulatory |
| 9 | patient-centered-market-and-survey | drug-regulatory |
| 10 | figure-composer, paper-narrative, agentic-campaign-manuscript, scientific-poster, synthetic-peer-review | — |

## Notes on ordering & loops
- **Stage 1b ARCHETYPE LOCK runs immediately after SCOPE LOCK** and sets the branch (`data_density`,
  archetype, mechanism) that Stages 3/4/5/8/9 read. Do it before any landscape or data spend.
- Stages 1–3 are **sequential context-building**; 4–6 are the **scientific core**
  (4 [TARGET EVIDENCE soft gate] → 5 [TARGET/MODALITY LOCK hard gate] → 6);
  7–9 are **strategy** (can run in parallel once leads + modality are locked); 10 is **assembly**.
- **Monogenic shortcut:** when the causal gene is known and confirmed, Stage 4 is confirmation not
  discovery, so 1→1b→4 (mechanism) → 5 (modality tree) is the critical path; Stages 2/3 inform but
  don't gate the modality choice.
- **Redesign loop:** a DESIGN NO-GO at Stage 6 returns to Stage 5 (re-pick target/modality) or
  iterates within Stage 6 (optimization). Cap iterations; surface the loop to the user.
- **Early-exit:** if Stage 3 whitespace/DATA SUFFICIENCY or Stage 4 target evidence is weak, the
  orchestrator computes `program_verdict()` and surfaces a "kill or pivot" checkpoint rather than
  pushing a weak program to design compute. A weak verdict is a finding: pair it with the
  highest-value alternative (natural-history study, registry, biomarker/endpoint development,
  repurposing screen) — the honest best next step for the community, not a speculative program.
