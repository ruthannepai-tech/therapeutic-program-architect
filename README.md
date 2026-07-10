# Therapeutic Program Architect

An end-to-end, human-in-the-loop **therapeutic drug-development pipeline** that runs on
[Claude Science](https://www.anthropic.com). It takes an indication from unmet need and patient
priorities, through data-, literature-, and genetics-mined target and modality selection, AI/ML
computational design and in-silico pressure-testing, to the scientific, regulatory, and
commercial strategy and final deliverables (business plan, scientific plan, pitch deck,
manuscript).

It works as a **conductor**: rather than reimplementing analyses, it sequences existing catalog
skills stage by stage and threads one program dossier (`program_dossier.json`) through the whole
pipeline as the source of truth, stopping for human validation at every consequential fork.

> **Not a substitute for professional judgment.** This is research and planning software. Every
> target, modality, endpoint, price, and go/no-go decision is surfaced for human confirmation —
> the pipeline never commits one autonomously. Genetic diagnosis and mechanism-of-pathogenesis
> are clinical claims requiring expert validation. Feasibility verdicts are heuristics to
> structure a decision, not validated instruments.

## What's in this repo

```
skills/drug-program-orchestration/   # the pipeline skill (load into Claude Science)
  SKILL.md                           # conductor spec: 10 stages, gates, composition map
  kernel.py                          # pure-compute helpers (dossier, gates, routers, verdict)
  stage_spec.md                      # full per-stage blueprint (goal/inputs/outputs/gate)
  checkpoint_protocol.md             # human-in-the-loop rules + patient-centered conduct
  assets/                            # gate map, dossier schema, rubrics, decision trees, templates
agent/
  agent_manifest.json                # portable agent profile (system prompt + connector loadout)
deploy_agent.py                      # helper to recreate the agent profile from the manifest
```

## The 10 stages

1. Indication & unmet need · **1b. Archetype lock** (genetic architecture, mechanism, data
   density) · 2. Patient priorities / PFDD · 3. Literature + competitive-pipeline map ·
   4. Data mining → target nomination · 5. Target & modality selection · 6. Design &
   computational pressure-test · 7. Scientific development plan · 8. Regulatory strategy ·
   9. Commercial & financing · 10. Deliverables & synthesis.

The pipeline is **archetype-adaptive**: common/polygenic data-rich diseases run the omics-
discovery path; monogenic/rare diseases (where the causal gene is known, data are sparse, and
there are no prior trials) run a genetics-led path with a mechanism→modality decision tree and a
rare-disease regulatory + ultra-rare commercial toolkit.

## Deploy it

You need a **Claude Science** workspace (the skill and agent run there; they are not standalone
scripts).

### 1. Install the skill

Copy `skills/drug-program-orchestration/` into your Claude Science skills, or publish it
programmatically from a Claude Science session (via the `customize` skill's `host.skills` SDK):

```python
# in a Claude Science repl cell
import os
base = "skills/drug-program-orchestration"
for dirpath, _, files in os.walk(base):
    for fn in files:
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, base)            # e.g. "SKILL.md", "assets/checkpoint_map.csv"
        host.skills.edit("drug-program-orchestration", rel, open(p).read())
host.skills.publish("drug-program-orchestration")
```

Once published it appears in the live catalog; load it in any session with
`skill({skill: "drug-program-orchestration"})`.

### 2. Recreate the agent profile

Run `deploy_agent.py`'s logic from a Claude Science repl cell (it uses the `host.agents` SDK,
documented in the `customize` skill). It reads `agent/agent_manifest.json` and creates the
profile with full catalog access, then attaches the connectors listed in the manifest.

```python
# in a Claude Science repl cell — see deploy_agent.py for the full version
import json
m = json.load(open("agent/agent_manifest.json"))
host.agents.create(m["name"], m["display_name"], m["description"],
                   system_prompt=m["system_prompt"])   # unrestricted (full catalog + connectors)
```

An `unrestricted` profile already reaches every connector your workspace has, so you usually do
**not** need to attach them one by one — the manifest's connector list is a record of what the
pipeline expects (human-genetics: `variants`, `clinical-genomics`, `human-genetics`,
`genes-ontologies`; plus `omics-archives`, `chembl`, `drug-regulatory`, `clinical-trials`,
`literature`, `structures-interactions`, and more).

### 3. Run it

Switch to the profile (or select "Therapeutic Program Architect" in the session picker) and give
it the trigger:

> Run a therapeutic program for &lt;disease&gt;.

It initializes the dossier and opens with a **SCOPE LOCK** checkpoint, then **ARCHETYPE LOCK** —
and proceeds stage by stage, stopping for your confirmation at each gate.

## Connectors & compute

- **Data/knowledge connectors** are MCP servers available inside Claude Science (Ensembl, gnomAD/
  ClinVar, ClinGen/Open Targets, GEO/PRIDE, ChEMBL, ClinicalTrials.gov, Drugs@FDA, GWAS Catalog,
  PDB/AlphaFold, etc.). The manifest records which ones the pipeline uses.
- **Stage 6 design** (binder/epitope/construct modeling) uses GPU skills (ProteinMPNN, Boltz,
  AlphaFold2, ESM, DiffDock, Evo2, …) and needs a compute target configured in your workspace.

## Provenance

Generalized from the EoE "Project Tolera" program built during the *Built with Claude: Life
Sciences* hackathon. Disease-, modality-, and archetype-agnostic.

## License

MIT — see [LICENSE](LICENSE).
