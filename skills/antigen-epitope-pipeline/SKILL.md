---
name: antigen-epitope-pipeline
description: Map antigen proteins to MHC-II/I binding epitopes and per-HLA burden for a personalized, disease-agnostic pMHC pipeline. Use when building food/auto/microbial-antigen epitope panels (EoE, celiac, T1D, IBD), predicting which peptides a patient's HLA can present, or designing antigen-specific T-cell diagnostics/tolerance reagents. Covers antigen->UniProt->peptide-window->MHC-prediction->burden, and the presentation-vs-pathology guardrail.
---

# Antigen-epitope / pMHC pipeline

A reusable, disease-agnostic pipeline for turning a set of candidate antigens
into an HLA-resolved epitope map: **antigen set -> UniProt sequences -> peptide
windows -> MHC-II/I binding prediction -> per-HLA burden -> personalized panel**.
Built for EoE (food allergens x HLA-DR/DQ) but the antigen set and HLA panel are
parameters — swap them for celiac (gluten x DQ2.5/DQ8), T1D (islet autoantigens),
IBD (microbial/self-antigens), or any class-II-restricted disease.

`kernel.py` ships the pure-compute helpers (`fetch_uniprot_fasta`,
`sliding_windows`, `summarize_binders`, `unique_core_count`; and for
deamidation-driven diseases `tg2_deamidation_sites`, `deamidate`,
`deamidation_windows`, `benchmark_known_epitopes`). The MHC-prediction step is
env-specific and described below.

## The one guardrail that matters: presentation != pathology

**A binding prediction says a peptide CAN be presented on a given MHC. It does
NOT say that peptide drives disease.** Disease requires an expanded, pathogenic
effector-T-cell clone specific for that peptide. Binding/burden is only a
PRIOR — which pools to build and test first. The specificity-defining evidence
is always a FUNCTIONAL readout (antigen-specific Th2/peTh2 by AIM assay or
tetramer on patient cells). This was learned concretely in EoE: a patient's
DQ2.2 presented wheat gluten at high burden, yet the patient tolerated wheat
(negative functional response, negative tTG-IgA). Never name a trigger, or
claim pathogenicity, from binding prediction alone. Report HLA-presentation
findings as *risk/capacity*, not *disease*.

## Workflow

