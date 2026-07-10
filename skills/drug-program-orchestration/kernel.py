"""
kernel.py — helpers for drug-program-orchestration.

Pure-compute state + gating helpers for the conductor. Functions only (no top-level
classes/decorators) so the sidecar auto-loads into the kernel when the skill is loaded.

State lives in a workspace JSON file (default ./program_dossier.json). Helpers read/write it;
the orchestrator makes the actual ask_user / save_artifacts / skill tool calls — helpers never
call tools.
"""

import os
import json
import datetime

DOSSIER_PATH = "program_dossier.json"
SCHEMA_VERSION = "1.1"

# Canonical 10-stage names (ids are strings "1".."10").
STAGE_NAMES = {
    "1": "Indication & unmet need",
    "2": "Patient priorities / PFDD",
    "3": "Literature + competitive-pipeline map",
    "4": "Data mining -> target nomination",
    "5": "Target & modality selection",
    "6": "Design & computational pressure-test",
    "7": "Scientific development plan",
    "8": "Regulatory strategy",
    "9": "Commercial & financing",
    "10": "Deliverables & synthesis",
}

# gate_name -> (stage_id, type). Mirrors assets/checkpoint_map.csv.
# ARCHETYPE LOCK fires at Stage 1b (right after SCOPE LOCK) and reshapes Stages 3/4/5/8/9.
GATES = {
    "SCOPE LOCK": ("1", "hard"),
    "ARCHETYPE LOCK": ("1b", "hard"),
    "PRIORITY RANK": ("2", "soft"),
    "WHITESPACE CONFIRM": ("3", "hard"),
    "DATA SUFFICIENCY": ("3b", "soft"),
    "TARGET EVIDENCE": ("4", "soft"),
    "TARGET/MODALITY LOCK": ("5", "hard"),
    "DESIGN GO/NO-GO": ("6", "hard"),
    "REG ASSUMPTIONS": ("8", "soft"),
    "FINANCING ASSUMPTIONS": ("9", "hard"),
    "FINAL REVIEW": ("10", "hard"),
    "LOW CONFIDENCE": ("any", "soft"),
}

VALID_MODALITIES = [
    "antibody", "ligand_trap_binder", "small_molecule", "aso_rna",
    "cell_therapy", "vaccine", "enzyme", "gene_therapy", "peptide", "other",
    # genetic-disease modality families
    "gene_replacement", "enzyme_replacement", "aso_knockdown", "sirna_knockdown",
    "splice_switching_aso", "base_prime_editing", "crispr_nuclease", "readthrough",
]

# Disease archetypes on the genetic-architecture axis (set at ARCHETYPE LOCK).
ARCHETYPES = [
    "monogenic", "oligogenic", "polygenic_complex", "chromosomal",
    "mitochondrial", "somatic", "unknown",
]

# Mechanism of pathogenesis for monogenic disease (the axis that drives modality).
MECHANISMS = [
    "loss_of_function_haploinsufficient", "loss_of_function_recessive",
    "gain_of_function", "dominant_negative", "splice", "repeat_expansion",
    "nonsense", "toxic_rna", "unknown",
]

# Data-density tiers (drives the Stage-3/4 branch).
DATA_DENSITY = ["rich", "moderate", "sparse"]


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ----------------------------------------------------------------------------- dossier lifecycle
def init_dossier(disease, scope=None, path=None):
    """Create a fresh program dossier for `disease` and write it to `path`. Returns the dict."""
    if path is None:
        path = DOSSIER_PATH
    d = {
        "schema_version": SCHEMA_VERSION,
        "disease": disease,
        "scope": scope or {},
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "disease_archetype": None,          # one of ARCHETYPES; set at ARCHETYPE LOCK
        "mechanism_of_pathogenesis": None,  # one of MECHANISMS (monogenic); needs clinical validation
        "causal_gene": None,                # for monogenic: the known causal gene (often == target)
        "data_density": None,               # one of DATA_DENSITY; drives Stage-3/4 branch
        "modality": None,
        "lead_targets": [],
        "patient_priorities": [],
        "stages": {sid: {"name": name, "status": "not_started", "confidence": "na",
                          "skill_used": None, "artifacts": [], "summary": None}
                   for sid, name in STAGE_NAMES.items()},
        "gates": {g: {"type": t, "status": "pending", "question": None,
                      "resolution": None, "resolved_at": None}
                  for g, (s, t) in GATES.items()},
        "decisions": [],
        "open_questions": [],
        "deliverables": [],
    }
    save_dossier(d, path)
    return d


