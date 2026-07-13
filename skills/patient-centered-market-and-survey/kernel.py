"""Helpers for the patient-centered-market-and-survey skill.

Loaded into the kernel when the skill is loaded. Two workflows:
  - market_sizing / value_based_price  -> Workflow A (market report)
  - generate_form_script               -> Workflow B (survey execution kit)

All figures are assumption-driven planning estimates, not guidance.
"""


def fmt_int(n):
    return f"{int(round(n)):,}"


def fmt_money(n):
    n = float(n)
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.0f}k"
    return f"${n:,.0f}"


def market_sizing(population, prevalence, diagnosed_frac, eligible_frac,
                  mature_som_frac, chronic_annual_price=None,
                  one_course_price=None, basis=None):
    """Layered TAM/SAM/SOM market sizing for a therapeutic indication.

    Funnel: population -> prevalent -> diagnosed -> eligible (SAM) ->
    obtainable mature annual share (SOM).

    Args:
        population:        reference population (e.g. 335e6 for US).
        prevalence:        fraction of population with the disease (e.g. 1/2000).
        diagnosed_frac:    fraction of prevalent that is clinically diagnosed.
        eligible_frac:     fraction of diagnosed eligible for the therapy (SAM).
        mature_som_frac:   realistic serviceable-obtainable share of SAM at maturity.
        chronic_annual_price: annual price of the chronic-therapy comparator (for TAM $).
        one_course_price:  price of the one-course/durable therapy (for SOM revenue $).
        basis:             optional dict of per-layer source strings for the table.

    Returns dict with patient counts, dollar figures, and a markdown table.
    """
    basis = basis or {}
    prevalent = population * prevalence
    diagnosed = prevalent * diagnosed_frac
    sam = diagnosed * eligible_frac
    som = sam * mature_som_frac

    out = {
        "population": population,
        "prevalent": prevalent,
        "diagnosed": diagnosed,
        "sam_eligible": sam,
        "som_annual": som,
        "prevalence": prevalence,
        "diagnosed_frac": diagnosed_frac,
        "eligible_frac": eligible_frac,
        "mature_som_frac": mature_som_frac,
    }

    tam_dollars = som_rev = None
    if chronic_annual_price is not None:
        tam_dollars = sam * chronic_annual_price   # if whole eligible pool treated at comparator price
        out["tam_annual_dollars"] = tam_dollars
    if one_course_price is not None:
        som_rev = som * one_course_price
        out["som_annual_revenue"] = som_rev

    rows = [
        ("Prevalence", f"{prevalence:.2%} of population", fmt_int(prevalent),
         basis.get("prevalent", f"{prevalence:.4g} x {fmt_int(population)} pop")),
        ("Diagnosed", f"{diagnosed_frac:.0%} of prevalent", fmt_int(diagnosed),
         basis.get("diagnosed", f"{diagnosed_frac:.0%} clinically diagnosed")),
        ("SAM — eligible", f"{eligible_frac:.0%} of diagnosed", fmt_int(sam),
         basis.get("sam", f"{eligible_frac:.0%} therapy-eligible")),
        ("SOM (mature, annual)", f"{mature_som_frac:.0%} of SAM", fmt_int(som),
         basis.get("som", f"{mature_som_frac:.0%} of SAM at maturity")),
    ]
    md = ["| Layer | Definition | Patients | Basis |", "|---|---|---|---|"]
    for layer, defn, pts, bas in rows:
        md.append(f"| **{layer}** | {defn} | **{pts}** | {bas} |")
    lines = []
    if tam_dollars is not None:
        lines.append(f"- **TAM ~ {fmt_money(tam_dollars)}/yr** if the eligible pool "
                     f"were treated at {fmt_money(chronic_annual_price)}/yr comparator pricing.")
    if som_rev is not None:
        lines.append(f"- **SOM revenue ~ {fmt_money(som_rev)}/yr** at maturity, "
                     f"at a one-course price of {fmt_money(one_course_price)} on "
                     f"~{fmt_int(som)} patients/yr.")
    out["table_md"] = "\n".join(md) + ("\n\n" + "\n".join(lines) if lines else "")
    return out


def value_based_price(chronic_annual_price, one_course_price, horizon_years=10,
                      discount_rate=0.0):
    """Frame a one-course/durable therapy against the lifetime cost it displaces.

    Computes payback period (years of avoided chronic therapy to recoup the
    one-course price) and cumulative payer savings over a horizon.

    Returns dict with payback_years, cumulative_savings, and a per-year schedule.
    """
    if chronic_annual_price <= 0:
        raise ValueError("chronic_annual_price must be > 0")
    payback = one_course_price / chronic_annual_price
    schedule, cum_chronic = [], 0.0
    for yr in range(1, horizon_years + 1):
        disc = (1 + discount_rate) ** yr if discount_rate else 1.0
        cum_chronic += chronic_annual_price / disc
        savings = cum_chronic - one_course_price
        schedule.append({"year": yr,
                         "cum_chronic_cost": cum_chronic,
                         "one_course_cost": one_course_price,
                         "cumulative_savings": savings})
    return {
        "payback_years": payback,
        "cumulative_savings": schedule[-1]["cumulative_savings"],
        "horizon_years": horizon_years,
        "schedule": schedule,
        "summary": (f"One course at {fmt_money(one_course_price)} pays back in "
                    f"~{payback:.1f} yr vs {fmt_money(chronic_annual_price)}/yr chronic; "
                    f"saves ~{fmt_money(schedule[-1]['cumulative_savings'])}/patient "
                    f"by year {horizon_years}."),
    }


