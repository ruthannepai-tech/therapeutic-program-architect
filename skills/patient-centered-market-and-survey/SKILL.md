---
name: patient-centered-market-and-survey
description: >
  Produce a patient-centered therapeutic market report AND design a
  patient-community survey for a disease indication. Use when the task is to
  size a market for a drug/biologic/novel modality, map the competitive
  landscape and find whitespace, build a modular market/commercial report, OR
  to design and field a patient-partnership survey (research questions,
  sampling, recruitment via patient orgs, validated-instrument anchoring,
  analysis plan, ethics/plain-language) and hand responses off for analysis.
  Trigger on "market report", "market sizing", "TAM/SAM/SOM", "competitive
  landscape", "commercial analysis", "patient survey", "survey design",
  "patient perspectives", "patient-focused drug development / PFDD", or "poll
  the patient community". Disease-agnostic; ships an eosinophilic-esophagitis
  worked example. NOT for statistical analysis of returned survey CSVs — that
  is a downstream analysis step.
---

# Patient-Centered Market Report & Patient-Community Survey

Two complementary deliverables for a therapeutic program, both organized around
the principle that a market is made of patients, not just dollars:

- **Workflow A — Patient-centered market report.** A modular commercial/market
  document: disease + epidemiology context, patient-experienced burden, market
  sizing (TAM/SAM/SOM), competitive landscape and whitespace, pipeline map,
  patient journey, regulatory precedent, market access + value-based pricing,
  and an explicit patient-voice section. Every section is anchored to real
  precedent, not assumption.
- **Workflow B — Patient-community survey.** A patient-partnership-first survey:
  research questions, sampling (with pediatric/caregiver strata where relevant),
  recruitment through trusted patient organizations, domains mapped to validated
  instruments, an analysis plan, and ethics/plain-language design — plus an
  execution kit that stands up a live anonymous form and recruitment copy in
  minutes.

The two reinforce each other: the market report states what the program
*assumes* patients want and will tolerate; the survey *tests* those assumptions
with the people the therapy is meant to serve, and feeds the report's
patient-voice section with primary data.

> Guardrail: nothing produced here is medical advice or investment guidance.
> Market figures are assumption-driven planning estimates — state assumptions
> inline. Survey instruments require patient-advisor review and IRB approval
> before fielding.

---

## When to use which workflow