def load_dossier(path=None):
    """Load the dossier from `path`, or raise FileNotFoundError if not initialized."""
    if path is None:
        path = DOSSIER_PATH
    with open(path) as f:
        return json.load(f)


def save_dossier(d, path=None):
    """Persist the dossier, stamping updated_at. Returns the path."""
    if path is None:
        path = DOSSIER_PATH
    d["updated_at"] = utc_now()
    with open(path, "w") as f:
        json.dump(d, f, indent=2)
    return path


# ----------------------------------------------------------------------------- stage tracking
def update_stage(d, stage_id, status=None, confidence=None, skill_used=None,
                 artifacts=None, summary=None):
    """Update a stage entry in-place. `artifacts` is a list of dicts
    {filename, artifact_id, version_id} (extend, don't replace). Returns the stage dict."""
    sid = str(stage_id)
    st = d["stages"].setdefault(sid, {"name": STAGE_NAMES.get(sid, sid), "artifacts": []})
    if status:
        st["status"] = status
        if status == "in_progress" and "started_at" not in st:
            st["started_at"] = utc_now()
        if status in ("complete", "skipped"):
            st["completed_at"] = utc_now()
    if confidence:
        st["confidence"] = confidence
    if skill_used:
        st["skill_used"] = skill_used
    if summary:
        st["summary"] = summary
    if artifacts:
        st.setdefault("artifacts", []).extend(artifacts)
    return st


def stage_status(d):
    """Return an ordered list of (stage_id, name, status, confidence) for a quick progress view."""
    return [(sid, d["stages"][sid]["name"], d["stages"][sid]["status"],
             d["stages"][sid].get("confidence", "na"))
            for sid in sorted(d["stages"], key=lambda x: int(x))]


def next_stage(d):
    """Return the id of the first stage not yet complete/skipped, or None if all done."""
    for sid in sorted(d["stages"], key=lambda x: int(x)):
        if d["stages"][sid]["status"] not in ("complete", "skipped"):
            return sid
    return None


# ----------------------------------------------------------------------------- gates & decisions
def set_gate(d, gate_name, status, resolution=None, question=None):
    """Mark a named gate. status in {pending, passed, failed, skipped}. Returns the gate dict."""
    g = d["gates"].setdefault(gate_name, {"type": GATES.get(gate_name, ("any", "soft"))[1]})
    g["status"] = status
    if question:
        g["question"] = question
    if resolution is not None:
        g["resolution"] = resolution
    if status in ("passed", "failed", "skipped"):
        g["resolved_at"] = utc_now()
    return g


def record_decision(d, stage_id, decision, rationale=None, decided_by="user"):
    """Append a decision to the audit log. decided_by in {user, orchestrator}."""
    d["decisions"].append({
        "stage": str(stage_id), "decision": decision, "rationale": rationale,
        "decided_by": decided_by, "timestamp": utc_now(),
    })
    return d["decisions"][-1]


def add_open_question(d, stage_id, question, needs="user_input"):
    """Record an unresolved uncertainty. needs in
    {user_input, clinical_validation, more_data, expert_review}."""
    d["open_questions"].append({
        "stage": str(stage_id), "question": question, "needs": needs, "status": "open",
    })
    return d["open_questions"][-1]


def resolve_open_question(d, index):
    """Mark open_questions[index] resolved."""
    d["open_questions"][index]["status"] = "resolved"
    return d["open_questions"][index]


# ----------------------------------------------------------------------------- checkpoint formatting
def format_checkpoint(found, decision, recommendation, options, consequence=None):
    """Assemble the argument dict for an ask_user checkpoint from the five required parts.
    `options` is a list of dicts each with at least {label}; optional {description, pros, cons}.
    Returns {question, options} — the orchestrator adds its own `header` and makes the actual
    ask_user tool call (helpers cannot call tools)."""
    parts = [f"**What was found:** {found}",
             f"**Decision:** {decision}",
             f"**Recommendation:** {recommendation}"]
    if consequence:
        parts.append(f"**Consequence:** {consequence}")
    clean = []
    for o in options:
        if not isinstance(o, dict) or "label" not in o:
            raise ValueError("each option needs at least a 'label'")
        clean.append({k: v for k, v in o.items()
                      if k in ("label", "description", "pros", "cons")})
    return {"question": "\n\n".join(parts), "options": clean}


