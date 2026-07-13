"""Helpers for the antigen-epitope / pMHC pipeline skill.

Pure-compute utilities for the disease-agnostic epitope-mapping workflow:
antigen sequence -> peptide windows -> (external MHC prediction) -> per-HLA
burden. The MHC prediction step itself is env-specific (netMHCIIpan via IEDB,
or mhcnuggets in a TF env) and lives in SKILL.md, not here.
"""

STRONG_IC50_NM = 500.0        # class-II strong-binder threshold (nM)
DEFAULT_CLASSII_K = 15        # class-II core-containing peptide length
DEFAULT_CLASSI_K = 9          # class-I peptide length


def fetch_uniprot_fasta(accession, timeout=30):
    """Fetch a UniProt sequence by accession. Returns (header, sequence)."""
    import requests
    url = "https://rest.uniprot.org/uniprotkb/" + accession + ".fasta"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    header = lines[0].lstrip(">") if lines else accession
    seq = "".join(l.strip() for l in lines[1:])
    return header, seq


def sliding_windows(seq, k=None, step=1):
    """All length-k peptide windows over a sequence.

    Returns list of (start_1based, peptide). k defaults to class-II 15-mer.
    """
    if k is None:
        k = DEFAULT_CLASSII_K
    seq = "".join(seq.split())
    out = []
    for i in range(0, len(seq) - k + 1, step):
        out.append((i + 1, seq[i:i + k]))
    return out


def summarize_binders(rows, allele_key="allele", antigen_key="antigen",
                      ic50_key="ic50", threshold=None):
    """Aggregate a flat list of prediction dicts into strong-binder counts.

    rows: iterable of dicts with allele/antigen/ic50 fields.
    Returns dict with per_allele, per_antigen, per_allele_antigen counts and
    the total number of strong binders (ic50 < threshold).
    """
    if threshold is None:
        threshold = STRONG_IC50_NM
    per_allele = {}
    per_antigen = {}
    per_pair = {}
    total = 0
    for row in rows:
        try:
            ic50 = float(row.get(ic50_key))
        except (TypeError, ValueError):
            continue
        if ic50 >= threshold:
            continue
        total += 1
        al = row.get(allele_key, "NA")
        ag = row.get(antigen_key, "NA")
        per_allele[al] = per_allele.get(al, 0) + 1
        per_antigen[ag] = per_antigen.get(ag, 0) + 1
        key = al + "|" + ag
        per_pair[key] = per_pair.get(key, 0) + 1
    return {"total_strong": total, "per_allele": per_allele,
            "per_antigen": per_antigen, "per_allele_antigen": per_pair,
            "threshold_nM": threshold}


def unique_core_count(rows, core_key="core", ic50_key="ic50", threshold=None):
    """Count distinct strong-binding cores (dedups shared cores across alleles).

    Guards against the common double-count bug where per-cell sums inflate the
    true number of unique binding cores.
    """
    if threshold is None:
        threshold = STRONG_IC50_NM
    cores = set()
    for row in rows:
        try:
            ic50 = float(row.get(ic50_key))
        except (TypeError, ValueError):
            continue
        if ic50 < threshold and row.get(core_key):
            cores.add(row[core_key])
    return len(cores)


# --- TG2 deamidation model (celiac and other deamidation-driven diseases) -----

def tg2_deamidation_sites(seq):
    """0-based indices of Gln (Q) that TG2 deamidates, under the QXP rule.

    Consensus (Fleckenstein/Vader/Dorum): TG2 targets Q in a Q-X-Pro motif
    (proline at +2), but a Q immediately followed by proline (+1) is NOT a
    substrate. Recovers ~77% of experimentally annotated celiac sites.
    """
    seq = "".join(seq.split())
    sites = []
    n = len(seq)
    for i, aa in enumerate(seq):
        if aa != "Q":
            continue
        if i + 2 < n and seq[i + 2] == "P" and seq[i + 1] != "P":
            sites.append(i)
    return sites


def deamidate(seq):
    """Return the TG2-deamidated sequence (Q->E at QXP sites)."""
    seq = "".join(seq.split())
    chars = list(seq)
    for i in tg2_deamidation_sites(seq):
        chars[i] = "E"
    return "".join(chars)


