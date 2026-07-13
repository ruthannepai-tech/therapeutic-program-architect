import numpy as np
import pandas as pd


def moderated_de(expr, labels, case="EoE", control="control", min_frac=0.2, s0=None):
    """Per-gene case-vs-control DE on log2 expression.

    Variance-moderated Welch t-test: adds a prior variance (default = median
    pooled variance across genes) to stabilise low-variance genes, then BH-FDR.

    Parameters
    ----------
    expr : DataFrame  genes x samples, log2-scale.
    labels : Series   index = sample names, values in {case, control}.
    case, control : str  label values to contrast (case - control).
    min_frac : float  keep genes detected (>0) in >= max(3, min_frac*n) samples.
    s0 : float or None  prior variance; None -> median pooled variance.

    Returns DataFrame sorted by padj: gene, log2FC, t, pval, padj.
    """
    from scipy import stats
    from statsmodels.stats.multitest import multipletests

    lab = labels.reindex(expr.columns)
    keep = (expr > 0).sum(axis=1) >= max(3, min_frac * expr.shape[1])
    E = expr[keep]
    ca = E.loc[:, (lab == case).values].astype(float)
    co = E.loc[:, (lab == control).values].astype(float)
    n1, n0 = ca.shape[1], co.shape[1]
    if n1 < 2 or n0 < 2:
        raise ValueError(f"need >=2 samples per group (got case={n1}, control={n0})")
    m1, m0 = ca.mean(1), co.mean(1)
    v1, v0 = ca.var(1, ddof=1), co.var(1, ddof=1)
    s2 = ((n1 - 1) * v1 + (n0 - 1) * v0) / (n1 + n0 - 2)
    if s0 is None:
        s0 = float(np.median(s2.dropna()))
    se = np.sqrt((s2 + s0) * (1 / n1 + 1 / n0))
    lfc = m1 - m0
    t = lfc / se
    dfree = n1 + n0 - 2
    p = 2 * stats.t.sf(np.abs(t), dfree)
    res = pd.DataFrame({"gene": E.index, "log2FC": lfc.values,
                        "t": t.values, "pval": p}).dropna()
    res["padj"] = multipletests(res["pval"], method="fdr_bh")[1]
    return res.sort_values("padj").reset_index(drop=True)


def meta_analysis(fc_df, se_df, min_studies=3):
    """DerSimonian-Laird random-effects meta-analysis across studies.

    fc_df, se_df : DataFrame  genes x studies of per-study log2FC and SE
        (SE typically |log2FC / t| from moderated_de). Aligned by index/columns.

    Returns DataFrame indexed by gene, sorted by padj: pooled_log2FC, se, z,
    pval, padj, Q, I2, k, n_up, n_dn, direction. Only genes present in
    >= min_studies studies are returned.
    """
    from scipy import stats
    from statsmodels.stats.multitest import multipletests

    fc_df = fc_df.copy()
    se_df = se_df.reindex_like(fc_df).replace([np.inf, -np.inf], np.nan)
    rows = []
    for g in fc_df.index:
        yi = fc_df.loc[g].values.astype(float)
        vi = (se_df.loc[g].values.astype(float)) ** 2
        m = np.isfinite(yi) & np.isfinite(vi) & (vi > 0)
        yi, vi = yi[m], vi[m]
        k = len(yi)
        if k < min_studies:
            continue
        wi = 1 / vi
        fe = np.sum(wi * yi) / np.sum(wi)
        Q = np.sum(wi * (yi - fe) ** 2)
        df = k - 1
        C = np.sum(wi) - np.sum(wi ** 2) / np.sum(wi)
        tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
        wr = 1 / (vi + tau2)
        ybar = np.sum(wr * yi) / np.sum(wr)
        se = np.sqrt(1 / np.sum(wr))
        z = ybar / se
        p = 2 * stats.norm.sf(abs(z))
        I2 = max(0.0, (Q - df) / Q) * 100 if Q > 0 else 0.0
        rows.append({"gene": g, "pooled_log2FC": ybar, "se": se, "z": z,
                     "pval": p, "Q": Q, "I2": I2, "k": k,
                     "n_up": int((yi > 0).sum()), "n_dn": int((yi < 0).sum())})
    meta = pd.DataFrame(rows).set_index("gene")
    meta["padj"] = multipletests(meta["pval"], method="fdr_bh")[1]
    meta["direction"] = np.where(meta["pooled_log2FC"] > 0, "up", "down")
    return meta.sort_values("padj")
