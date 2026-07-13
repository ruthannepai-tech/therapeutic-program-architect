"""Kernel helpers for the synthetic-peer-review skill.

Loaded automatically when the skill is loaded. Main entry point:
    run_peer_review_panel(host, manuscripts, personas=None, shared_frame=None, ...)
"""
import re
from datetime import datetime

# ---- Default persona triad (comp-bio therapeutics; swap per field) ----
DEFAULT_PERSONAS = {
    1: ("Domain clinician-scientist lens. Scrutinize biological plausibility, "
        "clinical framing, biomarker/companion-diagnostic real-world utility, and "
        "whether clinical claims are appropriately hedged. Push hard where disease "
        "reasoning is thin or an in-silico signal is over-confident."),
    2: ("Computational biologist & biostatistician lens. Scrutinize statistical "
        "rigor: multiple-testing control, single-cohort claims, cohort independence/"
        "circularity, enrichment tests, prediction-tool validity/concordance, "
        "unit-of-analysis / pseudoreplication, and reproducibility. Demand methods "
        "detail and appropriate uncertainty."),
    3: ("Methodology & research-ethics lens. Scrutinize over-claiming on autonomy/"
        "novelty, whether curated exhibits have a denominator or are cherry-picked, "
        "equity of any proposed design, AI-disclosure norms, and adequacy of "
        "limitations/caveats. Judge whether headline claims match the evidence."),
}

REVIEW_STRUCTURE = """Produce your review in this exact structure, in markdown:
### Reviewer {N}: {your one-line identity & expertise}
For EACH manuscript separately:
- **Brief summary** (2-3 sentences, your own words, showing you read it)
- **Strengths** (bullets)
- **Major concerns** (numbered; must-fix for soundness)
- **Minor concerns** (numbered; clarity/presentation)
- **Feasible revisions** (numbered; each achievable within the stated scope — no out-of-scope asks)
- **Recommendation** (Accept / Minor revision / Major revision / Reject) + one-sentence justification, appropriate to the manuscript's venue.
End with **Cross-cutting comment** (2-4 sentences on the set as a whole).
Be concrete: cite specific claims, numbers, figures, sections. Depth of a real journal review."""


def build_shared_frame(work_description, in_scope, out_of_scope, manuscript_blurbs):
    """Assemble the framing brief every reviewer receives.

    work_description: what the work is (1-3 sentences).
    in_scope / out_of_scope: strings naming what revisions are / are not allowed.
    manuscript_blurbs: list of "PAPER X (venue): title — one line" strings.
    """
    mans = "\n".join(f"- {b}" for b in manuscript_blurbs)
    return f"""You are serving as an expert peer reviewer for the following manuscript(s).

CRITICAL FRAMING — read before reviewing:
- {work_description}
- IN SCOPE for revision: {in_scope}
- OUT OF SCOPE: {out_of_scope}. Do NOT make your recommendation contingent on out-of-scope work; every revision you request must be achievable within the in-scope set (more analysis, statistical robustness, clarification, tempered claims, better caveats, restructuring).
- Be genuinely critical and skeptical — a rigorous reviewer, not a cheerleader — while fair and specific. Reward honesty about limitations; penalize over-claiming, unsupported causal language, weak statistics, and scope inflation.

The manuscript(s):
{mans}

{REVIEW_STRUCTURE}"""


def persona_system(shared_frame, n, persona_text):
    return (shared_frame.replace("{N}", str(n))
            + f"\n\nYOUR REVIEWER PERSONA (Reviewer {n}):\n{persona_text}")


