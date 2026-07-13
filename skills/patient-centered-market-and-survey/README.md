# patient-centered-market-and-survey

A [Claude Science](https://claude.ai) skill for producing **two complementary
deliverables** for a therapeutic program in any chronic or rare disease:

1. **A patient-centered market report** — disease/epidemiology context, market
   sizing (TAM/SAM/SOM), competitive landscape + whitespace, pipeline map,
   patient journey, regulatory precedent, market access + value-based pricing,
   and an explicit patient-voice section.
2. **A patient-community survey** — a patient-partnership-first instrument
   (research questions → domains, validated-instrument anchoring, sampling,
   recruitment through patient organizations, analysis plan, ethics/plain-language)
   plus an execution kit that stands up a live anonymous Google Form and
   recruitment copy in minutes.

The two reinforce each other: the market report states what a program *assumes*
patients want and will tolerate; the survey *tests* those assumptions with the
people the therapy is meant to serve.

## Contents

```
patient-centered-market-and-survey/
├── SKILL.md          # the skill definition + full workflow
├── kernel.py         # helpers: market_sizing, value_based_price, generate_form_script
├── templates/
│   ├── market_report_outline.md
│   ├── survey_design_blueprint.md
│   └── survey_distribution_kit.md
└── examples/         # eosinophilic-esophagitis worked instance
```

## Quick start

```python
from kernel import market_sizing, value_based_price, generate_form_script

s = market_sizing(335_000_000, 1/2000, 0.60, 0.55, 0.15,
                  chronic_annual_price=40_000, one_course_price=150_000)
print(s["table_md"])

open("build_form.gs", "w").write(
    generate_form_script("Patient Perspectives", "Anonymous, ~5 min."))
```

## Provenance & disclaimers

Distilled from a real eosinophilic-esophagitis therapeutic project (see
`examples/`). Market figures are assumption-driven planning estimates, **not**
investment guidance. Survey instruments require patient-advisor review and IRB
approval before fielding. Nothing here is medical advice.

Generated with Claude Science.