# ----------------------------------------------------------------------------- Stage 5 routing
def recommend_modality(target_facts):
    """Heuristic modality recommendation from target biology. `target_facts` is a dict with any of:
    localization ('secreted'|'cell_surface'|'intracellular'), role ('ligand'|'receptor'|'enzyme'|
    'driver'|'antigen'), is_antigen_specific_tolerance (bool), enzyme_deficiency (bool),
    has_chemical_matter (bool). Returns (modality, rationale). This is a DEFAULT to present at the
    TARGET/MODALITY LOCK gate, never an autonomous commitment."""
    f = {k: target_facts.get(k) for k in
         ("localization", "role", "is_antigen_specific_tolerance",
          "enzyme_deficiency", "has_chemical_matter")}
    if f.get("is_antigen_specific_tolerance"):
        return "vaccine", "Antigen-specific tolerance problem -> tolerizing vaccine / peptide construct."
    if f.get("enzyme_deficiency"):
        return "enzyme", "Loss-of-function enzyme deficiency -> enzyme replacement or gene therapy."
    loc, role = f.get("localization"), f.get("role")
    if loc == "secreted" or role == "ligand":
        return "ligand_trap_binder", "Secreted ligand -> neutralizing binder / ligand-trap (or antibody)."
    if loc == "cell_surface" or role == "receptor":
        return "antibody", "Cell-surface / receptor target -> antibody or engineered binder."
    if loc == "intracellular" or role == "driver":
        if f.get("has_chemical_matter"):
            return "small_molecule", "Intracellular driver with tractable chemistry -> small molecule."
        return "aso_rna", "Intracellular / undruggable-by-small-molecule -> ASO/RNA knockdown."
    return "other", "Insufficient biology to default a modality; decide with the user."