def run_peer_review_panel(host, manuscripts, shared_frame, personas=None,
                          max_tokens=8000, editor_max_tokens=5000,
                          write_report=True, report_title="Mock Peer-Review Report"):
    """Run the full synthetic peer-review flow.

    manuscripts: list of (label, text) tuples, e.g. [("PAPER D (Perspective)", md_str), ...].
    shared_frame: the framing brief (use build_shared_frame()).
    personas: dict {1: text, 2: text, ...}; defaults to DEFAULT_PERSONAS.
    Returns {reviews, editor, recommendations}.
    """
    personas = personas or DEFAULT_PERSONAS
    model = host.reasoning_model()
    corpus = "\n\n".join(f"===== {lbl} =====\n{txt}" for lbl, txt in manuscripts)
    prompt = f"{corpus}\n\nWrite your complete peer review now."

    reqs = [{"system": persona_system(shared_frame, n, personas[n]),
             "prompt": prompt, "max_tokens": max_tokens, "model": model}
            for n in sorted(personas)]
    out = host.llm(reqs, max_concurrency=len(reqs))
    reviews = []
    for n, r in zip(sorted(personas), out):
        txt = r.get("text", "")
        if r.get("stop_reason") == "max_tokens":  # retry once with bigger budget
            r2 = host.llm({"system": persona_system(shared_frame, n, personas[n]),
                           "prompt": prompt, "max_tokens": int(max_tokens * 1.6),
                           "model": model})
            txt = r2.get("text", txt)
        reviews.append(txt)

    recs = [re.findall(r"Recommendation[:\*\s]*\**\s*(Accept|Minor revision|Major revision|Reject)", rv, re.I)
            for rv in reviews]

    joined = "\n\n".join(f"===== REVIEWER {i+1} =====\n{rv}" for i, rv in enumerate(reviews))
    ed_system = shared_frame + """

You are now the HANDLING EDITOR, not a reviewer. With the completed reviews in hand, write an editor's decision letter that:
1. Opens with a 2-3 sentence overview of the submission.
2. States a DECISION PER MANUSCRIPT (Accept / Minor revision / Major revision / Reject), consistent with the balance of reviews.
3. Synthesizes CONVERGENT major concerns (raised by >=2 reviewers) into a prioritized, numbered 'Essential revisions' list PER MANUSCRIPT — each achievable within the stated scope, naming which reviewers raised it.
4. Notes substantive DISAGREEMENTS and how the authors should adjudicate.
5. Gives a short 'Path to acceptance' paragraph per manuscript.
Be decisive and specific. Markdown with clear headers."""
    editor = host.llm({"system": ed_system,
                       "prompt": f"Here are the reviews. Write your editor's decision letter.\n\n{joined}",
                       "max_tokens": editor_max_tokens, "model": model}).get("text", "")

    if write_report:
        write_peer_review_report(host, manuscripts, personas, reviews, editor, report_title)
    return {"reviews": reviews, "editor": editor, "recommendations": recs}


def write_peer_review_report(host, manuscripts, personas, reviews, editor, title):
    blurbs = "\n".join(f"- **{lbl}**" for lbl, _ in manuscripts)
    persona_lines = "\n".join(f"- **Reviewer {n}** — {personas[n].split('.')[0]}"
                              for n in sorted(personas))
    full = "\n\n".join(
        f"===== REVIEWER {i+1} =====\n{rv}" for i, rv in enumerate(reviews))
    full = re.sub(r"===== REVIEWER (\d+) =====", r"## Reviewer \1", full)
    report = f"""# {title}

**Manuscripts assessed:**
{blurbs}

**Review model:** {len(personas)} independent expert reviewers + handling-editor synthesis. Reviewers were briefed on the manuscript framing and scope; every requested revision is achievable within that scope.

**Panel:**
{persona_lines}

*Generated {datetime.utcnow().strftime('%Y-%m-%d')} · reviews produced by independent model instances under distinct expert personas. Advisory only — verify any specific factual claim before acting on it.*

---

## Editor's Decision Letter

{editor}

---

## Full Reviews

{full}
"""
    with open("peer_review_report.md", "w") as f:
        f.write(report)
    # DOCX: reuse agentic-campaign-manuscript helpers if present, else pypandoc
    try:
        render_manuscript_docx("peer_review_report.md", "peer_review_report.docx", title=title)  # noqa: F821
    except Exception:
        try:
            import pypandoc
            pypandoc.convert_file("peer_review_report.md", "docx",
                                  outputfile="peer_review_report.docx")
        except Exception:
            pass
    return report
