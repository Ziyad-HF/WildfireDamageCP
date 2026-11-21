"""Collect the report tables from results/tables into one JSON file for build_report.js.
Usage: python scripts/report/report_data.py OUT.json
Every number in the report tables comes from the result files below; nothing is typed by hand.
"""
import os, sys, json, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = os.path.join(ROOT, "results", "tables")
MOD = {"T1 ConvNeXt": "T1 CNN", "T2 VLM zero-shot": "T2 VLM zero-shot", "T3 VLM + LoRA": "T3 VLM + LoRA"}
FIRES = ["Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"]


def ev(s): return "Eaton" if s.startswith("Eaton") else s.split(": ")[1]


def md_table(path, heading):
    """Rows of the first markdown table after a '## heading' line."""
    lines = open(path).read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("## ") and heading in l)
    rows = []
    for l in lines[i + 1:]:
        if l.startswith("## "): break
        if l.startswith("|") and not re.match(r"^\|(-+\|)+$", l):
            rows.append([c.strip() for c in l.strip("|").split("|")])
    return rows


out = {}
d = pd.read_csv(os.path.join(T, "table1_data.csv"))
rows = []
for _, r in d[d.role == "test"].iterrows():
    rows.append([r.test_fire, f"xBD, fold {r.fold} test", f"{r['no damage']:,}", f"{r.damaged:,}", f"{r.destroyed:,}", f"{r.total:,}"])
e = d[d.role == "eaton"].iloc[0]
rows.append(["Eaton 2025", "external test", f"{e['no damage']:,}", f"{e.damaged:,}", f"{e.destroyed:,}", f"{e.total:,}"])
out["data"] = rows

a = pd.read_csv(os.path.join(T, "table2_accuracy.csv"))
out["accuracy"] = [[MOD[r.model], ev(r.evaluation), r.macro_F1, r["macro_F1 95% CI"], r["F1 no damage"], r["F1 damaged"], r["F1 destroyed"]] for _, r in a.iterrows()]
c = pd.read_csv(os.path.join(T, "table3_calibration.csv"))
out["calibration"] = [[MOD[r.model], ev(r.evaluation), r["T"], r["ECE before"], r["ECE after"], r["Brier before"], r["Brier after"]] for _, r in c.iterrows()]
k = pd.read_csv(os.path.join(T, "table4_conformal.csv")); k = k[k.method.isin(["LAC", "APS", "Mondrian"])]
out["conformal"] = [[MOD[r.model], r.method, ev(r.evaluation), r.coverage, r["cov no damage"], r["cov damaged"], r["cov destroyed"], r["mean set size"]] for _, r in k.iterrows()]
q = pd.read_csv(os.path.join(T, "table5b_routing_A1.csv"))
q = q[q.method.isin(["LAC", "APS", "Mondrian"])]
out["routing"] = [[MOD[r.model], r.method, ev(r.evaluation), r["auto-labelled share"], r["missed destroyed"], r["missed 95% CI"], r["error among auto"]] for _, r in q.iterrows()]

e1 = pd.read_csv(os.path.join(T, "e1_summary.csv")); e1 = e1[e1.scheme == "B"]
tg = {"fold1": "Santa Rosa", "fold2": "Woolsey", "fold3": "Pinery", "fold4": "Portugal", "eaton": "Eaton"}
rows = []
for m in ["t3", "t1"]:
    for t in ["fold1", "fold2", "fold3", "fold4", "eaton"]:
        x = e1[(e1.model == m) & (e1.tgt == t)]
        g = lambda meth, arm, n, col: x[(x.method == meth) & (x.arm == arm) & (x.n == n)][col].iloc[0]
        rows.append([m.upper(), tg[t], "other fires", "–", f"{g('Mondrian', 'baseline', 100, 'cov_c2'):.3f}",
                     f"{g('APS', 'baseline', 100, 'auto_A1'):.3f}", f"{g('APS', 'baseline', 100, 'missed_A1'):.3f}", "–"])
        for n in [100, 200, 300]:
            rows.append([m.upper(), tg[t], f"local ≈{n}", f"{g('APS', 'recal', n, 'n_sample'):.0f} ({g('APS', 'recal', n, 'n_des_sample'):.0f})",
                         f"{g('Mondrian', 'recal', n, 'cov_c2'):.3f}", f"{g('APS', 'recal', n, 'auto_A1'):.3f}",
                         f"{g('APS', 'recal', n, 'missed_A1'):.3f}", f"{g('APS', 'recal', n, 'share_reps_missed_le5_A1'):.2f}"])
out["e1"] = rows

E2 = os.path.join(T, "e2_report_tables.md")
out["e2_methods"] = md_table(E2, "Methods compared — T3, destroyed vs not")
out["e2_robust"] = md_table(E2, "Per-model robustness")
out["e2_robust"][0][0] = "Method"
p = pd.read_csv(os.path.join(T, "e2_wp5_paired.csv"))
names = {"macro_f1": "Macro-F1", "f1_des": "F1 destroyed", "ece": "ECE after scaling", "auto_share": "Auto-labelled share (APS)",
         "missed_destroyed_rate": "Missed destroyed (APS)"}
out["e2_paired"] = [[names[mt]] + [
    (lambda r: f"{r.diff_t3_minus_t1:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]")(p[(p.metric == mt) & (p.target == f)].iloc[0]) for f in FIRES]
    for mt in names]
w = pd.read_csv(os.path.join(T, "e2_wp8_summary.csv"))
lab = {"t2": "Qwen3-VL zero-shot, prompt v1 (T2)", "t2v2": "Qwen3-VL, prompt v2 (CAL FIRE terms)", "t2v3": "Qwen3-VL, prompt v3 (reversed options)",
       "t2v4": "Qwen3-VL, prompt v4 (destroyed yes/no)", "t2gemma": "Gemma 4 12B zero-shot", "t3": "Qwen3-VL + LoRA, 3-epoch cap (T3)",
       "t3e6": "Qwen3-VL + LoRA, 6-epoch cap"}
rows = []
for run in ["t2", "t2v2", "t2v3", "t2v4", "t2gemma", "t3", "t3e6"]:
    x = w[w.run == run].set_index("target")
    mf = [("–" if pd.isna(x.loc[f, "macro_f1"]) else f"{x.loc[f, 'macro_f1']:.3f}") for f in FIRES]
    au = [f"{x.loc[f, 'auroc_destroyed']:.3f}" for f in FIRES]
    rows.append([lab[run], "macro-F1"] + mf); rows.append(["", "AUROC destroyed"] + au)
out["e2_vlm"] = rows
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print({k_: len(v) for k_, v in out.items()})