def design_skills_for(modality):
    """Return the ordered sub-skills/connectors Stage 6 should load for a modality. Returns a dict
    {design, validation, support, notes}."""
    m = (modality or "").lower()
    routes = {
        "antibody": {
            "design": ["proteinmpnn", "solublempnn", "ligandmpnn"],
            "validation": ["boltz", "chai1", "esmfold2", "alphafold2", "openfold3"],
            "support": ["fair-esm2"],
            "backbone_generation": "RFdiffusion (no catalog skill; run on GPU via remote-compute-modal/ssh + compute-env-setup)",
            "notes": "Structure fetch (RCSB/AlphaFold) -> backbones via RFdiffusion GPU job (see backbone_generation) -> inverse-fold with the 'design' skills -> fold-back with 'validation' skills -> interface metrics (ipTM/pLDDT/pAE) -> lead select.",
        },
        "small_molecule": {
            "design": ["diffdock"], "validation": ["boltz", "chai1"],
            "support": ["fair-esm2"],
            "notes": "mcp-chembl for chemical matter/mechanism -> docking -> co-fold validation.",
        },
        "vaccine": {
            "design": ["antigen-epitope-pipeline", "ligandmpnn"],
            "validation": ["esmfold2", "alphafold2", "boltz"], "support": ["fair-esm2"],
            "notes": "Epitope selection -> construct assembly -> complex/groove validation.",
        },
        "aso_rna": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "notes": "Sequence/regulatory modeling for oligo/RNA modality.",
        },
        "gene_therapy": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "notes": "Regulatory-element / cargo modeling.",
        },
        "enzyme": {
            "design": ["proteinmpnn", "solublempnn"],
            "validation": ["boltz", "esmfold2"], "support": ["fair-esm2"],
            "notes": "Sequence design + fold validation for enzyme/replacement construct.",
        },
        # ---- genetic-disease modality families ----
        "gene_replacement": {
            "design": ["evo2", "borzoi"], "validation": [], "support": ["fair-esm2"],
            "delivery": "AAV (serotype/tropism to target tissue) or LNP; payload size limit ~4.7kb for AAV",
            "notes": "Codon-optimized cDNA + regulatory cassette design (evo2/borzoi); protein-level QC of the transgene product with fair-esm2. Delivery vehicle is the crux, not the coding sequence.",
        },
        "enzyme_replacement": {
            "design": ["proteinmpnn", "solublempnn"],
            "validation": ["boltz", "esmfold2", "alphafold2"], "support": ["fair-esm2"],
            "delivery": "Recombinant protein IV; consider fusion tags for tissue/CNS uptake",
            "notes": "Recombinant enzyme sequence design + fold/stability validation; glycosylation and uptake-tag engineering are key.",
        },
        "aso_knockdown": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "delivery": "Chemistry (2'-MOE/PS gapmer); route intrathecal (CNS) or systemic",
            "notes": "Antisense oligo for RNase-H knockdown of a gain-of-function / toxic transcript. Sequence + off-target screen; no structure step.",
        },
        "sirna_knockdown": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "delivery": "GalNAc conjugate (hepatic) or LNP; RISC-mediated",
            "notes": "siRNA duplex design + off-target screen for knockdown of a dominant/toxic transcript.",
        },
        "splice_switching_aso": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "delivery": "Steric-block ASO (2'-MOE/PMO); intrathecal or systemic",
            "notes": "Steric-block ASO to correct splicing (exon inclusion/skipping). Precedent: nusinersen (SMN2 inclusion), casimersen (DMD exon skip).",
        },
        "base_prime_editing": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "delivery": "AAV/LNP of editor + guide; ex-vivo or in-vivo",
            "notes": "Guide/edit design for a defined point mutation; base editor for transitions, prime editor for small indels. Off-target + bystander-edit screen essential.",
        },
        "crispr_nuclease": {
            "design": ["evo2", "borzoi"], "validation": [], "support": [],
            "delivery": "LNP/AAV or ex-vivo; NHEJ knockout or HDR correction",
            "notes": "Guide design for knockout (dominant/GoF) or HDR correction; off-target screen essential.",
        },
        "readthrough": {
            "design": ["diffdock"], "validation": ["boltz", "chai1"], "support": [],
            "delivery": "Oral small molecule (ribosomal readthrough)",
            "notes": "Small-molecule readthrough of a premature nonsense codon (e.g. ataluren-class); mcp-chembl for chemical matter -> docking.",
        },
    }
    # ligand_trap_binder and peptide share the antibody/vaccine routes
    routes["ligand_trap_binder"] = routes["antibody"]
    routes["peptide"] = routes["vaccine"]
    return routes.get(m, {
        "design": [], "validation": [], "support": [],
        "notes": "No default route; choose design skills with the user based on the modality.",
    })


# ----------------------------------------------------------------------------- archetype + genetics
def classify_archetype(facts):
    """Classify the disease archetype from grounded facts (present at ARCHETYPE LOCK, never
    committed autonomously). `facts` is a dict with any of:
      inheritance ('monogenic'|'oligogenic'|'polygenic'|'chromosomal'|'mitochondrial'|'somatic'),
      n_causal_genes (int), clingen_validity ('definitive'|'strong'|'moderate'|'limited'|None),
      n_omics_cohorts (int), n_registered_trials (int), n_key_papers (int).
    Returns dict {archetype, data_density, rationale}. Archetype and mechanism are CLAIMS that
    require human/clinical validation — this only proposes a default for the gate."""
    inh = (facts.get("inheritance") or "").lower()
    ncg = facts.get("n_causal_genes")
    validity = (facts.get("clingen_validity") or "").lower()

    if inh in ("monogenic", "mendelian") or ncg == 1:
        archetype = "monogenic"
    elif inh == "oligogenic" or (isinstance(ncg, int) and 2 <= ncg <= 5):
        archetype = "oligogenic"
    elif inh in ("polygenic", "complex", "multifactorial"):
        archetype = "polygenic_complex"
    elif inh == "chromosomal":
        archetype = "chromosomal"
    elif inh == "mitochondrial":
        archetype = "mitochondrial"
    elif inh == "somatic":
        archetype = "somatic"
    else:
        archetype = "unknown"

    density = data_triage(facts.get("n_omics_cohorts", 0),
                          facts.get("n_registered_trials", 0),
                          facts.get("n_key_papers", 0))["data_density"]
    rat = (f"inheritance={inh or 'unspecified'}, causal_genes={ncg}, "
           f"clingen_validity={validity or 'n/a'} -> {archetype}; data_density={density}.")
    return {"archetype": archetype, "data_density": density, "rationale": rat}


