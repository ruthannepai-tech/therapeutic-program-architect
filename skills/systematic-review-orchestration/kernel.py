"""Helpers for the systematic-review orchestration skill.

Pure-compute utilities that sit on top of the base literature-review skill's
retrieval/verification primitives (search_openalex, expand_citations,
verify_dois, crossref_lookup). These handle the ORCHESTRATION layer: DOI
normalization + dedup, evidence tiering, and the relevance-screen prompt
builder. Retrieval and MCP calls (PubMed, ClinicalTrials.gov) stay in SKILL.md
because connector calls only run in the repl tool.
"""

TIER_VENUE_HINTS = {
    "Tier-1": ["n engl j med", "nejm", "lancet", "nature", "nature genetics",
               "nature immunology", "nature medicine", "science", "cell",
               "immunity", "gastroenterology", "j allergy clin immunol",
               "journal of allergy and clinical immunology"],
}


def normalize_doi(doi):
    """Lowercase, strip URL prefixes and whitespace for dedup keying."""
    if not doi:
        return None
    d = str(doi).strip().lower()
    for pre in ("https://doi.org/", "http://doi.org/", "doi:", "https://dx.doi.org/"):
        if d.startswith(pre):
            d = d[len(pre):]
    return d.strip() or None


def dedup_by_doi(records, doi_key="doi", prefer_keys=("abstract",)):
    """Collapse records to one-per-normalized-DOI, merging source provenance.

    records: list of dicts. Keeps the entry with the most non-empty prefer_keys
    (e.g. prefers a record that carries an abstract). Adds 'source_dbs' listing
    which source tags contributed, and 'n_sources'.
    """
    by = {}
    for r in records:
        nd = normalize_doi(r.get(doi_key))
        if not nd:
            continue
        src = r.get("source_db") or r.get("source") or "?"
        if nd not in by:
            r2 = dict(r); r2["doi"] = nd
            r2["_srcs"] = {src}
            by[nd] = r2
        else:
            cur = by[nd]
            cur["_srcs"].add(src)
            score_new = sum(1 for k in prefer_keys if r.get(k))
            score_cur = sum(1 for k in prefer_keys if cur.get(k))
            if score_new > score_cur:
                merged_srcs = cur["_srcs"]
                cur = dict(r); cur["doi"] = nd; cur["_srcs"] = merged_srcs
                by[nd] = cur
    out = []
    for nd, r in by.items():
        srcs = sorted(r.pop("_srcs"))
        r["source_dbs"] = "|".join(srcs)
        r["n_sources"] = len(srcs)
        out.append(r)
    return out


def assign_tier(record, topic_terms, cite_key="cited_by", venue_key="venue",
                title_key="title"):
    """Assign Tier-1/2/3 with a TOPICAL-SPECIFICITY guardrail.

    A high citation count alone does NOT earn Tier-1 — the record must also be
    ON-TOPIC (title contains a topic term). This stops generic high-citation
    reviews (NF-kB, IL-6, microbiota) from polluting Tier-1. topic_terms: list
    of lowercase disease/mechanism keywords that define on-topic-ness.
    """
    title = str(record.get(title_key, "")).lower()
    venue = str(record.get(venue_key, "")).lower()
    try:
        cites = float(record.get(cite_key) or 0)
    except (TypeError, ValueError):
        cites = 0.0
    on_topic = any(t in title for t in topic_terms)
    landmark_venue = any(h in venue for h in TIER_VENUE_HINTS["Tier-1"])
    if on_topic and (cites >= 300 or landmark_venue):
        return "Tier-1"
    if on_topic or cites >= 50:
        return "Tier-2"
    return "Tier-3"


def build_screen_prompt(record, disease, title_key="title", abs_key="abstract"):
    """Build a relevance-screen prompt for one record (for host.llm fan-out).

    Returns a string asking a yes/no relevance judgment. Use in a host.llm list
    fan-out over the ambiguous ('check') records; parse the leading token.
    """
    title = record.get(title_key, "")
    abstract = (record.get(abs_key) or "")[:1200]
    return (
        "You are screening a reference for a systematic review of " + disease + ".\n"
        "Answer with exactly RELEVANT or SKIP on the first line, then a short reason.\n"
        "RELEVANT = the paper is about " + disease + ", its mechanisms, diagnosis, "
        "treatment, genetics, epidemiology, or a directly-transferable method/precedent.\n"
        "SKIP = keyword false-positive (the term appears incidentally; the paper is "
        "about something else).\n\n"
        "TITLE: " + str(title) + "\n"
        "ABSTRACT: " + str(abstract) + "\n"
    )
