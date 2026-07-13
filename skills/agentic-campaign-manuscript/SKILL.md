---
name: agentic-campaign-manuscript
description: Prepare and UPDATE the "agentic-workflow narrative" manuscript (Paper D) that documents a human-supervised, self-correcting AI discovery-to-design campaign, with eosinophilic esophagitis (EoE) as the worked example. Use when building or revising this Perspective-style paper — recomputing verified campaign metrics from the artifact store, growing the living correction/calibration ledger with new self-correction and human-domain-catch episodes harvested from later chats, verifying citations against CrossRef, and rendering to DOCX for bioRxiv. Load whenever the user says "update the paper", "add a correction-ledger episode", "regenerate Figure 1/2/3/4 or Table 1/3", or "re-render the manuscript".
---

# Agentic-campaign manuscript (Paper D)

## What this paper is

A Perspective-style manuscript whose contribution is **trustworthy agentic
practice**, not the EoE biology. Thesis: *a domain-supervised AI agent can run
a coherent, reproducible, self-correcting discovery-to-design campaign
end-to-end on public data; EoE is the worked example.* The honest treatment of
the agent's **errors and their corrections** is the differentiator — the
correction ledger (§ Living correction ledger) is the heart of the paper and is
designed to grow as more chats and artifacts are reviewed.

Companion papers (separate manuscripts): **A** = pipeline/methods, **B** = EoE
target-landscape, **C** = antigen-directed pMHC framework. This is **D**.

## The non-negotiable discipline

This manuscript makes claims *about* rigor, so it must itself be rigorous.
Three rules, learned the hard way on this project:

1. **Every number is computed, never recalled.** Campaign metrics come from the
   artifact store and artifact timestamps (`compute_campaign_metrics()`), not
   memory. When you itemize a total (e.g. "214 artifacts = 61 figures + …"), the
   sub-rows **must sum to the headline** — add an "other" row if needed.
2. **Every citation is verified.** DOIs are checked against CrossRef
   (`verify_dois()`) before they enter the text. Never cite from memory.
3. **Distinguish measured from framed.** The active-compute span (~23 h from
   timestamps, and growing as the campaign continues) is not the calendar window
   (1-week hackathon). Say which is which, and recompute — don't reuse a prior
   session's number.

An auditor reviews this work; these three are the failures it catches.

## Deliverable manifest (current artifact IDs)

Update these by versioning the SAME artifact (`save_artifacts(...,
version_of={file: artifact_id})`), so lineage stays continuous.

| Item | file | artifact_id |
|---|---|---|
| Manuscript (Nature Perspective, md) | paperD_nature_perspective.md | `bbe2e8ad-d73f-4fea-9519-26bab96cd1e0` |
| Manuscript (DOCX) | paperD_nature_perspective.docx | `0b1a6ac0-22b3-444b-a49e-e4601bec865a` |
| Outline | paperD_agentic_workflow_outline.md | `279b681a-6f24-46ca-bf1a-31177889aca7` |
| Fig 1 campaign schematic | figure1_campaign_schematic.png | `e6ba6c6e-66f0-4493-a968-2fdc33797cf7` |
| Fig 2 operating model | figure2_operating_model.png | `5bc59e84-7439-4b59-bad4-97be36757ca6` |
| Fig 3 correction ledger | figure3_correction_ledger.png | `fb30a287-1576-4330-bfae-9c296e20c022` |
| Fig 4 SIGLEC6 lineage DAG | figure4_lineage_dag.png | `fd8d199b-1b1c-49da-b200-c924c1b9e21b` |
| Table 1 campaign metrics | table1_campaign_metrics.csv/.png | `e20f460d-65bc-4b25-8997-cc9b59bb3ca8` / `fe4f45bd-a5b6-458f-a4dc-7675b33cde51` |
| Table 2 correction ledger | correction_ledger_T2.csv | `b9a3e895-b2ab-4551-b816-24e6ef297420` |
| Table 3 task allocation | table3_task_allocation.csv/.png | `c940c8d1-1859-4468-a33a-13d5864abf7d` / `4f62152a-2dd2-4c46-b47f-29fe9f57525e` |
| Ledger inputs | novelty_ledger.csv | `a812e3cc-a46f-418f-97ca-1d21c65aff33` |
| Ledger inputs | independent_confirmation.csv | `be349a09-7406-4192-b58d-7b40a5fd2b61` |

