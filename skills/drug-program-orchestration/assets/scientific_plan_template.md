# Scientific Development Plan — {{DISEASE}} / {{PROGRAM_NAME}}

> Stage-7 template. Fill each `{{…}}` from the program dossier (Stages 4–6). Keep every claim
> traceable to a retrieved source or a generated result; flag anything needing wet-lab or
> clinical validation as an explicit open question with a go/no-go gate.

## 0. Program summary
- **Indication / scope:** {{DISEASE}} — {{POPULATION_SCOPE}}
- **Lead target(s):** {{LEAD_TARGETS}}  (evidence basis: {{TARGET_EVIDENCE}})
- **Modality:** {{MODALITY}}  (rationale: {{MODALITY_RATIONALE}})
- **Top patient priorities addressed:** {{PATIENT_PRIORITIES}}
- **One-line thesis:** {{THESIS}}

## 1. Computational design engine
- Target structure source ({{PDB_OR_ALPHAFOLD}}) and preparation (chain/domain selection,
  signal-peptide handling, hotspot/epitope definition: {{HOTSPOTS}}).
- Design method for the modality ({{DESIGN_SKILLS}}) and key parameters.
- In-silico validation: fold-back tool(s) {{VALIDATION_SKILLS}}, interface/quality metrics
  and thresholds ({{METRIC_THRESHOLDS}}, e.g. ipTM ≥ 0.85).
- Lead selection criteria and the selected lead(s): {{LEADS_TABLE}}.
- Sequence-level analysis / embeddings / liabilities (ESM): {{LIABILITY_NOTES}}.

## 2. In-vitro assay cascade
1. **Expression & QC** — construct format, expression system, purity/identity QC.
2. **Biophysics / binding** — affinity + kinetics (SPR/BLI), thermal/colloidal stability.
3. **Functional / cellular** — the mechanism-specific potency assay ({{FUNCTIONAL_ASSAY}}),
   plus the disease-relevant cellular readout.
- Go/no-go per tier: {{ASSAY_GONOGO}}.

## 3. Delivery & formulation
- Route, schedule, format ({{FORMAT}} — e.g. IV antibody, tolerogenic nanoparticle, oral SM).
- Formulation/stability considerations and any delivery-vehicle design.

## 4. Preclinical package
- Proof-of-concept model(s): {{POC_MODEL}}.
- PK/PD, biodistribution, and the GLP toxicology plan.
- Translational relevance and limitations of the model.

## 5. CMC & IND strategy
- Manufacturing route; platform vs. individualized framing ({{PLATFORM_NOTE}}).
- Release strategy; IND-enabling package scope and sequencing.

## 6. Companion diagnostic (if applicable)
- Biomarker(s), assay, and how patient selection / response monitoring works: {{CDX}}.

## 7. Translational PD / biomarker strategy & go/no-go gates
- Pharmacodynamic / target-engagement biomarker: {{PD_BIOMARKER}}.
- Efficacy-anchoring biomarker tied to the patient-priority endpoints.
- **Decision gates:** {{GONOGO_GATES}} — each with the criterion that advances or kills.

## 8. Open questions & required validation
{{OPEN_QUESTIONS}}  ← pull from dossier.open_questions; mark those needing clinical validation.
