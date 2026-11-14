"""E1 (added analysis, see configs/preregistration.md): few-shot recalibration on the target fire.
For each prediction file and target (its test fire, and Eaton): draw a small labelled sample (n houses,
grid-cell 'B' or random 'A'), refit T + conformal thresholds + routing alpha on it, evaluate on the rest of
the target; compare with the Phase 5 baseline (fitted on other fires' calib) on the same remaining houses.
Usage: python src/e1_recalibration.py [budget_seconds]   (resumable: skips files already written)
       python src/e1_recalibration.py summarise
"""
import sys, os, re, glob, time
import numpy as np, pandas as pd
from scipy.special import softmax
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import phase5 as P  # reuse the Phase 5 functions

METH = ["LAC", "APS", "Mondrian", "APS_rand"]
NS = [100, 200, 300]; R = 20; SCHEMES = {"A": 1, "B": 2}
RAW = os.path.join(ROOT, "results", "tables", "e1_raw")


def cell_maps():
    cx = pd.read_csv(os.path.join(ROOT, "data/processed/splits/cells_xbd.csv")).set_index("id").cell
    e = pd.read_csv(os.path.join(ROOT, "data/metadata/buildings_eaton.csv"))
    ce = pd.Series((np.floor(e.lon / 0.005).astype(int).astype(str) + "_" +
                    np.floor(e.lat / 0.005).astype(int).astype(str)).values, index=e.id)
    return pd.concat([cx, ce])


def draw(ids, cells, scheme, n, r):
    """ids: sorted target ids; returns boolean mask (sample) over ids."""
    rng = np.random.default_rng(100000 * SCHEMES[scheme] + 1000 * n + r)
    if scheme == "A":
        m = np.zeros(len(ids), bool); m[rng.choice(len(ids), n, replace=False)] = True; return m
    uc, inv = np.unique(cells, return_inverse=True); cnt = np.bincount(inv)
    order = rng.permutation(len(uc)); take = np.zeros(len(uc), bool); tot = 0
    for c in order:
        take[c] = True; tot += cnt[c]
        if tot >= n: break
    return take[inv]


def route(C, y):
    return P.routing_stats(C, y) if C is not None else {"auto_share": 0.0, "missed_destroyed_rate": 0.0,
                                                           "n_missed": 0, "n_destroyed": int((y == 2).sum())}


def pick(p, y, meth, u):
    ok = P._feasible(p, y, meth, 2, u)
    if not ok: return {"orig": None, "A1": None}
    best = max(r["auto_share"] for _, r in ok)
    return {"orig": ok[-1][0], "A1": [a for a, r in ok if r["auto_share"] == best][-1]}


