"""E2 WP5: paired T1 vs T3 comparison (implementation detail I12).
Same cluster-bootstrap resample of the target's grid cells for both models; metric = seed mean (Eaton: mean over
the 4 fold models x 3 seeds); difference T3 - T1 with a 95% percentile CI. Metrics: macro-F1, destroyed F1,
ECE after scaling, and APS-under-A1 auto share and missed-destroyed (Phase 5 sufficient statistics).
Equivalence on macro-F1: 95% CI inside [-0.02, 0.02].
Output: results/tables/e2_wp5_paired.csv
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
P = E.P
METS = ["macro_f1", "f1_des", "ece", "auto_share", "missed_destroyed_rate"]


def cell_sums(fn, target):
    r = E.load_run(fn); cal = r["role"] == "calib"; m = r["role"] == target
    a, _ = P.choose_alpha_amended(r["p"][cal], r["y"][cal], "APS")
    q = P.thresholds(r["p"][cal], r["y"][cal], "APS", a)
    C = P.sets(r["p"][m], "APS", q)
    ss = P.suff_stats(r["p"][m], r["y"][m], C, C)
    ss["cell"] = r["cell"][m].astype(str)
    return ss.groupby("cell").sum()


def main():
    files = {(m, k, s): fn for m, k, s, fn in E.run_files(("t1", "t3"))}
    out = []
    for target in [1, 2, 3, 4, "eaton"]:
        keys = {m: [(m, k, s) for k in ([target] if target != "eaton" else [1, 2, 3, 4]) for s in range(3)] for m in ("t1", "t3")}
        sums = {m: [cell_sums(files[key], "eaton" if target == "eaton" else "test") for key in keys[m]] for m in keys}
        idx = sums["t1"][0].index
        for m in sums:
            sums[m] = [x.reindex(idx).fillna(0) for x in sums[m]]
        rng = np.random.default_rng(0); nc = len(idx)
        W = np.stack([np.bincount(rng.integers(0, nc, nc), minlength=nc) for _ in range(1000)]).astype(float)
        res = {}
        for m in sums:
            pts, bts = [], []
            for x in sums[m]:
                A = x.to_numpy(); cols = x.columns
                pts.append(P.metrics_from_sums({c: A[:, j].sum() for j, c in enumerate(cols)}))
                TB = W @ A; bts.append(P.metrics_from_sums({c: TB[:, j] for j, c in enumerate(cols)}))
            res[m] = ({k_: np.mean([p_[k_] for p_ in pts]) for k_ in METS}, {k_: np.nanmean([b_[k_] for b_ in bts], 0) for k_ in METS})
        for met in METS:
            d_pt = res["t3"][0][met] - res["t1"][0][met]; d_bt = res["t3"][1][met] - res["t1"][1][met]
            lo, hi = np.nanpercentile(d_bt, 2.5), np.nanpercentile(d_bt, 97.5)
            row = {"target": E.FIRE[target], "metric": met, "t1": res["t1"][0][met], "t3": res["t3"][0][met],
                   "diff_t3_minus_t1": d_pt, "ci_lo": lo, "ci_hi": hi, "n_cells": nc,
                   "ci_excludes_0": bool(lo > 0 or hi < 0)}
            if met == "macro_f1": row["equivalent_within_0.02"] = bool(lo >= -0.02 and hi <= 0.02)
            out.append(row)
        print(target, "done", flush=True)
    df = pd.DataFrame(out); df.to_csv(os.path.join(E.TAB, "e2_wp5_paired.csv"), index=False, float_format="%.5f")
    print(df.round(4).to_string())


if __name__ == "__main__":
    main()
