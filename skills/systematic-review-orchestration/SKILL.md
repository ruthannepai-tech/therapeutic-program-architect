---
name: systematic-review-orchestration
description: Orchestrate an exhaustive, multi-database systematic literature review — taxonomy to tiered reference library to synthesis. Use when the ask is a comprehensive/exhaustive review of a disease or topic (not a single "what's the seminal paper" lookup). Layers on the base literature-review skill: query-matrix design, multi-DB retrieval (PubMed + OpenAlex + citation-graph), DOI dedup, LLM relevance screen, Tier-1/2/3 evidence rubric with topical-specificity guardrail, and the evidence-map figure. Disease-agnostic via a swappable taxonomy.
---

# Systematic-review orchestration

An orchestration layer for building **exhaustive, multi-database, tiered**
literature reviews. It does NOT replace the base `literature-review` skill —
load that FIRST for the retrieval/verification primitives (`search_openalex`,
`expand_citations`, `verify_dois`, `crossref_lookup`, `style_pass`). This skill
adds the pipeline that turns those primitives into a systematic review.

`kernel.py` ships the pure-compute helpers (`normalize_doi`, `dedup_by_doi`,
`assign_tier`, `build_screen_prompt`). Retrieval/MCP steps are in the workflow
below (connector calls run only in the repl tool).

## When to use
- "Most exhaustive review of X", "comprehensive review of the literature on Y",
  multi-part reviews. NOT for a single-anchor lookup (base skill handles those).

## Workflow

### 1. Taxonomy -> query matrix
Decompose the topic into parts -> subtopics -> text queries. Save a
`review_scope.json` (parts, subtopics, queries). Aim for tens of queries per
part; this is the recall backbone.

### 2. Multi-database retrieval (triangulate)
- **OpenAlex** (base-skill `search_openalex`, needs API key): run every query,
  n~=25. Tag each hit with its part.
- **PubMed** (repl tool, `host.mcp("pubmed","search_articles",...)` -> PMIDs,
  then `get_article_metadata` in batches for abstracts+DOIs). PubMed catches
  papers OpenAlex misses; expect a large complementary set.
- **ClinicalTrials.gov** (repl tool, `host.mcp`) for any therapeutics/pipeline part.
- **bioRxiv/medRxiv:** the connector has NO keyword search (category+date only)
  — rely on OpenAlex preprint indexing instead; note this limitation.
Save raw pulls under `handoff/retrieval_raw/*.json`.

### 3. Dedup -> master library
```python
# python tool
all_recs = openalex_recs + pubmed_recs   # each dict tagged source_db=
lib = dedup_by_doi(all_recs)             # normalized-DOI dedup, merges source_dbs
```
Verify a sample with `verify_dois` (catch retractions). Save
`<topic>_master_reference_library.csv`.

### 4. Citation-graph expansion on landmarks
Pick ~20 genuinely on-topic landmarks (filter out generic high-citation
false-positives FIRST). `expand_citations(doi, n_backward, n_forward)` on each,
then keep only new + on-topic DOIs. This recovers foundational papers the
keyword sweep missed.

### 5. Relevance screen (LLM fan-out)
Rule-based title pass first (clearly-relevant vs clearly-off vs ambiguous).
Screen the ambiguous ones with a parallel `host.llm` fan-out:
```python
prompts = [build_screen_prompt(r, disease="<topic>") for r in ambiguous]
verdicts = host.llm(prompts, max_concurrency=8)   # parse leading RELEVANT/SKIP
```
This is where the $-metered inference is worth spending. Drops keyword
false-positives.

### 6. Evidence tiering (with the guardrail)
```python
topic_terms = ["eosinophil", "esophag", "eoe", ...]   # lowercase on-topic keys
df["tier"] = df.apply(lambda r: assign_tier(r, topic_terms), axis=1)
```
**Guardrail:** `assign_tier` requires ON-TOPIC (title contains a topic term) for
Tier-1 — citation count alone never promotes. Without this, generic high-cite
reviews (NF-kB, IL-6) pollute Tier-1. Always spot-check the Tier-1 roster and
tighten `topic_terms` if off-topic papers appear.

### 7. Synthesis
Write parts as separate markdown docs, each citing ONLY DOIs verified present in
the library (check membership before writing an inline citation; verify
less-familiar DOIs with `verify_dois`). Then `style_pass` each. Build an
**evidence-map figure** (reference volume by part x tier, temporal depth,
claim->evidence-strength gap map) with `figure-style`. Consolidate a master doc
with navigation, cross-cutting synthesis (established/contested/open), and an
honest gap analysis. Bundle everything as tar.gz.

## Honesty rules (non-negotiable)
- **Every cited DOI must be verified** against the library and/or Crossref
  before it goes in prose. No citation from memory.
- **State the ceiling honestly:** open-API + abstract-level synthesis is not a
  full-text-read-of-every-paper review; say so rather than overclaiming
  "exhaustive".
- **Label evidence strength:** established vs emerging vs hypothesis-level.
- **Flag prior art / patents** for any translation-bound topic.
