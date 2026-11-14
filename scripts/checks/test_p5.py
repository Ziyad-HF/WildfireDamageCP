import os, sys, glob, re, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(R, "src"))
from phase5 import *
# hand examples
p = np.array([[0.6, 0.3, 0.1], [0.2, 0.5, 0.3], [0.1, 0.2, 0.7], [0.35, 0.3, 0.35]])
print("Ordinal S:\n", scores(p, "Ordinal")); print("APS S:\n", scores(p, "APS"))
# expected Ordinal row1 (m=1, p2>p0 -> right first): S1=.5, S2=.8, S0=1 ; row3 (tie argmax->0): S0=.35,S1=.65,S2=1
# split-calib coverage test (calib only; no test/eaton used)
rng = np.random.default_rng(1); res = []
for fn in sorted(glob.glob(f"{R}/results/preds/t[12]_fold*_seed0.csv")):
    d = pd.read_csv(fn); d = d[d.role == "calib"]; z = d[LOGIT].to_numpy(float); y = d.label.to_numpy()
    T = fit_T(z, y); pt = softmax(z / T, 1)
    for rep in range(20):
        perm = rng.permutation(len(y)); a, b = perm[: len(y) // 2], perm[len(y) // 2:]
        for meth in METHODS:
            C = sets(pt[b], meth, thresholds(pt[a], y[a], meth, ALPHA)); st = set_stats(C, y[b])
            res.append({"run": fn.split("/")[-1][:-4], "method": meth, **st})
r = pd.DataFrame(res).groupby(["method"])[["coverage", "cov_c0", "cov_c1", "cov_c2", "mean_set_size", "empty_share"]].mean()
print("\nhalf-split calib coverage, mean over 8 runs x 20 splits (target >= 0.90; Mondrian per-class >= 0.90):\n", r.round(4))
print("\nT per run (seed0):", {fn.split('/')[-1][:-4]: round(fit_T(pd.read_csv(fn).query("role=='calib'")[LOGIT].to_numpy(float), pd.read_csv(fn).query("role=='calib'").label.to_numpy()), 3) for fn in sorted(glob.glob(f'{R}/results/preds/t[12]_fold1_seed0.csv'))})
