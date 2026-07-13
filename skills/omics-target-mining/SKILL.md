---
name: omics-target-mining
description: End-to-end pipeline for mining public omics datasets (GEO, ArrayExpress, PRIDE, CELLxGENE) to nominate and prioritize therapeutic targets for a disease. Use when the task is to survey all public datasets for a condition, derive a reproducible cross-study differential-expression signature, validate at single-cell resolution, and rank druggable/tractable targets. Covers dataset inventory + tiering, harmonization, per-study moderated-t DE, DerSimonian-Laird random-effects meta-analysis, scanpy single-cell composition/DE, pathway+regulator+ligand-receptor enrichment, multi-omics integration, and Open Targets druggability scoring.
---

# Omics target mining

A reproducible pipeline that goes from "here is a disease" to "here is a
ranked, druggability-annotated therapeutic-target shortlist" using only
public data. Ten stages; each ends by saving artifacts.

**Cross-disorder by design.** Every stage parameterizes on the disease name,
the case/control contrast, and the marker sets — nothing is hardwired to one
condition. Developed on EoE; reruns for any inflammatory/immune disorder
(other EGIDs, celiac, IBD, autoimmune disease) by swapping the disease terms,
the Tier-1 dataset filter, and the canonical-marker panel. The EoE-derived
notes below (granulocyte dropout, HLA false-positives, marker-direction
heterogeneity) are stated as general gotchas, not disease specifics.

**Composes with:** `antigen-epitope-pipeline` (turn nominated antigens into
HLA-resolved epitope maps for antigen-specific dx/tx) and
`systematic-review-orchestration` (ground the target rationale in a tiered
literature base). Together these three are the reusable methodology stack for
target discovery in a new inflammatory disorder.

Two bespoke statistics ship in `kernel.py` and are auto-loaded when this
skill loads: `moderated_de(expr, labels)` and `meta_analysis(fc_df, se_df)`.

## When to use
- "Find novel targets for <disease> from public data."
- "Build a cross-study expression signature for <condition>."
- "Which dysregulated genes are druggable / antibody-tractable?"

## Environment
Create a dedicated env (heavy stack): `pandas numpy scipy statsmodels
scikit-learn matplotlib seaborn requests openpyxl` + pip `GEOparse gseapy
mygene`. Single-cell stages need a scanpy env (`scanpy leidenalg
harmonypy`, and `liana` for cell-cell communication). Set
`NUMBA_CACHE_DIR=/tmp/numba_cache` before importing scanpy on read-only
site-packages. Load `figure-style` and call `apply_figure_style()` before
plotting.

## Stage 1 - Dataset inventory
Query each repository and build one master table (accession, assay, tissue,
n_samples, has_control, treatment_context, platform, date, title, summary).
- GEO: NCBI E-utilities esearch/esummary with disease-name + assay terms.
- ArrayExpress (non-GEO), PRIDE (proteomics), CELLxGENE (curation API
  `/curation/v1/collections`).
Audit for keyword-only false positives (co-mention of the disease); flag
`relevant=False` with an exclusion reason rather than deleting. Save
`*_dataset_inventory.csv` + a landscape figure (assay x repository).

## Stage 2 - Tier & prioritize
Score each dataset on relevance / analytical role / tractability. Tier 1 =
human in-vivo case-control bulk/array with interpretable design and usable
n; Tier 2 = single-cell; Tier 3 = complementary (miRNA, methylation,
proteomics, blood, in-vitro/mouse). Save `dataset_tiers.csv` + rationale md.

## Stage 3 - Retrieve & QC Tier-1 bulk
Download supplementary count/intensity matrices. Build binary case/control
labels per study (schemas differ - keep the labelling logic in a reusable
script). Harmonize IDs to gene symbols (ENSG via mygene; array probes via
platform annotation). Normalize: raw counts -> log-CPM; already-normalized
kept as-is; linear microarray intensity -> log2. QC: per-study PCA (expect
case/control separation) and a canonical-marker check (recovers known
markers with correct direction => labels/orientation validated). Save a
harmonized bundle as a checkpoint. **Report marker direction
heterogeneity-aware** - a marker that reverses in one cohort is not "clean
across all studies".