def run_file(fn, cmap):
    model, k, s = re.search(r"(t\d)_fold(\d)_seed(\d)", fn).groups()
    d = pd.read_csv(fn); z = d[P.LOGIT].to_numpy(np.float64); y = d.label.to_numpy(); role = d.role.to_numpy()
    u_all = np.random.default_rng(0).uniform(size=len(d))  # identical to Phase 5 (P1)
    cal = role == "calib"; T0 = P.fit_T(z[cal], y[cal]); p0 = softmax(z / T0, 1)
    base = {}
    for meth in METH:
        uc = u_all[cal] if meth.endswith("_rand") else None
        al = pick(p0[cal], y[cal], meth, uc)
        base[meth] = {"q": P.thresholds(p0[cal], y[cal], meth, P.ALPHA, uc),
                      **{rule: (a, P.thresholds(p0[cal], y[cal], meth, a, uc) if a is not None else None) for rule, a in al.items()}}
    rows = []
    for tgt in ["test", "eaton"]:
        idx = np.where(role == tgt)[0]; o = np.argsort(d.id.to_numpy()[idx]); idx = idx[o]
        cells = cmap.reindex(d.id.to_numpy()[idx]).to_numpy(); assert pd.notna(cells).all()
        zt, yt, ut, pt0 = z[idx], y[idx], u_all[idx], p0[idx]
        bsets = {}
        for meth in METH:
            uu = ut if meth.endswith("_rand") else None; b = base[meth]
            bsets[meth] = (P.sets(pt0, meth, b["q"], uu),
                           {rule: (P.sets(pt0, meth, b[rule][1], uu) if b[rule][1] is not None else None, b[rule][0]) for rule in ("orig", "A1")})
        for sc in SCHEMES:
            for n in NS:
                for r in range(R):
                    S = draw(idx, cells, sc, n, r)
                    M = ~S; Ts = P.fit_T(zt[S], yt[S]); ps = softmax(zt / Ts, 1)
                    key = {"model": model, "fold": int(k), "seed": int(s), "target": tgt, "scheme": sc, "n": n, "rep": r,
                           "n_sample": int(S.sum()), "n_des_sample": int((yt[S] == 2).sum()), "n_dmg_sample": int((yt[S] == 1).sum()),
                           "n_eval": int(M.sum())}
                    ece_b, ece_r = P.ece(pt0[M], yt[M]), P.ece(ps[M], yt[M])
                    for meth in METH:
                        uu = ut if meth.endswith("_rand") else None; uS = ut[S] if uu is not None else None
                        uM = ut[M] if uu is not None else None
                        # baseline
                        Cb, rb = bsets[meth]
                        row = {**key, "method": meth, "arm": "baseline", "T": T0, "ece": ece_b, **P.set_stats(Cb[M], yt[M])}
                        for rule, (C, a) in rb.items():
                            rs = route(C[M] if C is not None else None, yt[M])
                            row.update({f"alpha_{rule}": a, f"auto_{rule}": rs["auto_share"], f"missed_{rule}": rs["missed_destroyed_rate"]})
                        rows.append(row)
                        # recalibrated on the sample
                        q = P.thresholds(ps[S], yt[S], meth, P.ALPHA, uS)
                        row = {**key, "method": meth, "arm": "recal", "T": Ts, "ece": ece_r, **P.set_stats(P.sets(ps[M], meth, q, uM), yt[M])}
                        al = pick(ps[S], yt[S], meth, uS)
                        for rule, a in al.items():
                            C = P.sets(ps[M], meth, P.thresholds(ps[S], yt[S], meth, a, uS), uM) if a is not None else None
                            rs = route(C, yt[M])
                            row.update({f"alpha_{rule}": a, f"auto_{rule}": rs["auto_share"], f"missed_{rule}": rs["missed_destroyed_rate"]})
                        rows.append(row)
    return pd.DataFrame(rows)


def summarise():
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(RAW, "*.csv")))])
    met = ["coverage", "cov_c0", "cov_c1", "cov_c2", "mean_set_size", "empty_share", "ece",
           "auto_orig", "missed_orig", "auto_A1", "missed_A1", "n_sample", "n_des_sample"]
    # target label: test fire per fold, Eaton pooled over folds
    d["tgt"] = np.where(d.target == "eaton", "eaton", "fold" + d.fold.astype(str))
    # 1) average over seeds (and over fold models for Eaton) within each repeat
    g = d.groupby(["model", "tgt", "scheme", "n", "rep", "method", "arm"])[met].mean().reset_index()
    for rule in ("orig", "A1"): g[f"ok_{rule}"] = (g[f"missed_{rule}"] <= 0.05).astype(float)
    # 2) over repeats: mean, p10, p90
    out = []
    for key, x in g.groupby(["model", "tgt", "scheme", "n", "method", "arm"]):
        row = dict(zip(["model", "tgt", "scheme", "n", "method", "arm"], key))
        for m in met: row[m] = x[m].mean()
        for m in ["coverage", "cov_c2", "auto_orig", "missed_orig", "auto_A1", "missed_A1"]:
            row[m + "_p10"], row[m + "_p90"] = x[m].quantile(0.1), x[m].quantile(0.9)
        row["share_reps_missed_le5_orig"] = x.ok_orig.mean(); row["share_reps_missed_le5_A1"] = x.ok_A1.mean()
        out.append(row)
    out = pd.DataFrame(out)
    out.to_csv(os.path.join(ROOT, "results", "tables", "e1_summary.csv"), index=False, float_format="%.4f")
    print(f"e1_summary.csv: {len(out)} rows from {len(d)} raw rows")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summarise": summarise(); sys.exit()
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 1e9; t0 = time.time()
    only = sys.argv[2] if len(sys.argv) > 2 else "t"
    cmap = cell_maps(); os.makedirs(RAW, exist_ok=True)
    for fn in sorted(glob.glob(os.path.join(ROOT, "results", "preds", f"{only}*.csv"))):
        out = os.path.join(RAW, os.path.basename(fn))
        if os.path.exists(out): continue
        if time.time() - t0 > budget: print("budget reached"); break
        t1 = time.time(); df = run_file(fn, cmap); df.to_csv(out + ".tmp", index=False); os.replace(out + ".tmp", out)
        print(f"{os.path.basename(fn)}: {len(df)} rows, {time.time()-t1:.0f}s", flush=True)