To regenerate any figure, pull its build code from lineage:
`host.lineage[<latest_version_id>]["code"]`, edit in memory, re-run.

## Embedding figures — two marker forms, two contexts

- **Inside a saved `.md`/`.tex`/`.html` document artifact:** write
  `{{artifact:art_<ARTIFACT_ID>}}` (the artifact_id, prefixed `art_`). The embed
  then tracks that artifact's **latest version** — so Fig 1 stays current
  through version bumps. This is what the manuscript markdown uses.
- **Inline in a chat reply:** use the bare `{{artifact:<VERSION_ID>}}` from the
  `save_artifacts` return.
- **For DOCX:** pandoc cannot read either marker. Resolve markers to real image
  paths first (`resolve_markers_to_paths()`), then convert.

## Living correction ledger (the core of the paper)

Table 2 / Figure 3 hold the campaign's correction & calibration episodes. This
is a **living record**: as later chats surface new self-corrections, human
domain catches, contained contradictions, or validated novel claims, append
them. Episode schema (columns of `correction_ledger_T2.csv`):

`episode` · `claim` (initial claim) · `trigger` (orthogonal test applied) ·
`caught_by` (agent / human + who) · `resolution` · `impact`

Episode **type** is one of: *Agent self-correction* · *Human domain catch* ·
*Contradiction contained* · *Uncertainty calibrated* · *Novel claim validated*.

### Recorded episodes (8)
1. **Agent self-correction** — S100A8/9 alarmin axis → reversed to S100A4 mast
   remodeling when ligand direction across 9 cohorts contradicted it.
2. **Human domain catch** — antigen-presentation analysis scored MHC-I (CD8);
   supervisor noted EoE is CD4/Th2 → re-scoped to MHC-II.
3. **Contradiction contained** — FLG up in one recurrence cohort; recorded as
   cohort-specific (canonical down held 8/9), not suppressed.
4. **Uncertainty calibrated** — PPI-refractory persistence rested on the only
   paired cohort; flagged unreplicated, caveat carried forward.
5. **Novel claim validated** — SIGLEC6 mast-state (single-cell) upheld in 8/8
   bulk cohorts (sig 7/8).
6. **Human domain catch — recruitment ethics.** Agent proposed enrolling the
   pMHC trial by HLA-DRB1 epitope-burden tiers (enrich high-burden alleles);
   supervisor flagged that allele frequencies are ancestry-linked, so
   burden-based eligibility encodes ancestry inequity. Redesigned HLA-agnostic
   (every patient eligible; burden kept as a covariate, never a gate). No
   quantitative check flags an unfair design — this is human-only judgement.
   Source: `recruitment_stratification_rationale.md` v1→v5.
7. **Human domain catch — missed prior art (Hill/Dilollo 2025 TCR).** Supervisor
   flagged Dilollo/Spergel/Hill 2025 (JACI, doi:10.1016/j.jaci.2025.01.008), the
   first functionally-validated EoE food-specific TCR (eoeTCR-4, β-casein
   aa59–78, DR7-restricted, tetramer-confirmed). Redirected the pMHC arm from
   binding prediction alone toward a functional peTH2/TCR ground truth, and
   exposed a panel gap (β-casein omitted; +539 strong binders once the casein
   family was added). The agent's own predictor then independently recovered the
   same DR7 β-casein window — an external validation. Source:
   `index_case_groundtruth_calibration.md`, `eoe_food_trigger_dx_design.md`.
