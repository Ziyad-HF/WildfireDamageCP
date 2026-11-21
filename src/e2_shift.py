"""E2 WP3: how different is each target from the calibration buildings, and does that predict where the
missed-destroyed limit slips? (implementation detail I11)

Per run and target: energy distance and MMD (Gaussian kernel, median-heuristic bandwidth) between calib and
target temperature-scaled probability vectors (2,000 buildings each, numpy default_rng(0)), plus the transfer gap
of Phase 5 APS under A1 and simple facts (destroyed share, buildings per cell).
Within-target check: 4 x 4-cell blocks with >= 10 destroyed buildings; Spearman correlation between a block's
distance to calib and its missed-destroyed rate.
Outputs: results/tables/e2_wp3_shift.csv, e2_wp3_blocks.csv
"""
import os, sys
import numpy as np, pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
P = E.P


def sub(X, n, seed=0):
    return X if len(X) <= n else X[np.random.default_rng(seed).choice(len(X), n, replace=False)]


def energy(X, Y): return 2 * cdist(X, Y).mean() - cdist(X, X).mean() - cdist(Y, Y).mean()


def mmd(X, Y):
    Z = np.r_[X, Y]; D = cdist(Z, Z, "sqeuclidean"); bw = np.median(D[D > 0])
    K = np.exp(-D / bw); n = len(X)
    return K[:n, :n].mean() + K[n:, n:].mean() - 2 * K[:n, n:].mean()


def block_id(cell):
    a, b = str(cell).split("_")
    return f"{int(a) // 4}_{int(b) // 4}"


rows, blocks = [], []
for model, k, s, fn in E.run_files():
    r = E.load_run(fn); cal = r["role"] == "calib"
    a, rc = P.choose_alpha_amended(r["p"][cal], r["y"][cal], "APS")
    q = P.thresholds(r["p"][cal], r["y"][cal], "APS", a); Xc = sub(r["p"][cal], 2000)
    for target in ["test", "eaton"]:
        m = r["role"] == target; pt, yt = r["p"][m], r["y"][m]
        C = P.sets(pt, "APS", q); st = P.routing_stats(C, yt)
        cells = r["cell"][m].astype(str)
        rows.append({"model": model, "fold": k, "seed": s, "target": target, "energy": energy(Xc, sub(pt, 2000)),
                     "mmd": mmd(Xc, sub(pt, 2000)), "destroyed_share": float((yt == 2).mean()),
                     "buildings_per_cell": len(yt) / len(np.unique(cells)), "calib_missed": rc["missed_destroyed_rate"],
                     "target_missed": st["missed_destroyed_rate"],
                     "transfer_gap_pp": 100 * (st["missed_destroyed_rate"] - rc["missed_destroyed_rate"])})
        auto, lab = C.sum(1) == 1, C.argmax(1)
        bid = np.array([block_id(c) for c in cells])
        for b in np.unique(bid):
            mb = bid == b; nd = int((yt[mb] == 2).sum())
            if nd < 10: continue
            miss = (auto[mb] & (yt[mb] == 2) & (lab[mb] != 2)).sum() / nd
            Xb = pt[mb]
            blocks.append({"model": model, "fold": k, "seed": s, "target": target, "block": b, "n": int(mb.sum()), "n_destroyed": nd,
                           "energy": energy(Xc, sub(Xb, 2000)), "missed": miss})
    print(model, k, s, flush=True)
df = pd.DataFrame(rows); df.to_csv(os.path.join(E.TAB, "e2_wp3_shift.csv"), index=False, float_format="%.5f")
bl = pd.DataFrame(blocks); bl.to_csv(os.path.join(E.TAB, "e2_wp3_blocks.csv"), index=False, float_format="%.5f")
# within-target Spearman, per model and target (blocks pooled over seeds / fold models)
bl["tgt"] = np.where(bl.target == "eaton", "Eaton", bl.fold.map(E.FIRE))
out = []
for (model, tgt), g in bl.groupby(["model", "tgt"]):
    gg = g.groupby("block")[["energy", "missed"]].mean()
    rho, pv = spearmanr(gg.energy, gg.missed) if len(gg) >= 5 else (np.nan, np.nan)
    out.append({"model": model, "target": tgt, "n_blocks": len(gg), "spearman_rho": rho, "p_value": pv})
pd.DataFrame(out).to_csv(os.path.join(E.TAB, "e2_wp3_blocks_spearman.csv"), index=False, float_format="%.4f")
print(pd.DataFrame(out).round(3).to_string())
df["tgt"] = np.where(df.target == "eaton", "Eaton", df.fold.map(E.FIRE))
print(df.groupby(["model", "tgt"])[["energy", "mmd", "transfer_gap_pp", "destroyed_share"]].mean().round(4).to_string())
