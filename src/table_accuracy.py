"""Accuracy tables (rule 6: macro-F1 primary, per-class F1) for each model x fold x seed on val, test and eaton.
Writes results/tables/acc_runs.csv (every run) and acc_summary.csv (T1: mean +- SD over seeds per fold;
Eaton: mean +- SD across the 4 fold models, rule 9; T2 is one deterministic model)."""
import glob, re, numpy as np, pandas as pd
from sklearn.metrics import f1_score, accuracy_score
from data import PROJ
rows = []
for f in sorted(glob.glob(f"{PROJ}/results/preds/t[123]_fold*_seed*.csv")):
    model, k, s = re.search(r"(t\d)_fold(\d)_seed(\d)", f).groups()
    d = pd.read_csv(f); pred = d[["p_no", "p_dmg", "p_des"]].to_numpy().argmax(1)
    for role in ["val", "test", "eaton"]:
        m = (d.role == role).to_numpy(); y, p = d.label[m], pred[m]
        pc = f1_score(y, p, average=None, labels=[0, 1, 2], zero_division=0)
        rows.append({"model": model, "fold": int(k), "seed": int(s), "role": role, "n": int(m.sum()),
                     "macro_f1": f1_score(y, p, average="macro", labels=[0, 1, 2], zero_division=0),
                     "f1_no": pc[0], "f1_dmg": pc[1], "f1_des": pc[2], "accuracy": accuracy_score(y, p),
                     "pred_no": int((p == 0).sum()), "pred_dmg": int((p == 1).sum()), "pred_des": int((p == 2).sum())})
r = pd.DataFrame(rows); r.round(4).to_csv(f"{PROJ}/results/tables/acc_runs.csv", index=False)
M = ["macro_f1", "f1_no", "f1_dmg", "f1_des"]
FIRE = {1: "Santa Rosa", 2: "Woolsey", 3: "Pinery", 4: "Portugal"}
out = []
for model in ["t1", "t2", "t3"]:
    for k in range(1, 5):
        g = r[(r.model == model) & (r.fold == k) & (r.role == "test")]
        out.append({"model": model, "eval": f"test fold{k} {FIRE[k]}", "n_runs": len(g),
                    **{c: f"{g[c].mean():.3f} ± {g[c].std(ddof=1):.3f}" if len(g) > 1 else f"{g[c].mean():.3f}" for c in M}})
    e = r[(r.model == model) & (r.role == "eaton")].groupby("fold")[M].mean()  # one value per fold model
    out.append({"model": model, "eval": "Eaton (mean ± SD across 4 fold models)", "n_runs": int(((r.model == model) & (r.role == "eaton")).sum()),
                **{c: f"{e[c].mean():.3f} ± {e[c].std(ddof=1):.3f}" for c in M}})
s = pd.DataFrame(out); s.to_csv(f"{PROJ}/results/tables/acc_summary.csv", index=False)
pd.set_option("display.width", 250); print(s.to_string(index=False))
print("\nper run, test + eaton macro-F1:")
print(r[r.role != "val"].pivot_table(index=["model", "fold", "seed"], columns="role", values="macro_f1").round(3).to_string())
print("\nT2 val (natural class mix):"); print(r[(r.model == "t2") & (r.role == "val")][["fold"] + M + ["pred_no", "pred_dmg", "pred_des"]].round(3).to_string(index=False))