| The ask… | Use |
|---|---|
| "Size the market / build a market report / competitive landscape" | Workflow A |
| "Design a patient survey / poll the community / PFDD prep" | Workflow B |
| "Full go-to-market package for indication X" | Both (A first, then B to test A's assumptions) |
| "Analyze these survey responses (CSV)" | Neither — this is downstream; use a survey-analysis skill |

`templates/` holds ready-to-fill scaffolds; `kernel.py` provides the sizing math
and the form-generator so you don't hand-compute or hand-write boilerplate.

---

## Workflow A — Patient-centered market report

Build the report section by section. Each section is a separate markdown file so
sections can be drafted, reviewed, and revised independently, then concatenated.
`templates/market_report_outline.md` is the fillable scaffold.

**A1. Disease-area & epidemiology context.** Size the *disease* before the
market: prevalence/incidence (with trend), standard of care and why it is
non-curative, treatment burden as patients experience it (procedures, dietary
restriction, chronic dosing, disease progression). If the program spans multiple
candidate indications, build a comparative snapshot table (driving antigen/target,
genetic restriction, biomarker, standard of care, existing tolerance/curative
therapy, opportunity) so the lead indication's rationale is explicit.

**A2. Market sizing (TAM/SAM/SOM).** Use `market_sizing()` from `kernel.py`.
Layer prevalence → diagnosed → serviceable-addressable (eligible sub-population)
→ obtainable (realistic mature share). State every fraction and its basis. Then
run `value_based_price()` to frame a durable/one-course therapy against the
lifetime cost it displaces (payback period, cumulative payer savings) — the
value-based-pricing argument incumbents on chronic dosing cannot make.

**A3. Competitive landscape & whitespace.** Table every approved and pipeline
agent: company, mechanism, dosing cadence, and the axes your program is
differentiated on (e.g. mechanism specificity, durability off-therapy). Identify
the structural feature competitors *share* — that shared feature defines the
whitespace your program occupies alone. Note field signals honestly, including
failures (a discontinued competitor is evidence about the endpoint, not just
good news).

**A4. Pipeline map, patient journey, regulatory, market access.** Separate
short sections: the therapeutic pipeline by phase; the patient journey from
symptom to diagnosis to management (surface the friction points a new therapy
removes); regulatory precedent and likely path (relevant approvals, endpoints,
COAs, breakthrough/orphan angles); and market-access/reimbursement logic
(coverage comparators, the payer conversation your pricing enables).

**A5. Patient-voice section.** This is what makes the report patient-*centered*
rather than patient-*adjacent*. Summarize lived-experience insight — ideally
primary data from Workflow B, otherwise sourced patient-org/registry findings —
on burden ranking, outcome priorities, and risk/route tolerance. If the founder
or team includes patients, state that standing; it is a design input, not a
footnote.

**A6. Assumptions & sensitivities.** Close with a table of every planning
assumption, the value used, and its sensitivity/direction. Diligence-grade
honesty here is what makes the rest credible.

Concatenate the section files into the final report and `save_artifacts` both the
sections and the assembled document. Keep a one-page executive framing at the top.

---

## Workflow B — Patient-community survey

Four principles govern the design (from `templates/survey_design_blueprint.md`):

1. **Nothing about us without us.** Patients/caregivers co-design the instrument;
   drafted items are a starting point for patient-advisor revision, not final.
2. **Anchor to lessons already paid for.** Treat known program failures and
   adoption problems in adjacent indications as empirical priors — design items
   that would detect the analogous failure mode (e.g. safety-risk tolerance,
   schedule/route burden) *before* it is built into a program.
3. **Measure what patients feel, with tools patients helped build.** Anchor to
   validated instruments where they exist (for comparability and regulatory
   relevance); build new items transparently where they don't.
4. **Companion to, not replacement for, a formal PFDD meeting.** The survey
   generates the substrate that can seed one.

**B1. Research questions → domains.** Turn the program's open questions into
7–9 survey domains: current burden, understanding of the proposed modality,
efficacy expectations / minimum acceptable benefit, route & schedule tolerance,
risk tolerance, prior-treatment history & fatigue, trust/consent/information
needs, companion-diagnostic acceptability, and desired ongoing involvement +
demographics. Draft 3–5 items per domain (mix of Likert, single-choice,
checklist, ranked, and open-text). Use the blueprint template.

**B2. Anchor domains to validated instruments.** Map burden/symptom and
quality-of-life domains to recognized clinical outcome assessments and
general-purpose instruments (disease-specific COAs; PROMIS short forms for
fatigue/global-health/anxiety) so patient-defined "meaningful improvement" can
later be benchmarked against trial endpoints. Flag which domains have *no*
validated instrument — those are the survey's novel contribution and future
psychometric-validation candidates.

**B3. Sampling & recruitment.** Define strata (age band, age at diagnosis,
disease-control status, current management, sociodemographic diversity with
deliberate oversampling of underrepresented groups). For pediatric-onset
diseases, include caregiver-proxy and adolescent-assent instruments. Recruit
through trusted patient-community channels first (patient advocacy
organizations, disease registries consented for research contact, clinical
research consortia for a clinically-verified subgroup), then snowball/social.
Set a descriptive/exploratory target n; state it is not hypothesis-testing-powered.

**B4. Analysis plan.** Quantitative: descriptives for all closed items; segment
comparisons (chi-square/Fisher for categorical, Kruskal–Wallis for ordinal
Likert); composite burden/risk scores; latent-class/cluster analysis to surface
patient segments if n allows. Qualitative: inductive thematic coding of open-text
by ≥2 coders including a patient co-analyst. Report by pediatric/caregiver vs.
adult and by severity to avoid masking divergent needs in an averaged patient.

**B5. Ethics & plain language.** 6th–8th-grade reading level, health-literacy
checklist, cognitive-interview pilot (5–10 respondents) before fielding. Layered
consent (short summary + expandable detail). The modality explainer must convey
mechanism and its real risks honestly without inducing alarm or false
reassurance. IRB approval before any data collection; state that respondents
are directed to their own clinicians for medical decisions.

**B6. Execution kit — stand up the live form.** For a fast anonymous field:
- Call `generate_form_script(...)` from `kernel.py` to emit a Google Apps Script
  (`build_form.gs`) that builds the form with **email collection OFF**,
  **one-response-per-user OFF** (no forced sign-in), progress bar ON — nothing
  identifying stored. Paste into script.google.com → New project → Run → copy the
  LIVE FORM url from the execution log.
- Use `templates/survey_distribution_kit.md` for short/long recruitment messages
  (texts vs. patient-community forums) and community-etiquette tips (check group
  rules, offer to remove if not allowed).
- When responses arrive: Responses → Sheets → Download CSV → hand off to a
  survey-analysis step (a dedicated survey-analysis skill, if available).

---

## Quick start

```python
skill({"skill": "patient-centered-market-and-survey"})   # loads kernel.py helpers
```

```python
# Market sizing
s = market_sizing(
    population=335_000_000, prevalence=1/2000, diagnosed_frac=0.60,
    eligible_frac=0.55, mature_som_frac=0.15,
    chronic_annual_price=40_000, one_course_price=150_000)
print(s["table_md"])          # TAM/SAM/SOM markdown table
print(s["som_annual_revenue"])

vb = value_based_price(chronic_annual_price=40_000, one_course_price=150_000, horizon_years=10)
print(vb["payback_years"], vb["cumulative_savings"])

# Survey form
gs = generate_form_script(title="EoE Patient Perspectives",
                          description="~5 min, anonymous.",
                          items=[...])   # or use the built-in example schema
open("build_form.gs", "w").write(gs)
```

See `templates/` for the fillable report outline, survey blueprint, distribution
kit, and a reference Apps Script. The `examples/` folder holds the
eosinophilic-esophagitis worked instance these were distilled from.
