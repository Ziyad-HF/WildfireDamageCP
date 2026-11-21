"""E2 WP2-M5, image-feature version (I10): weighted conformal routing with weights from a calib-vs-target
classifier on T1 penultimate image features (512-d, standardised; logistic regression C = 1, max_iter 1,000).
Weights w = p/(1-p) * n_calib/n_target, clipped to the calib 1st-99th percentile; APS thresholds and A1 alpha
selection as in e2_wp2.py. The weights of T1 fold k seed s are applied to both T1 and T3 runs of fold k seed s.
Output: results/tables/e2_wp2_m5_features.csv
"""
import os, sys
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
from e2_wp2 import wroute, wpick_alpha, stats

rows = []
for k in range(1, 5):
    for s in range(3):
        fz = np.load(os.path.join(E.ROOT, "results", "features", f"t1_fold{k}_seed{s}.npz"), allow_pickle=True)
        fid, frole, F = fz["ids"], fz["roles"], fz["feats"].astype(np.float32)
        pos = pd.Series(np.arange(len(fid)), index=fid)
        for target in ["test", "eaton"]:
            ic, it = np.where(frole == "calib")[0], np.where(frole == target)[0]
            X = StandardScaler().fit_transform(np.r_[F[ic], F[it]]); dl = np.r_[np.zeros(len(ic)), np.ones(len(it))]
            pr = LogisticRegression(C=1.0, max_iter=1000).fit(X, dl).predict_proba(X)[:, 1]
            w = pr / (1 - pr) * len(ic) / len(it); lo, hi = np.quantile(w[:len(ic)], [0.01, 0.99]); w = np.clip(w, lo, hi)
            wc = pd.Series(w[:len(ic)], index=fid[ic]); wt = pd.Series(w[len(ic):], index=fid[it])
            for model in ["t1", "t3"]:
                r = E.load_run(os.path.join(E.PRED, f"{model}_fold{k}_seed{s}.csv"))
                cal, tg = r["role"] == "calib", r["role"] == target
                for task in ["binary", "3class"]:
                    p, y, des = E.task_probs(r["p"], r["y"], task)
                    a_w = wc.reindex(r["id"][cal]).to_numpy(); t_w = wt.reindex(r["id"][tg]).to_numpy()
                    assert np.isfinite(a_w).all() and np.isfinite(t_w).all()
                    pick = wpick_alpha(p[cal], y[cal], a_w, des, 0.05)
                    if pick is None: st = {"auto_share": 0.0, "missed_destroyed_rate": 0.0}; a = None
                    else:
                        a = pick[0]; auto, lab = wroute(p[cal], y[cal], a_w, p[tg], t_w, a); st = stats(auto, lab, y[tg], des)
                    rows.append({"model": model, "fold": k, "seed": s, "task": task, "limit": 0.05, "target": target,
                                 "alpha": a, "auto_share": st["auto_share"], "missed_destroyed_rate": st["missed_destroyed_rate"],
                                 "domain_sep": float(pr[len(ic):].mean() - pr[:len(ic)].mean())})
        print(k, s, flush=True)
pd.DataFrame(rows).to_csv(os.path.join(E.TAB, "e2_wp2_m5_features.csv"), index=False, float_format="%.5f")
print("done")