8. **Uncertainty calibrated — index-case blinded ground truth.** Personalized
   food-trigger panel ranked foods by MHC-II presentation. Tested blind against
   an index patient's elimination-diet ground truth (withheld until after the
   prediction): both true triggers (milk, soy) ranked top-2; 5 tolerated foods
   ranked low. The one discordance — wheat, heavily presented by the celiac-risk
   DQ2.2 heterodimer yet tolerated — corrected a latent *presentation ⇒
   pathology* assumption. Presentation is a prior; a driving food additionally
   needs an expanded pathogenic-effector-Th2 clone (the functional assay's
   readout). Strongest single external validation in the campaign. Source:
   `index_case_groundtruth_calibration.md`, `personalized_therapy_plan_index_case.md`.

Episode-type counts (for the Table 1 breakdown row): 1 self-correction ·
3 human catch · 1 contained · 2 calibrated · 1 novel-validated = 8.

The novelty-ledger *finding* partition (Fig 3a) is separate from the episode
ledger and unchanged at 8/12 grounded (7 confirmatory + 1 confirmatory-with-
novel-emphasis; 3 novel, 1 contradictory). Figure 3a also now carries a
*Blinded clinical calibration* callout for episode 8.

### How to add an episode
1. Confirm the episode is real — trace it to an artifact or a specific chat
   turn (`host.frames(pattern=...)`), don't reconstruct from memory.
2. Append a row to `correction_ledger_T2.csv`; keep wording terse and factual.
3. Re-render Figure 3 (pull build code from the Fig 3 artifact's lineage; the
   per-episode accent-color list extends by one). Re-check Panel a arithmetic:
   grounded = confirmatory + confirmatory-with-novel-emphasis; contradictory is
   NOT "grounded".
4. Version the same artifacts (`version_of=`), update the manifest IDs above via
   `host.skills.edit`, and re-render the manuscript + DOCX.

## Manuscript structure (Nature Perspective register)

Standfirst → *The trust problem in agentic science* → *Anatomy of the campaign*
(cites Table 1, Fig 1) → *A supervisor, not a spectator* (Fig 2, Table 3) →
*What the campaign found* (compact EoE results) → *Calibration and
self-correction* (Fig 3 — the core) → *Provenance as a graph* (Fig 4) →
*Lessons for trustworthy agentic science* (the 5 practices) → *Outlook* →
Methods → Data/code availability → Author contributions & AI-use → References.

The five generalizable practices (keep these as the paper's takeaway):
require orthogonal confirmation for novel claims; keep an auditable correction
ledger; keep the human as a supervisor with defined judgment — biological
plausibility, prior art, and **ethics/equity sign-off**; calibrate against
withheld ground truth where possible; track provenance for every artifact.

## Update workflow (typical "update the paper in a few days")

1. `compute_campaign_metrics(project_id)` → refresh Table 1 numbers; re-render
   T1 (sub-rows must reconcile to the headline).
2. Harvest new correction-ledger episodes (§ above) → update Table 2 + Figure 3.
   When reviewing a new batch of chats/artifacts, scan for all five episode
   types — self-corrections, human domain catches (incl. ethics and missed
   prior art), contained contradictions, calibrated uncertainties, validated
   novelty. Ethics catches and blinded ground-truth calibrations are the
   highest-value entries; foreground them.
3. If new targets/findings emerged, update *What the campaign found* and add
   verified citations (`verify_dois()`).
4. Re-render figures that changed (lineage → edit → save with `version_of`).
5. Rebuild the composite panel if used, re-render DOCX
   (`render_manuscript_docx()`), version both md and docx.
6. Update this skill's manifest table with any new artifact IDs.

## Rendering to DOCX

```python
resolve_markers_to_paths("paperD_nature_perspective.md", "paperD_docx_source.md")
render_manuscript_docx("paperD_docx_source.md", "paperD_nature_perspective.docx")
```
Then verify: unzip the docx and confirm image count, reference presence, and key
metric strings (see kernel `verify_docx()`). Requires `pypandoc-binary`
(`pip install pypandoc-binary` if absent).
