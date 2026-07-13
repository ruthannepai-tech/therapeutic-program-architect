"""Helpers for preparing/updating the agentic-campaign manuscript (Paper D).

All functions are pure-ish utilities the agent calls from a python cell after
`skill({skill:"agentic-campaign-manuscript"})`. Third-party imports are deferred
into function bodies per the sidecar rules.
"""

MANUSCRIPT_MD = "paperD_nature_perspective.md"
DOCX_SOURCE = "paperD_docx_source.md"
DOCX_OUT = "paperD_nature_perspective.docx"

# CrossRef base; contact email is passed by the caller (never hardcode one).
CROSSREF = "https://api.crossref.org/works/"


def compute_campaign_metrics(host, project_id, exclude_frame_id=None):
    """Recompute verified campaign metrics from the artifact store.

    Returns a dict with active-compute span (hours, from artifact-version
    timestamps), total latest-version deliverable count, and a content-type
    breakdown that SUMS to the total (the itemization rule). Pass
    exclude_frame_id to drop the current manuscript session so counts are
    stable across re-runs. `host` is the kernel host object.
    """
    from collections import Counter
    res = host.artifacts(project_id=project_id, limit=1000,
                         include_intermediate=False)
    arts = res["artifacts"]
    if exclude_frame_id:
        arts = [a for a in arts if a.get("root_frame_id") != exclude_frame_id]
    ct = Counter(a["content_type"] for a in arts)
    total = len(arts)
    named = {
        "figures (png)": ct.get("image/png", 0),
        "tables (csv)": ct.get("text/csv", 0),
        "reports (md)": ct.get("text/markdown", 0),
        "structures (pdb)": ct.get("chemical/x-pdb", 0),
    }
    other = total - sum(named.values())
    if other:
        named["other"] = other
    assert sum(named.values()) == total, "breakdown must reconcile to total"
    return {"total_deliverables": total, "breakdown": named}


def compute_active_span_hours(host, project_id, exclude_frame_id=None):
    """Active-compute span in hours from artifact-version timestamps.

    This is the MEASURED span, distinct from the calendar/hackathon window —
    keep the two labeled separately in the manuscript.
    """
    res = host.artifacts(project_id=project_id, limit=1000,
                         include_intermediate=True)
    ts = []
    for a in res["artifacts"]:
        if exclude_frame_id and a.get("root_frame_id") == exclude_frame_id:
            continue
        t = a.get("created_at")
        if isinstance(t, (int, float)):
            ts.append(t)
    if not ts:
        return None
    span_ms = max(ts) - min(ts)
    # created_at may be epoch-ms (int) — normalize to hours
    return round(span_ms / 1000 / 3600, 1)


def verify_dois(dois, email=None):
    """Verify DOIs against CrossRef; return {doi: {first,year,journal,title,
    volume,page}} for those that resolve, and mark failures with 'status'.

    NEVER cite a DOI that does not resolve here. `email` (from
    host.get_user_email()) is passed as CrossRef's polite mailto when present.
    """
    import time
    import html
    import requests
    out = {}
    params = {"mailto": email} if email else {}
    for d in dois:
        try:
            r = requests.get(CROSSREF + d, params=params, timeout=20)
            if r.status_code == 200:
                m = r.json()["message"]
                auth = m.get("author", [])
                out[d] = {
                    "first": (auth[0].get("family", "") if auth else ""),
                    "n_auth": len(auth),
                    "year": (m.get("issued", {}).get("date-parts", [[None]])[0][0]),
                    "journal": html.unescape((m.get("container-title") or [""])[0]),
                    "title": html.unescape((m.get("title") or [""])[0]),
                    "volume": m.get("volume"),
                    "page": m.get("page"),
                }
            else:
                out[d] = {"status": r.status_code}
        except Exception as e:
            out[d] = {"err": str(e)[:80]}
        time.sleep(0.15)
    return out


def resolve_markers_to_paths(host, md_in, md_out):
    """Rewrite {{artifact:art_<ID>}} document markers to real local image
    paths (for pandoc, which cannot interpret markers), and convert
    'Display items' bullets of the form '- **Figure N** — cap (path)' into
    inline image embeds. Returns (n_images, n_unresolved).
    """
    import re
    res = host.artifacts(limit=1000)
    id2path = {a["id"]: host.artifact_path(a["latest_version_id"])
               for a in res["artifacts"]}
    md = open(md_in).read()

    def repl(m):
        return id2path.get(m.group(1), m.group(0))

    md = re.sub(r"\{\{artifact:art_([0-9a-f\-]+)\}\}", repl, md)
    lines, out = md.splitlines(), []
    pat = re.compile(r"- \*\*(Figure \d|Table \d)\*\* — (.+?) \((/.+?\.png)\)")
    for l in lines:
        m = pat.match(l)
        if m:
            label, cap, path = m.groups()
            out.append("![**%s.** %s](%s)\n" % (label, cap, path))
        else:
            out.append(l)
    md = "\n".join(out)
    open(md_out, "w").write(md)
    n_img = len(re.findall(r"!\[.*?\]\(/.*?\.png\)", md))
    n_unres = len(re.findall(r"\{\{artifact", md))
    return n_img, n_unres


def render_manuscript_docx(md_source, docx_out, title="Manuscript"):
    """Render a marker-resolved markdown source to DOCX via pypandoc.

    Requires pypandoc-binary. Returns the output path. Run
    resolve_markers_to_paths() FIRST so images embed.
    """
    import os
    import pypandoc
    pypandoc.convert_file(
        md_source, "docx", outputfile=docx_out,
        extra_args=["--standalone", "--resource-path=.",
                    "--metadata=title:" + title])
    assert os.path.exists(docx_out) and os.path.getsize(docx_out) > 0
    return docx_out


def verify_docx(docx_path, must_contain=None):
    """Sanity-check a rendered DOCX: count embedded images/drawings and
    confirm key strings survived. Returns a dict of checks. `must_contain`
    is a list of substrings expected in the document body.
    """
    import zipfile
    z = zipfile.ZipFile(docx_path)
    media = [n for n in z.namelist() if n.startswith("word/media/")]
    doc = z.read("word/document.xml").decode("utf-8", "ignore")
    checks = {"embedded_images": len(media),
              "drawings": doc.count("<w:drawing>")}
    for s in (must_contain or []):
        checks["has:" + s[:24]] = (s in doc)
    return checks
