import re, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import glob
for f in glob.glob("/root/.fonts/roboto/Roboto-*.ttf"):
    try: fm.fontManager.addfont(f)
    except Exception: pass
plt.rcParams.update({"font.family": "Roboto", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8B9088", "axes.labelcolor": "#4A4A48", "xtick.color": "#4A4A48", "ytick.color": "#4A4A48"})
G, GOLD, GREY, RED, LG, BODY = "#275D37", "#F1CC00", "#8B9088", "#C00000", "#4EA72E", "#4A4A48"
MC = {"T1": "#275D37", "T2": "#8B9088", "T3": "#F1CC00"}
T = "/mnt/user-data/uploads/Project/WildfireDamageCP/results/tables/"
FIRES = ["Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"]
def ev(s): return "Eaton" if s.startswith("Eaton") else s.split(": ")[1]
def num(s): return float(str(s).split(" ")[0])
def lohi(s):
    m = re.findall(r"[\d.]+", str(s)); return (float(m[0]), float(m[1])) if len(m) == 2 else (np.nan, np.nan)
mod = lambda s: s.split(" ")[0]
a = pd.read_csv(T + "table2_accuracy.csv"); a["fire"] = a.evaluation.map(ev); a["m"] = a.model.map(mod)
c = pd.read_csv(T + "table4_conformal.csv"); c["fire"] = c.evaluation.map(ev); c["m"] = c.model.map(mod)
r = pd.read_csv(T + "table5b_routing_A1.csv"); r["fire"] = r.evaluation.map(ev); r["m"] = r.model.map(mod)
k = pd.read_csv(T + "table3_calibration.csv"); k["fire"] = k.evaluation.map(ev); k["m"] = k.model.map(mod)

def bars(ax, df, col, models, ci=None, ref=None, reflab=None, ylim=(0, 1), fmt="{:.2f}", labels=True):
    x = np.arange(len(FIRES)); w = 0.8 / len(models)
    for i, m in enumerate(models):
        d = df[df.m == m].set_index("fire").reindex(FIRES); y = d[col].map(num).to_numpy()
        err = None
        if ci is not None:
            lo, hi = zip(*d[ci].map(lohi)); lo, hi = np.array(lo), np.array(hi)
            err = np.vstack([np.where(np.isnan(lo), 0, y - lo), np.where(np.isnan(hi), 0, hi - y)])
        b = ax.bar(x + (i - (len(models) - 1) / 2) * w, y, w * 0.95, color=MC[m], label={"T1": "T1 CNN", "T2": "T2 VLM zero-shot", "T3": "T3 VLM + LoRA"}[m],
                   yerr=err, capsize=3, error_kw={"lw": 1, "ecolor": BODY}, edgecolor="white")
        if labels:
            top = y if err is None else y + err[1]
            for xi, yi, ti in zip(x + (i - (len(models) - 1) / 2) * w, y, top):
                ax.text(xi, ti + (ylim[1] - ylim[0]) * 0.015, fmt.format(yi), ha="center", va="bottom", fontsize=10, color=BODY)
    if ref is not None:
        ax.axhline(ref, color=RED, ls="--", lw=1.5); ax.text(-0.45, ref + (ylim[1]-ylim[0])*0.01, reflab, color=RED, va="bottom", ha="left", fontsize=11)
    ax.set_xticks(x); ax.set_xticklabels([f if f != "Eaton" else "Eaton 2025\n(external)" for f in FIRES]); ax.set_ylim(*ylim)
    ax.axvspan(3.5, 4.5, color="#EDF5F0", zorder=-1)

def save(fig, name): fig.savefig(f"img/{name}.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# A: macro-F1
fig, ax = plt.subplots(figsize=(10, 4.3)); bars(ax, a, "macro_F1", ["T1", "T2", "T3"], ci="macro_F1 95% CI", ylim=(0, 0.85))
ax.set_ylabel("macro-F1 (3 classes)"); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12)); save(fig, "figA_macroF1")
# A2: per-class F1 (T3)
fig, ax = plt.subplots(figsize=(10, 4.0)); x = np.arange(5); d = a[a.m == "T3"].set_index("fire").reindex(FIRES)
for i, (col, cc, lab) in enumerate([("F1 no damage", G, "no damage"), ("F1 damaged", RED, "damaged"), ("F1 destroyed", GOLD, "destroyed")]):
    y = d[col].map(num).to_numpy(); ax.bar(x + (i - 1) * 0.27, y, 0.26, color=cc, label=lab, edgecolor="white")
    for xi, yi in zip(x + (i - 1) * 0.27, y): ax.text(xi, yi + 0.015, f"{yi:.2f}", ha="center", fontsize=10, color=BODY)
ax.set_xticks(x); ax.set_xticklabels(FIRES); ax.set_ylim(0, 1.08); ax.set_ylabel("F1 (T3, seed mean)"); ax.axvspan(3.5, 4.5, color="#EDF5F0", zorder=-1)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13)); save(fig, "figA2_perclassF1")
# B: ECE after scaling
fig, ax = plt.subplots(figsize=(10, 4.0)); bars(ax, k, "ECE after", ["T1", "T2", "T3"], ylim=(0, 0.27), fmt="{:.3f}")
ax.set_ylabel("ECE after temperature scaling"); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12)); save(fig, "figB_ece")
# C: destroyed coverage, Mondrian
cm = c[c.method == "Mondrian"]
fig, ax = plt.subplots(figsize=(10, 4.3)); bars(ax, cm, "cov destroyed", ["T1", "T2", "T3"], ref=0.9, reflab="target 0.90", ylim=(0, 1.12))
ax.set_ylabel("coverage of destroyed homes\n(Mondrian sets, α = 0.10)"); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12)); save(fig, "figC_destroyed_coverage")
# C2: overall coverage per method T3
fig, ax = plt.subplots(figsize=(10, 4.0)); x = np.arange(5)
for i, (meth, cc) in enumerate([("LAC", GREY), ("APS", GOLD), ("Mondrian", G)]):
    d = c[(c.m == "T3") & (c.method == meth)].set_index("fire").reindex(FIRES); y = d.coverage.map(num).to_numpy()
    ax.bar(x + (i - 1) * 0.27, y, 0.26, color=cc, label=meth, edgecolor="white")
    for xi, yi in zip(x + (i - 1) * 0.27, y): ax.text(xi, yi + 0.01, f"{yi:.2f}", ha="center", fontsize=10, color=BODY)
