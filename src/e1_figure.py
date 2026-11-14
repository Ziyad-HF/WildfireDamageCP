"""E1 figure: T3, grid-cell sampling (B). Bars = mean over 20 repeats, whiskers = 10th-90th percentile."""
import os, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = pd.read_csv(os.path.join(ROOT, "results/tables/e1_summary.csv"))
TG = ["fold1", "fold2", "fold3", "fold4", "eaton"]; LAB = ["Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"]
ARMS = [("baseline", 200, "Other fires (current)", "#9e9e9e"), ("recal", 100, "Local sample ≈100", "#a5d6a7"),
        ("recal", 200, "Local sample ≈200", "#43a047"), ("recal", 300, "Local sample ≈300", "#1b5e20")]
PAN = [("Mondrian", "cov_c2", "(a) Destroyed-class coverage\n(Mondrian, α = 0.10)", 0.90),
       ("APS", "missed_A1", "(b) Missed destroyed among auto-labels\n(APS, routing rule A1)", 0.05),
       ("APS", "auto_A1", "(c) Share auto-labelled\n(APS, routing rule A1)", None)]
for model in ["t3", "t1"]:
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    for a, (meth, col, title, ref) in zip(ax, PAN):
        x = np.arange(len(TG)); w = 0.2
        for i, (arm, n, lab, c) in enumerate(ARMS):
            q = s[(s.model == model) & (s.scheme == "B") & (s.method == meth) & (s.arm == arm) & (s.n == n)].set_index("tgt").reindex(TG)
            y = q[col].to_numpy(); lo, hi = q[col + "_p10"].to_numpy(), q[col + "_p90"].to_numpy()
            err = None if arm == "baseline" else [np.clip(y - lo, 0, None), np.clip(hi - y, 0, None)]
            a.bar(x + (i - 1.5) * w, y, w, color=c, label=lab, yerr=err, capsize=2, error_kw={"lw": 0.8})
        if ref is not None: a.axhline(ref, color="#c62828", ls="--", lw=1)
        a.set_xticks(x); a.set_xticklabels(LAB); a.set_title(title, fontsize=11)
        a.spines[["top", "right"]].set_visible(False); a.set_ylim(0, 1.05 if col != "missed_A1" else 0.45)
    h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=10)
    fig.suptitle(f"E1 (added analysis): recalibrating on a small labelled sample from the new fire — {model.upper()}, grid-cell sampling", fontsize=12)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(ROOT, f"outputs/figures/fig6_recalibration{'' if model == 't3' else '_t1'}.{ext}"), dpi=200)
    plt.close(fig)
print("ok")