def deamidation_windows(seq, k=None):
    """Paired native/deamidated peptide windows over a sequence.

    Returns list of (start_1based, native_window, deamidated_window, n_edits).
    Feed both forms to the MHC predictor to measure the deamidation shift.
    """
    if k is None:
        k = DEFAULT_CLASSII_K
    seq = "".join(seq.split())
    dseq = deamidate(seq)
    out = []
    for i in range(0, len(seq) - k + 1):
        nat = seq[i:i + k]
        dea = dseq[i:i + k]
        out.append((i + 1, nat, dea,
                    sum(1 for a, b in zip(nat, dea) if a != b)))
    return out


# --- Benchmark predictions against a known-epitope ground truth --------------

def best_ic50_for_core(rows, known_core, allele=None, allele_key="allele",
                       peptide_key="peptide", ic50_key="ic50"):
    """Lowest predicted IC50 among windows whose peptide contains known_core.

    Optionally restrict to one allele. Returns None if the core is not found.
    Use the DEAMIDATED-form predictions and the deamidated known core.
    """
    best = None
    for row in rows:
        if allele is not None and row.get(allele_key) != allele:
            continue
        if known_core in (row.get(peptide_key) or ""):
            try:
                ic50 = float(row.get(ic50_key))
            except (TypeError, ValueError):
                continue
            if best is None or ic50 < best:
                best = ic50
    return best


def benchmark_known_epitopes(rows, known, threshold=None, allele_key="allele",
                             peptide_key="peptide", ic50_key="ic50"):
    """Benchmark deamidated-form predictions against mapped known epitopes.

    rows : flat list of DEAMIDATED prediction dicts {allele, peptide, ic50, ...}.
    known: list of dicts, each {core, restricting_allele, name?, immunodominant?}
           where `core` is the TG2-DEAMIDATED epitope core.

    Returns a dict with:
      recall_at_threshold  - fraction of located epitopes with best IC50 < thr
      per_epitope          - list of {name, restricting_allele, best_ic50,
                             pct_rank_in_allele, recovered, allele_preferred}
      allele_preference    - correct / located: best IC50 on the restricting
                             allele lower than on every other allele
    NOTE (calibration): netMHCIIpan under-scores HLA-DQ; canonical celiac
    epitopes score in the 'weak' IC50 range. Trust `pct_rank_in_allele` and
    `allele_preference`, NOT `recall_at_threshold`, when interpreting DQ.
    """
    if threshold is None:
        threshold = STRONG_IC50_NM
    # pre-sort IC50 per allele for percentile ranks
    by_allele = {}
    for row in rows:
        try:
            ic50 = float(row.get(ic50_key))
        except (TypeError, ValueError):
            continue
        by_allele.setdefault(row.get(allele_key), []).append(ic50)
    for al in by_allele:
        by_allele[al].sort()
    alleles = list(by_allele.keys())

    def pct_rank(al, ic50):
        arr = by_allele.get(al) or []
        if not arr:
            return None
        import bisect
        return bisect.bisect_right(arr, ic50) / len(arr)

    per = []
    located = 0
    recovered = 0
    pref_correct = 0
    pref_total = 0
    for e in known:
        rest = e.get("restricting_allele")
        core = e.get("core")
        best = best_ic50_for_core(rows, core, allele=rest, allele_key=allele_key,
                                  peptide_key=peptide_key, ic50_key=ic50_key)
        rec = {"name": e.get("name"), "restricting_allele": rest,
               "immunodominant": e.get("immunodominant"),
               "best_ic50": best,
               "pct_rank_in_allele": pct_rank(rest, best) if best is not None else None,
               "recovered": (best is not None and best < threshold)}
        if best is not None:
            located += 1
            if best < threshold:
                recovered += 1
            others = [best_ic50_for_core(rows, core, allele=a, allele_key=allele_key,
                                         peptide_key=peptide_key, ic50_key=ic50_key)
                      for a in alleles if a != rest]
            others = [o for o in others if o is not None]
            if others:
                pref_total += 1
                pref = best < min(others)
                rec["allele_preferred"] = pref
                if pref:
                    pref_correct += 1
        per.append(rec)
    return {"n_known": len(known), "n_located": located,
            "recall_at_threshold": (recovered / located) if located else None,
            "threshold_nM": threshold,
            "allele_preference": {"correct": pref_correct, "located": pref_total,
                                  "fraction": (pref_correct / pref_total) if pref_total else None},
            "per_epitope": per}