ax.axhline(0.9, color=RED, ls="--", lw=1.5); ax.set_xticks(x); ax.set_xticklabels(FIRES); ax.set_ylim(0.5, 1.02); ax.set_ylabel("overall coverage (T3)")
ax.axvspan(3.5, 4.5, color="#EDF5F0", zorder=-1); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13)); save(fig, "figC2_overall_coverage")
# D: routing APS (A1 = rule 8 for APS)
ra = r[r.method == "APS"]
fig, ax = plt.subplots(1, 2, figsize=(15, 4.6))
bars(ax[0], ra, "auto-labelled share", ["T1", "T3"], ci="auto 95% CI", ylim=(0, 1.1)); ax[0].set_title("Share auto-labelled (no visit)", color=G, fontweight="bold")
bars(ax[1], ra, "missed destroyed", ["T1", "T3"], ci="missed 95% CI", ref=0.05, reflab="5% target", ylim=(0, 0.5)); ax[1].set_title("Destroyed homes missed among auto-labels", color=G, fontweight="bold")
ax[0].legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
save(fig, "figD_routing")
# E: E1 recalibration (T3, scheme B)
e = pd.read_csv(T + "e1_summary.csv"); TG = ["fold1", "fold2", "fold3", "fold4", "eaton"]
fig, ax = plt.subplots(1, 2, figsize=(13, 4.3))
for j, (meth, col, title, ref, yl) in enumerate([("Mondrian", "cov_c2", "Coverage of destroyed homes (Mondrian)", 0.9, (0, 1.1)),
                                                ("APS", "missed_A1", "Destroyed homes missed (APS routing)", 0.05, (0, 0.42))]):
    x = np.arange(5)
    for i, (arm, n, lab, cc) in enumerate([("baseline", 200, "calibrated on other fires", GREY), ("recal", 100, "local sample ≈100", "#A8D5A2"),
                                           ("recal", 200, "local sample ≈200", LG), ("recal", 300, "local sample ≈300", G)]):
        q = e[(e.model == "t3") & (e.scheme == "B") & (e.method == meth) & (e.arm == arm) & (e.n == n)].set_index("tgt").reindex(TG)
        ax[j].bar(x + (i - 1.5) * 0.2, q[col], 0.19, color=cc, label=lab, edgecolor="white")
    ax[j].axhline(ref, color=RED, ls="--", lw=1.5); ax[j].set_xticks(x); ax[j].set_xticklabels(FIRES); ax[j].set_ylim(*yl)
    ax[j].set_title(title, color=G, fontweight="bold"); ax[j].axvspan(3.5, 4.5, color="#EDF5F0", zorder=-1)
h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.06))
save(fig, "figE_recalibration")
# F: data composition (test role per fold + eaton), from table1
t1 = pd.read_csv(T.replace("tables/", "tables/") + "table1_data.csv") if False else None
