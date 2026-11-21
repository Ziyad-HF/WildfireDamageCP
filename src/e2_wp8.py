"""E2 WP8: a fairer test of the vision-language models.
  python src/e2_wp8.py merge NAME     # e2_raw/NAME chunks -> results/preds/NAME_fold{k}_seed0.csv (same format as T2)
  python src/e2_wp8.py analyse        # accuracy, calibration and routing for every available WP8 run
Part A: T2 with prompts v2 (CAL FIRE terms), v3 (reversed options), v4 (destroyed yes/no; binary task only).
Part B: a second VLM zero-shot (google/gemma-4-12B-it, prompt v1).
Part C: T3 with a 6-epoch cap (t3e6); it replaces the original T3 only if its validation macro-F1 is higher
        (decided on val only, before looking at any test fire or Eaton).
Outputs: results/tables/e2_wp8_runs.csv, e2_wp8_summary.csv, e2_wp8_t3e6_val.csv
"""
import os, sys, glob, re, json
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, roc_auc_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
from data import load_fold
P = E.P
COLS = ["id", "source", "role", "label", "logit_no", "logit_dmg", "logit_des", "p_no", "p_dmg", "p_des"]
NAMES = {"t2": "T2 prompt v1 (original)", "t2v2": "T2 prompt v2 (CAL FIRE terms)", "t2v3": "T2 prompt v3 (reversed options)",
         "t2v4": "T2 prompt v4 (destroyed yes/no)", "t2gemma": "Gemma 4 12B zero-shot (prompt v1)",
         "t3": "T3 LoRA, 3-epoch cap (original)", "t3e6": "T3 LoRA, 6-epoch cap"}


def merge(name):
    raw = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(E.PRED, "e2_raw", name, "chunk*.csv")))])
    assert raw.id.is_unique and len(raw) == 83079, len(raw)
    L = raw[["logit_no", "logit_dmg", "logit_des"]].to_numpy()
    p = np.exp(L - L.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
    raw[["p_no", "p_dmg", "p_des"]] = p
    print(name, "letter mass min/median:", raw.abc_mass.min().round(4), raw.abc_mass.median().round(4))
    for k in range(1, 5):
        f = load_fold(k).query("role != 'train'").merge(raw, on="id", how="left", validate="1:1")
        assert f.p_no.notna().all(); f["label"] = f.y.astype(int)
        f[COLS].to_csv(os.path.join(E.PRED, f"{name}_fold{k}_seed0.csv"), index=False)
    print("wrote", name)


def runs():
    out = []
    for fn in sorted(glob.glob(os.path.join(E.PRED, "t*_fold*_seed*.csv"))):
        m = re.search(r"/(t2|t2v2|t2v3|t2v4|t2gemma|t3|t3e6)_fold(\d)_seed(\d)\.csv$", fn)
        if m: out.append((m.group(1), int(m.group(2)), int(m.group(3)), fn))
    return out


def analyse():
    rows = []
    for name, k, s, fn in runs():
        r = E.load_run(fn); cal = r["role"] == "calib"
        d = pd.read_csv(fn); z = d[P.LOGIT].to_numpy(float); praw = np.exp(z - z.max(1, keepdims=True)); praw /= praw.sum(1, keepdims=True)
        tasks = ["binary"] if name == "t2v4" else ["3class", "binary"]
        for target in ["val", "test", "eaton"]:
            m = r["role"] == target; y = r["y"][m]; p = r["p"][m]
            base = {"run": name, "fold": k, "seed": s, "target": target, "T": r["T"]}
            if name != "t2v4":
                pred = p.argmax(1); f1 = f1_score(y, pred, average=None, labels=[0, 1, 2])
                base.update({"macro_f1": f1.mean(), "f1_no": f1[0], "f1_dmg": f1[1], "f1_des": f1[2],
                             "ece_before": P.ece(praw[m], y), "ece_after": P.ece(p, y)})
            yb = (y == 2).astype(int); base.update({"auroc_destroyed": roc_auc_score(yb, p[:, 2]),
                                                    "f1_destroyed_binary": f1_score(yb, (p[:, 2] >= 0.5).astype(int))})
            if target != "val":
                for task in tasks:
                    pt, yt, des = E.task_probs(r["p"], r["y"], task)
                    a, rc, st = E.conformal_route(pt[cal], yt[cal], pt[m], yt[m], "APS", "A1", des)
                    base.update({f"{task}_alpha": a, f"{task}_auto": st["auto_share"], f"{task}_missed": st["missed_destroyed_rate"]})
            rows.append(base)
        print(name, k, s, flush=True)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(E.TAB, "e2_wp8_runs.csv"), index=False, float_format="%.5f")
    # summary: test = mean over seeds per fold; Eaton = mean over fold models (seed-averaged first)
    mets = [c for c in df.columns if c not in ("run", "fold", "seed", "target")]
    out = []
    for (name, target), g in df[df.target != "val"].groupby(["run", "target"]):
        if target == "test":
            for k, gg in g.groupby("fold"):
                out.append({"run": name, "label": NAMES[name], "target": E.FIRE[k], **gg[mets].mean().to_dict()})
        else:
            out.append({"run": name, "label": NAMES[name], "target": "Eaton", **g.groupby("fold")[mets].mean().mean().to_dict()})
    pd.DataFrame(out).to_csv(os.path.join(E.TAB, "e2_wp8_summary.csv"), index=False, float_format="%.4f")
    # Part C decision on val only
    logs = []
    for tag in ["t3", "t3e6"]:
        for fn in sorted(glob.glob(os.path.join(E.ROOT, "results", "t3_logs", f"{tag}_fold*_seed*.json"))):
            j = json.load(open(fn)); mm = re.search(r"fold(\d)_seed(\d)", fn)
            logs.append({"run": tag, "fold": int(mm.group(1)), "seed": int(mm.group(2)), "best_val_macro_f1": j["best_val_macro_f1"],
                         "best_epoch": j["best_epoch"], "steps_run": j["steps_run"], "gpu": j["gpu"]})
    lg = pd.DataFrame(logs)
    if (lg.run == "t3e6").any():
        piv = lg.pivot_table(index=["fold", "seed"], columns="run", values="best_val_macro_f1")
        lg.to_csv(os.path.join(E.TAB, "e2_wp8_t3e6_val.csv"), index=False, float_format="%.4f")
        print("Part C, mean val macro-F1:", piv.mean().round(4).to_dict(),
              "-> 6-epoch T3 replaces the original" if piv["t3e6"].mean() > piv["t3"].mean() else "-> original T3 kept")
    print(pd.DataFrame(out)[["label", "target", "macro_f1", "ece_after", "auroc_destroyed", "3class_missed", "binary_auto", "binary_missed"]].round(3).to_string())


if __name__ == "__main__":
    if sys.argv[1] == "merge": merge(sys.argv[2])
    else: analyse()
