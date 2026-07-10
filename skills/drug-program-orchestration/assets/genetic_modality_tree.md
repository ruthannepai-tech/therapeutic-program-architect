# Genetic mechanism → modality decision tree

Companion to `genetic_modality_tree.csv` and the `recommend_modality_genetic()` helper. Used at
**Stage 5** when the disease archetype (set at ARCHETYPE LOCK) is `monogenic` (or another
genetic archetype where a mechanism of pathogenesis is defined).

> **Mechanism of pathogenesis is a claim that must be human/clinically confirmed** before it
> drives a modality choice. The tree proposes a default at the TARGET/MODALITY LOCK gate; it
> does not commit. Ground the mechanism in ClinVar variant interpretation, ClinGen dosage/
> validity curation, gnomAD constraint, and the primary literature — then confirm with the user.

## How to read it

The pathogenic mechanism determines the therapeutic logic:

1. **Loss-of-function (recessive / null)** → *restore function.* Gene replacement (AAV/LNP cDNA)
   is first-line; if the missing product is a secreted or lysosomal enzyme, enzyme replacement is
   an established alternative. Nonsense-specific: read-through.
2. **Loss-of-function (haploinsufficient)** → *raise dosage.* Gene replacement/augmentation, or
   upregulation of the intact allele (splice-modulating ASO). Watch overexpression toxicity —
   dosage is dose-sensitive by definition (low gnomAD LOEUF / high pLI confirms this).
3. **Nonsense (premature stop)** → *read through or correct.* Small-molecule ribosomal
   read-through, or base/prime editing / gene replacement to fix the codon.
4. **Gain-of-function / toxic-RNA / repeat-expansion** → *remove the bad product.* Knock down the
   mutant transcript with an ASO (RNase-H gapmer) or siRNA; allele-selective where a SNP allows;
   editing to excise/knock out as an alternative.
5. **Dominant-negative** → *silence the bad allele selectively.* Allele-selective ASO/siRNA
   (spare the wild-type), or allele-specific editing.
6. **Splice-altering** → *fix the splicing.* Steric-block splice-switching ASO (exon inclusion or
   skipping).

## Delivery is often the crux, not the coding sequence

For genetic medicines the deliverable that decides success is usually the **delivery vehicle and
route**, not the payload sequence:
- **AAV** — serotype/tropism must match the target tissue; ~4.7 kb payload ceiling; pre-existing
  immunity and re-dosing are constraints.
- **LNP** — systemic/hepatic default; editor + guide co-delivery.
- **GalNAc conjugate** — hepatocyte-restricted siRNA/ASO.
- **Intrathecal** — CNS ASOs (the SMA/ALS precedents); the BBB is the limiting factor for CNS
  enzyme/protein and systemic oligos.
- **Ex-vivo** — HSC/T-cell editing then re-infusion (avoids in-vivo delivery, adds manufacturing).

Stage 6 records the delivery consideration from the route (`design_skills_for(modality)["delivery"]`)
and flags it as a program risk in the scientific plan.

## Precedents (illustrative, not a completeness claim)
The `approved_precedent` column names real approved or clinical-stage programs for each mechanism
(e.g. nusinersen for SMN2 splice modulation, onasemnogene for SMN1 replacement, tofersen for SOD1
knockdown, patisiran-class siRNA, casimersen for DMD exon skipping). They anchor feasibility;
they are not a claim that the same approach transfers to a new gene without validation.