def data_triage(n_omics_cohorts=0, n_registered_trials=0, n_key_papers=0):
    """Decide which Stage-3/4 path to run from data availability. Returns dict
    {data_density, stage4_path, stage3_path, note}.
    - rich    (>=3 omics cohorts): Stage 4 = omics DE meta-analysis; Stage 3 = full competitive review.
    - moderate(1-2 cohorts):       Stage 4 = single-study DE + genetics confirmation; Stage 3 = review + natural history.
    - sparse  (0 cohorts):         Stage 4 = genetics-led target/mechanism confirmation (no DE);
                                    Stage 3 = natural-history + analogous-modality precedent."""
    n = n_omics_cohorts or 0
    if n >= 3:
        density = "rich"
        s4 = "omics_de_meta_analysis"
        s3 = "full_competitive_review"
    elif n >= 1:
        density = "moderate"
        s4 = "single_study_de_plus_genetics"
        s3 = "competitive_review_plus_natural_history"
    else:
        density = "sparse"
        s4 = "genetics_led_confirmation"      # gnomAD constraint + ClinVar + ClinGen; no DE meta-analysis
        s3 = "natural_history_plus_analogous_precedent"
    note = (f"{n} omics cohort(s), {n_registered_trials or 0} trial(s), "
            f"{n_key_papers or 0} key paper(s) -> {density}.")
    return {"data_density": density, "stage4_path": s4, "stage3_path": s3, "note": note}


def recommend_modality_genetic(mechanism, constraint=None, target_facts=None):
    """Mechanism-of-pathogenesis -> modality for a monogenic disease. `mechanism` is one of
    MECHANISMS. `constraint` is an optional dict {loeuf: float, pli: float} (gnomAD gene
    constraint) that informs haploinsufficiency-driven calls. `target_facts` (optional) is passed
    through to recommend_modality() only when mechanism is unknown. Returns
    (modality, rationale, alternatives). This is a DEFAULT for the TARGET/MODALITY LOCK gate and
    mechanism MUST be human/clinically confirmed first."""
    m = (mechanism or "unknown").lower()
    loeuf = (constraint or {}).get("loeuf")
    hi = loeuf is not None and loeuf < 0.35  # low LOEUF => haploinsufficiency-intolerant

    if m == "loss_of_function_recessive":
        return ("gene_replacement",
                "Recessive null LoF -> restore function: gene replacement (AAV/LNP cDNA) or, if the "
                "product is a secreted/lysosomal enzyme, enzyme replacement.",
                ["enzyme_replacement", "readthrough", "base_prime_editing"])
    if m == "loss_of_function_haploinsufficient":
        base = ("gene_replacement",
                "Haploinsufficient LoF -> raise dosage: gene replacement/augmentation, or "
                "upregulation of the intact allele (ASO/splice modulation).",
                ["splice_switching_aso", "aso_knockdown", "base_prime_editing"])
        if hi:
            base = (base[0], base[1] + f" (LOEUF={loeuf} confirms dosage-sensitivity.)", base[2])
        return base
    if m == "nonsense":
        return ("readthrough",
                "Nonsense (premature stop) -> small-molecule ribosomal readthrough, or gene "
                "replacement / editing to correct the codon.",
                ["gene_replacement", "base_prime_editing"])
    if m in ("gain_of_function", "toxic_rna"):
        return ("aso_knockdown",
                "Gain-of-function / toxic transcript -> knock down the mutant message "
                "(ASO/siRNA), allele-selective where possible.",
                ["sirna_knockdown", "crispr_nuclease"])
    if m == "dominant_negative":
        return ("aso_knockdown",
                "Dominant-negative -> allele-selective knockdown of the mutant allele "
                "(ASO/siRNA), or allele-specific editing.",
                ["sirna_knockdown", "base_prime_editing", "crispr_nuclease"])
    if m == "splice":
        return ("splice_switching_aso",
                "Splice-altering variant -> steric-block splice-switching ASO to restore "
                "correct isoform.",
                ["base_prime_editing", "gene_replacement"])
    if m == "repeat_expansion":
        return ("aso_knockdown",
                "Repeat-expansion (toxic gain) -> knock down the expanded transcript (ASO/siRNA), "
                "or excise the repeat by editing.",
                ["sirna_knockdown", "crispr_nuclease"])
    # unknown mechanism: fall back to protein-biology router if we have target facts
    if target_facts:
        mod, rat = recommend_modality(target_facts)
        return (mod, "Mechanism unconfirmed; defaulted from target biology: " + rat,
                ["gene_replacement", "aso_knockdown"])
    return ("other",
            "Mechanism of pathogenesis not yet confirmed — resolve at the ARCHETYPE LOCK / "
            "TARGET-MODALITY gate before defaulting a modality.",
            [])