## Stage 4 - Per-study DE
`moderated_de(expr, labels)` on log2 expression: variance-moderated Welch t
(adds prior variance = median pooled variance), BH-FDR. Confirm canonical
markers rank highly with correct direction (quote actual q-values; do not
assume a uniform threshold). Underpowered studies may yield exactly 0 at
FDR<0.05 - say "0", not "few". Save per-study tables + volcanoes +
cross-study concordance heatmap.

## Stage 5 - Cross-study meta-analysis
`meta_analysis(fc_df, se_df)` - DerSimonian-Laird random-effects pooling
(per-study SE = |log2FC / t|), returns pooled log2FC, z, p, Q, I2, k,
n_up/n_dn. BH-FDR across genes. High-confidence signature = FDR<0.05 AND
|pooled FC|>=1 AND concordant in >=k_min studies. **Label figures by the
criterion actually plotted** - if the volcano highlights `FDR<0.05 &
|FC|>=1`, don't annotate it with counts from a stricter concordance-gated
subset. Save `*_meta_signature.csv` + high-conf subset + volcano + forest.

## Stage 6 - Single-cell validation
Pick a disease-specific 10x series (CELLxGENE atlases often lack an explicit
disease tag). Load per-sample, QC-filter (n_genes 200-6000, pct_mt<25),
concatenate. On a memory ceiling, keep the primary two-group contrast and
hold out extra groups. Normalize -> HVG -> PCA -> Harmony (by subject) ->
neighbors -> Leiden -> UMAP. Annotate clusters with marker score sets.
Composition shift per cell type (per-sample fractions, Mann-Whitney) and
per-cell-type case-vs-control DE. Save a slim (gzip) h5ad checkpoint,
UMAP/composition/dotplot figures, composition + cell-type-DE CSVs.
Note: granulocytes (eosinophils/neutrophils) often drop out of droplet
scRNA-seq - absence of a cluster is not absence of the cell. harmonypy
Z_corr orientation varies by version - verify shape is (cells x PCs)
before assigning to obsm.

## Stage 7 - Pathway / regulator / communication
Enrichr via gseapy on up/down signature (GO_BP, Reactome, Hallmark) and TF
libraries (ChEA, ENCODE, TRRUST) for upstream regulators. Single-cell
cell-cell communication with `liana.mt.rank_aggregate` on the case cells.
Save enrichment tables + a pathway/regulator figure + LR dotplot. (Enrichr
server maayanlab.cloud may need a network-access grant.)

## Stage 8 - Multi-omics integration
Build a per-gene evidence table combining independently-varying layers:
bulk-meta significance, cross-study reproducibility (k), single-cell
up-confirmation. **Compute the layer-count score over the FULL signature**,
not a pre-filtered subset - on an already-gated table the significance/k
terms are constant and the "multi-layer" score collapses to one axis.
Cross-check with an orthogonal layer (e.g. miRNA: down-miRNA vs up-target).
Watch assay sign conventions (TaqMan Ct is inverse to expression). Save the
evidence table + integration figure.

## Stage 9 - Druggability
Open Targets GraphQL (`api.platform.opentargets.org/api/v4/graphql`) per
target: `tractability`, `drugAndClinicalCandidates`, `subcellularLocations`,
`targetClass`. **Introspect the schema first** - field names drift
(`knownDrugs` -> `drugAndClinicalCandidates`; rows carry `maxClinicalStage`,
not `phase`). Composite priority score: effect size + reproducibility +
single-cell confirmation + accessibility (secreted > surface > intracellular
for biologics) + AB-tractability + clinical precedent + existing
pharmacology. Flag membrane-annotation false positives and ubiquitous
targets (e.g. HLA) for manual triage. Save `target_druggability.csv` + figure.

## Stage 10 - Consolidate
Curate a Tier-A shortlist (biological specificity + accessibility), add
mechanism rationale and a suggested modality per target, and write a report
+ integrated summary dashboard. State limitations honestly (dropout,
underpowered layers, annotation caveats).

## Reproducibility rules
`fig, ax = plt.subplots()` then `fig.savefig(...)` - never bare `plt.*`.
Fetches in their own cell. Save expensive state as a checkpoint (harmonized
bundle, slim h5ad), not every transform.