def example_survey_items():
    """Minimal illustrative item schema for generate_form_script."""
    return [
        {"section": "Disease & treatment burden"},
        {"type": "scale", "title": "In the past month, how often did swallowing "
         "difficulty affect what or how you ate?", "low": 1, "high": 5,
         "low_label": "Never", "high_label": "Every day"},
        {"type": "mc", "title": "Which outcome matters most to you personally?",
         "choices": ["Fewer symptoms", "Eat previously avoided foods",
                     "Fewer procedures", "Reduced medication", "Normal biopsy"]},
        {"type": "checkbox", "title": "Which treatments have you tried?",
         "choices": ["Elimination diet", "Topical steroids", "Biologic injection",
                     "Dilation procedure", "Other"]},
        {"type": "scale", "title": "How concerned would you be about a treatment "
         "derived from your trigger foods causing an allergic reaction?",
         "low": 1, "high": 5, "low_label": "Not at all", "high_label": "Extremely"},
        {"type": "paragraph", "title": "In your own words, what does living with "
         "this condition cost you day to day? (optional)", "required": False},
    ]


def generate_form_script(title, description="", items=None,
                         collect_email=False, limit_one_response=False,
                         progress_bar=True):
    """Emit a Google Apps Script (.gs) that builds an anonymous Google Form.

    Defaults are privacy-first: email collection OFF, one-response-per-user OFF
    (no forced sign-in), progress bar ON. Paste the output into
    script.google.com -> New project -> Run, approve the permission prompt, and
    copy the LIVE FORM url from the execution log.

    items: list of dicts. Supported shapes:
        {"section": "Heading"}                              -> page/section header
        {"type": "text",      "title", "required"?}         -> short answer
        {"type": "paragraph", "title", "required"?}         -> long answer
        {"type": "mc",        "title", "choices":[...], "required"?}  -> single choice
        {"type": "checkbox",  "title", "choices":[...], "required"?} -> multi select
        {"type": "scale",     "title", "low", "high", "low_label", "high_label", "required"?}
      If items is None, a small illustrative schema is used.

    Returns the .gs source as a string.
    """
    import json as _json
    if items is None:
        items = example_survey_items()

    def esc(s):
        return _json.dumps("" if s is None else str(s))

    body = []
    for it in items:
        if "section" in it:
            body.append(f"  form.addSectionHeaderItem().setTitle({esc(it['section'])});")
            continue
        t = it.get("type", "text")
        req = "true" if it.get("required", t != "paragraph") else "false"
        title_ = esc(it.get("title", ""))
        if t == "text":
            body.append(f"  form.addTextItem().setTitle({title_}).setRequired({req});")
        elif t == "paragraph":
            body.append(f"  form.addParagraphTextItem().setTitle({title_}).setRequired({req});")
        elif t in ("mc", "choice"):
            ch = ", ".join(esc(c) for c in it.get("choices", []))
            body.append(f"  form.addMultipleChoiceItem().setTitle({title_})"
                        f".setChoiceValues([{ch}]).setRequired({req});")
        elif t == "checkbox":
            ch = ", ".join(esc(c) for c in it.get("choices", []))
            body.append(f"  form.addCheckboxItem().setTitle({title_})"
                        f".setChoiceValues([{ch}]).setRequired({req});")
        elif t == "scale":
            lo, hi = int(it.get("low", 1)), int(it.get("high", 5))
            ll, hl = esc(it.get("low_label", "")), esc(it.get("high_label", ""))
            body.append(f"  form.addScaleItem().setTitle({title_})"
                        f".setBounds({lo}, {hi}).setLabels({ll}, {hl}).setRequired({req});")
        else:
            body.append(f"  form.addTextItem().setTitle({title_}).setRequired({req});")

    gs = f"""/**
 * Auto-generated by the patient-centered-market-and-survey skill.
 * Build an anonymous Google Form. In script.google.com: New project ->
 * paste this -> Save -> Run buildForm -> approve prompt -> copy the LIVE
 * FORM url printed in the Execution log.
 */
function buildForm() {{
  var form = FormApp.create({esc(title)});
  form.setDescription({esc(description)});
  form.setCollectEmail({str(collect_email).lower()});
  form.setLimitOneResponsePerUser({str(limit_one_response).lower()});
  form.setProgressBar({str(progress_bar).lower()});
  form.setAllowResponseEdits(false);

{chr(10).join(body)}

  Logger.log('LIVE FORM: ' + form.getPublishedUrl());
  Logger.log('EDIT: ' + form.getEditUrl());
}}
"""
    return gs