# ----------------------------------------------------------------------------- patient-centered lens
# Advisory only. Person-first is the default convention, but identity-first is preferred by some
# communities (e.g. many autistic and Deaf people). These are flags for human review, never an
# autonomous rewrite. Term -> (suggested people-first alternative, severity).
PEOPLE_FIRST_LEXICON = {
    "sufferer": ("person living with / people living with", "high"),
    "sufferers": ("people living with", "high"),
    "suffering from": ("living with", "high"),
    "victim": ("person affected by", "high"),
    "victims": ("people affected by", "high"),
    "afflicted": ("affected", "high"),
    "afflicted with": ("living with", "high"),
    "stricken": ("affected", "high"),
    "the disabled": ("disabled people / people with disabilities", "high"),
    "the handicapped": ("people with disabilities", "high"),
    "wheelchair-bound": ("wheelchair user", "high"),
    "confined to a wheelchair": ("wheelchair user", "high"),
    "mental retardation": ("intellectual disability", "high"),
    "retarded": ("person with an intellectual disability", "high"),
    "normal people": ("people without the condition / unaffected individuals", "medium"),
    "normals": ("unaffected individuals", "medium"),
    "high-functioning": ("describe the specific support need instead", "medium"),
    "low-functioning": ("describe the specific support need instead", "medium"),
    "diseased": ("affected", "medium"),
    "hopeless case": ("avoid; describe prognosis quantitatively", "high"),
}


def people_first_language(text):
    """Advisory people-first language check on user-facing prose. Returns
    {clean: bool, flags: [{term, count, suggestion, severity}], note}. It NEVER rewrites text —
    it surfaces terms for the orchestrator/user to reconsider. Person-first is the default; some
    communities prefer identity-first, so treat every flag as a prompt for judgment, not a rule."""
    low = (text or "").lower()
    flags = []
    for term, (suggestion, severity) in PEOPLE_FIRST_LEXICON.items():
        c = low.count(term)
        if c:
            flags.append({"term": term, "count": c, "suggestion": suggestion, "severity": severity})
    flags.sort(key=lambda f: (0 if f["severity"] == "high" else 1, -f["count"]))
    return {
        "clean": not flags,
        "flags": flags,
        "note": ("No flagged terms; still confirm the community's own preferred framing "
                 "(person-first vs identity-first)." if not flags else
                 "Flagged terms are advisory — some communities prefer identity-first language; "
                 "confirm the preferred framing with patient-org input before rewriting."),
    }


