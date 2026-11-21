"""E2 WP4: destroyed vs not. Ranking quality of the temperature-scaled p_des (AUROC, AUPRC) and destroyed F1
(argmax of [1 - p_des, p_des]) per run and target, with test-fire cluster-bootstrap CIs (I5) for AUROC.
The WP1/WP2 routing re-runs on this task are in e2_wp1_runs.csv / e2_wp2_* (task = binary).
Output: results/tables/e2_wp4_binary_runs.csv, e2_wp4_binary_summary.csv
"""
import os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E

rows = []
for model, k, s, fn in E.run_files():
    r = E.load_run(fn)
    for target in ["test", "eaton"]:
        m = r["role"] == target; pd_ = r["p"][m, 2]; yb = (r["y"][m] == 2).astype(int)
        rows.append({"model": model, "fold": k, "seed": s, "target": target, "n": int(m.sum()), "destroyed_share": yb.mean(),
                     "auroc": roc_auc_score(yb, pd_), "auprc": average_precision_score(yb, pd_),
                     "f1_destroyed_binary": f1_score(yb, (pd_ >= 0.5).astype(int)),
                     "f1_destroyed_3class": f1_score(yb, (r["p"][m].argmax(1) == 2).astype(int))})
    print(model, k, s, flush=True)
df = pd.DataFrame(rows); df.to_csv(os.path.join(E.TAB, "e2_wp4_binary_runs.csv"), index=False, float_format="%.5f")
# summary: test = mean ± SD over seeds per fold; Eaton = mean ± SD across the 4 fold models (seed-averaged first)
out = []
mets = ["auroc", "auprc", "f1_destroyed_binary", "f1_destroyed_3class"]
for (model, target), g in df.groupby(["model", "target"]):
    if target == "test":
        for k, gg in g.groupby("fold"):
            out.append({"model": model, "target": E.FIRE[k], "destroyed_share": gg.destroyed_share.iloc[0],
                        **{f"{m}_mean": gg[m].mean() for m in mets}, **{f"{m}_sd": gg[m].std(ddof=1) for m in mets}})
    else:
        f = g.groupby("fold")[mets].mean()
        out.append({"model": model, "target": "Eaton", "destroyed_share": g.destroyed_share.iloc[0],
                    **{f"{m}_mean": f[m].mean() for m in mets}, **{f"{m}_sd": f[m].std(ddof=1) for m in mets}})
pd.DataFrame(out).to_csv(os.path.join(E.TAB, "e2_wp4_binary_summary.csv"), index=False, float_format="%.4f")
print(pd.DataFrame(out)[["model", "target", "auroc_mean", "auprc_mean", "f1_destroyed_binary_mean"]].round(3).to_string())