### 1. Define the antigen set and HLA panel (the two swappable parameters)
- **Antigens:** list UniProt accessions for the disease's candidate proteins.
  Represent each source by its FULL clinically-relevant family, not a token
  protein (EoE milk lesson: omitting beta-casein CSN2/P02666 mis-ranked the
  patient's #1 trigger; complete casein family fixed it).
- **HLA panel:** population-representative class-II alleles (DRB1*01:01,
  03:01, 04:01, 07:01, 15:01; DQ heterodimers) or a patient's own typing for a
  personalized panel. For an inclusive platform, treat burden as a mechanistic
  covariate, never an enrollment gate — pair with a functional (HLA-agnostic)
  AIM readout.

### 2. Fetch sequences
```python
# python tool
recs = {acc: fetch_uniprot_fasta(acc) for acc in accessions}   # (header, seq)
```

### 3. Generate peptide windows
```python
windows = {acc: sliding_windows(seq, k=15) for acc, (h, seq) in recs.items()}  # class-II 15-mers
```

### 3b. (Deamidation-driven diseases) model post-translational editing

For celiac and other TG2/PAD-driven diseases the disease-relevant epitope is
the **deamidated** peptide, not the native one. TG2 converts Gln->Glu at
Q-X-Pro motifs, and the added negative charge is what fits the DQ2.5/DQ8 P4/P6
anchor pockets. Predict on BOTH native and deamidated forms and compare:

```python
from_native  = {acc: sliding_windows(seq, k=15) for acc, (h, seq) in recs.items()}
deamid_seqs  = {acc: deamidate(seq)            for acc, (h, seq) in recs.items()}
paired       = {acc: deamidation_windows(seq, k=15) for acc, (h, seq) in recs.items()}
#   paired[acc] -> [(start, native_15mer, deamidated_15mer, n_edits), ...]
```

Submit native and deamidated sequences as separate prediction runs (tag each
row with `form in {native, deamid}`). The mechanistic signal to report: how
many windows cross the strong-binder threshold ONLY after deamidation, and how
many are lost (in celiac the effect is strictly one-way — gains, ~zero losses).
`tg2_deamidation_sites` recovers ~77% of experimentally annotated sites;
non-canonical (e.g. glutenin) sites are under-called — state this.

### 4. Predict MHC binding (env-specific — pick one)
- **netMHCIIpan via IEDB** (`http://tools-cluster-interface.iedb.org/tools_api/mhcii/`,
  POST, `method=netmhciipan_ba` for IC50 nM). Run as a background cell over the
  antigen x allele grid; retry timeouts with a longer per-request timeout. This
  is the recommended primary predictor.
- **mhcnuggets** (local, in a TF env, e.g. `mhc`): class-II on DRB1 alleles,
  class-I via `mhcflurry`. Good for extending to many alleles offline;
  cross-validates with netMHCIIpan at Spearman rho ~= 0.79 on shared DR alleles.
- Class-I: `mhcflurry` (pan-allele, 9-mers) — use `DEFAULT_CLASSI_K=9`.
Collect predictions into a flat list of dicts: `{allele, antigen, peptide,
core, ic50}`.

### 5. Aggregate burden (pure helpers)
```python
summary = summarize_binders(rows)         # per_allele / per_antigen / total strong (IC50<500 nM)
n_cores = unique_core_count(rows)         # distinct strong cores — NOT the per-cell sum
```
**Gotcha:** the true number of unique binding cores dedups cores shared across
alleles; summing per-allele-per-antigen cells double-counts (the EoE "864 vs
470" bug). Use `unique_core_count`.

### 5b. Benchmark against a known-epitope ground truth (when one exists)

Some diseases have experimentally-mapped immunodominant epitopes (celiac:
Sollid nomenclature, doi:10.1007/s00251-012-0599-z). Use them to validate the
pipeline before trusting novel predictions:

```python
# rows = DEAMIDATED-form predictions [{allele, peptide, ic50, ...}]
# known = [{core, restricting_allele, name, immunodominant}]  (deamidated cores)
bench = benchmark_known_epitopes(rows, known)
bench["recall_at_threshold"]     # fraction recovered at IC50<500 nM
bench["allele_preference"]       # correct-restricting-allele fraction
```

**Critical calibration lesson (HLA-DQ):** netMHCIIpan is far less benchmarked on
DQ than DR and systematically UNDER-scores DQ affinity. Canonical celiac
epitopes are potent T-cell activators yet score as *weak* by IC50 (DQ2.5-glia-
a1a ~1900 nM, above the 500 nM cutoff). So recall at a fixed IC50 threshold can
be ~0% even when the method works. What DOES validate: (1) **allele preference**
— the known epitope's best IC50 is lower on its restricting allele than on the
others (celiac: 11/11 DQ2.5-restricted correct); (2) **within-allele percentile
rank**; (3) **deamidation improves recovery** (lower IC50 vs native). Report
these RELATIVE metrics for DQ, not the absolute strong/weak call.

### 6. Rank, but confirm functionally
Rank antigens by strong-binder burden to prioritize pools — then STOP and route
to the functional assay (see the guardrail). The ranking is a hypothesis, not a
diagnosis.

## Deliverables to produce
- `<disease>_epitope_panel.csv` — all predictions (allele x antigen x peptide x IC50; native+deamidated form column if applicable)
- `<disease>_epitope_load.csv` — per-antigen / per-allele strong-binder burden
- `<disease>_deamidation_map.csv` + native-vs-deamidated shift (deamidation-driven diseases)
- `<disease>_epitope_benchmark.csv` — recall / allele-preference vs known epitopes (when a ground truth exists)
- an epitope heatmap + per-antigen load bar (use `figure-style`)
- a personalized panel if patient HLA is supplied

## Provenance / honesty rules
- All predictions are computational PRIORS; state this in every output.
- DQ predictions are less benchmarked than DR — flag magnitudes as approximate.
- For any translation-bound claim, do a named-investigator prior-art search
  (the EoE food-specific-TCR paradigm is patented — Dilollo/Spergel/Hill 2025,
  doi:10.1016/j.jaci.2025.01.008).