def program_verdict(d):
    """Build an HONEST, quantitative feasibility verdict + a patient-useful best-next-step from the
    dossier's recorded evidence — never fabricated optimism. Returns
    {tier, score, rationale, best_next_step, requires_human_confirmation}. The tier is derived
    transparently from recorded stage confidences, the TARGET-EVIDENCE / DESIGN gate outcomes,
    data density, and open-question load. It is a recommendation to present at FINAL REVIEW (or an
    early kill-or-pivot gate), NOT an autonomous go/no-go. When the therapeutic path is weak, the
    best-next-step is still the most useful thing that can be done for the community, not a drug."""
    conf_w = {"high": 1.0, "medium": 0.6, "low": 0.2, "na": None}
    scored = [conf_w[s.get("confidence", "na")] for s in d["stages"].values()
              if conf_w.get(s.get("confidence", "na")) is not None]
    conf_score = sum(scored) / len(scored) if scored else 0.0

    gates = d.get("gates", {})
    def gstat(name):
        return gates.get(name, {}).get("status")
    target_ok = gstat("TARGET EVIDENCE") == "passed"
    design_ok = gstat("DESIGN GO/NO-GO") == "passed"
    density = d.get("data_density")
    density_pen = {"rich": 0.0, "moderate": 0.1, "sparse": 0.25}.get(density, 0.1)
    n_open = len([q for q in d.get("open_questions", []) if q.get("status") == "open"])
    open_pen = min(0.3, 0.05 * n_open)

    score = max(0.0, min(1.0, conf_score
                         + (0.15 if target_ok else 0.0)
                         + (0.15 if design_ok else 0.0)
                         - density_pen - open_pen))

    if score >= 0.7 and target_ok:
        tier = "tractable"
        nxt = "Advance the lead(s) into the scientific development plan; the evidence supports a fundable program."
    elif score >= 0.45:
        tier = "conditional"
        nxt = ("Advance, but de-risk the named gaps first (resolve the open questions, widen "
               "evidence where thin) before committing design/financing spend.")
    elif score >= 0.25:
        tier = "weak"
        nxt = ("A drug program is not yet justified. The most useful next step for the community is "
               "likely foundational: a natural-history study, a patient registry, biomarker/endpoint "
               "development, or a repurposing screen — pick per the specific gaps and confirm with "
               "the patient organization.")
    else:
        tier = "not_yet_tractable"
        nxt = ("No tractable therapeutic path on current evidence. Recommend the honest verdict plus "
               "the highest-value research investment (natural history, genetic/mechanistic "
               "confirmation, registry) that would change it — do not present a speculative program "
               "as fundable.")

    rationale = (f"score={score:.2f} (mean stage confidence={conf_score:.2f}; "
                 f"target_evidence_gate={'passed' if target_ok else 'not passed'}; "
                 f"design_gate={'passed' if design_ok else 'not passed'}; "
                 f"data_density={density or 'unknown'}; open_questions={n_open}).")
    return {"tier": tier, "score": round(score, 2), "rationale": rationale,
            "best_next_step": nxt, "requires_human_confirmation": True}


# ----------------------------------------------------------------------------- deliverable manifest
def build_manifest(d):
    """Build a deliverable manifest (list of dicts) from the dossier: every artifact recorded per
    stage plus explicit deliverables, deduped by filename. Useful for the Stage-10 bundle README."""
    seen, manifest = set(), []
    for sid in sorted(d["stages"], key=lambda x: int(x)):
        st = d["stages"][sid]
        for a in st.get("artifacts", []):
            fn = a.get("filename")
            if fn and fn not in seen:
                seen.add(fn)
                manifest.append({"stage": sid, "stage_name": st["name"],
                                 "filename": fn, "artifact_id": a.get("artifact_id"),
                                 "version_id": a.get("version_id")})
    for dv in d.get("deliverables", []):
        fn = dv.get("filename")
        if fn and fn not in seen:
            seen.add(fn)
            manifest.append({"stage": "10", "stage_name": "Deliverables",
                             "filename": fn, "kind": dv.get("kind"),
                             "artifact_id": dv.get("artifact_id")})
    return manifest


def progress_report(d):
    """Return a compact markdown progress table of stages + gate status. For the user, not stdout."""
    lines = [f"# Program dossier — {d['disease']}", "",
             "| # | Stage | Status | Confidence | Gate |", "|--|--|--|--|--|"]
    inv = {}
    for g, meta in d["gates"].items():
        sid = GATES.get(g, ("?", ""))[0]
        # sub-stage gates (e.g. "1b", "3b") display under their parent stage row
        parent = sid.rstrip("abcdef") if sid not in ("any", "?") else sid
        inv.setdefault(parent, []).append(f"{g}:{meta['status']}")
    for sid in sorted(d["stages"], key=lambda x: int(x)):
        st = d["stages"][sid]
        gate = "; ".join(inv.get(sid, [])) or "—"
        lines.append(f"| {sid} | {st['name']} | {st['status']} | "
                     f"{st.get('confidence', 'na')} | {gate} |")
    oq = [q for q in d["open_questions"] if q["status"] == "open"]
    if oq:
        lines += ["", f"**Open questions ({len(oq)}):**"]
        lines += [f"- [{q['stage']}] {q['question']} _(needs: {q['needs']})_" for q in oq]
    return "\n".join(lines)
