"""E2 report: tables (results/tables/e2_report_tables.md) and figures (outputs/figures/e2/) from the E2 outputs.
All results here are an added analysis (E2), defined after the main results had been seen.
"""
import os, sys
import numpy as np, pandas as pd, matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E

T = E.TAB; FIG = os.path.join(E.ROOT, "outputs", "figures", "e2"); os.makedirs(FIG, exist_ok=True)
ORDER = ["Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"]
INK, INK2, MUTED, GRIDC, AXC, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": AXC, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 9, "axes.titlecolor": INK,
                     "axes.grid": True, "grid.color": GRIDC, "grid.linewidth": 0.6, "axes.facecolor": SURF,
                     "figure.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.5})
md = ["# Added analysis E2: baselines, shift-robust routing and robustness checks\n",
      "Defined after the main results had been computed and seen (see configs/preregistration.md, E2 and I1–I14). "
      "Test fires: mean over seeds (and 95% cluster-bootstrap CI where shown). Eaton: mean over the 4 fold models. "
      "\"Safe\" = missed-destroyed ≤ 5%; \"useful\" = auto-labelled ≥ 50%; \"fixes transfer\" = safe and useful on ≥ 4 of 5 targets.\n"]


def tgt(d): return np.where(d.target == "eaton", "Eaton", d.fold.map(E.FIRE))


def to_md(df):
    h = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return h + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))


def save(fig, name):
    for ext in ("png", "pdf"): fig.savefig(os.path.join(FIG, f"{name}.{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def per_target(df, val_cols, keys):
    """seed mean within fold, then mean over fold models (Eaton)."""
    df = df.copy(); df["tgt"] = tgt(df)
    return df.groupby(keys + ["tgt", "fold"])[val_cols].mean().reset_index().groupby(keys + ["tgt"])[val_cols].mean().reset_index()


def cell(a, m): return f"{100 * a:.0f}% / {100 * m:.1f}%"


# ---------------- collect method results: T3, destroyed-vs-not, limit 5% ----------------
def method_table(model, task):
    w1 = pd.read_csv(os.path.join(T, "e2_wp1_runs.csv"))
    mm = "t1+t3" if model == "B5" else model
    w1 = w1[(w1.task == task) & (w1.limit == 0.05) & (w1.rule == "A1") & (w1.model.isin([model, "t1+t3"]))]
    res = per_target(w1.rename(columns={"missed_destroyed_rate": "missed", "auto_share": "auto"}), ["auto", "missed"], ["method"])
    names = {"C1_APS": "Conformal APS (Phase 5)", "C1_LAC": "Conformal LAC", "C1_Mondrian": "Conformal Mondrian",
             "C1_APS_rand": "Randomised APS (P1)", "C2_APS": "Conformal APS on seed average", "B1": "B1 top probability",
             "B2": "B2 margin", "B3": "B3 entropy", "B4": "B4 seed agreement", "B5": "B5 T1–T3 agreement"}
    res["method"] = res.method.map(names); res["family"] = "WP1 baseline"
    out = [res]
    m1 = pd.read_csv(os.path.join(T, "e2_wp2_m1.csv")); m1 = m1[(m1.model == model) & (m1.task == task) & (m1.limit == 0.05) & (m1.method == "M1_calib")]
    r = per_target(m1.rename(columns={"missed_destroyed_rate": "missed", "auto_share": "auto"}), ["auto", "missed"], []); r["method"] = "M1 risk control (calib)"; out.append(r)
    ml = pd.read_csv(os.path.join(T, "e2_wp2_m1_local.csv")); ml = ml[(ml.model == model) & (ml.task == task) & (ml.method == "M1_local")]
    for n in [100, 300]:
        r = per_target(ml[ml.n == n].rename(columns={"missed_destroyed_rate": "missed", "auto_share": "auto"}), ["auto", "missed"], [])
        r["method"] = f"M1 risk control (local sample, n = {n})"; out.append(r)
    m2 = pd.read_csv(os.path.join(T, "e2_wp2_m2.csv")); m2 = m2[(m2.model == model) & (m2.task == task) & (m2.limit == 0.05)]
    for a in [0.0, 0.05]:
        r = per_target(m2[m2.audit == a].rename(columns={"missed_mean": "missed", "auto_mean": "auto"}), ["auto", "missed"], [])
        r["method"] = f"M2 learn as you go ({int(100 * a)}% audits)"; out.append(r)
    if task == "binary":
        m3 = pd.read_csv(os.path.join(T, "e2_wp2_m3.csv")); m3 = m3[(m3.model == model) & (m3.limit == 0.05)]
        r = per_target(m3.rename(columns={"APS_missed": "missed", "APS_auto": "auto"}), ["auto", "missed"], []); r["method"] = "M3 label-shift reweighting"; out.append(r)
    m5 = pd.read_csv(os.path.join(T, "e2_wp2_m5.csv")); m5 = m5[(m5.model == model) & (m5.task == task) & (m5.limit == 0.05)]
    r = per_target(m5.rename(columns={"missed_destroyed_rate": "missed", "auto_share": "auto"}), ["auto", "missed"], []); r["method"] = "M5 look-alike weighting (scores)"; out.append(r)
    f5 = os.path.join(T, "e2_wp2_m5_features.csv")
    if os.path.exists(f5):
        m5f = pd.read_csv(f5); m5f = m5f[(m5f.model == model) & (m5f.task == task)]
        r = per_target(m5f.rename(columns={"missed_destroyed_rate": "missed", "auto_share": "auto"}), ["auto", "missed"], []); r["method"] = "M5 look-alike weighting (image features)"; out.append(r)
    res = pd.concat(out); res["family"] = res.family.fillna("WP2 repair")
    return res


def wide(res):
    w = res.assign(v=[cell(a, m) for a, m in zip(res.auto, res.missed)]).pivot_table(index=["family", "method"], columns="tgt", values="v", aggfunc="first")
    w = w[[c for c in ORDER if c in w.columns]].reset_index()
    ok = res.assign(safe=res.missed <= 0.05, useful=res.auto >= 0.5).groupby("method")[["safe", "useful"]].apply(
        lambda g: pd.Series({"safe on": int(g.safe.sum()), "safe and useful on": int((g.safe & g.useful).sum())}))
    w = w.merge(ok, left_on="method", right_index=True)
    w["fixes transfer"] = np.where(w["safe and useful on"] >= 4, "yes", "no")
    return w


for model, task in [("t3", "binary"), ("t3", "3class"), ("t1", "binary"), ("t1", "3class")]:
    res = method_table(model, task)
    md.append(f"## Methods compared — {model.upper()}, {'destroyed vs not' if task == 'binary' else '3 classes'}, limit 5%\n\n"
              "Cells: auto-labelled share / missed-destroyed rate on the target. "
              + ("Main comparison (fixed in advance): M2 with 5% audits vs Conformal APS (Phase 5)." if (model, task) == ("t3", "binary") else "") + "\n\n"
              + to_md(wide(res)) + "\n")
    if (model, task) == ("t3", "binary"): main_res = res

# per-run robustness (T3, destroyed vs not, 5%): how many single models are safe and useful
def runs_ok(d, a, m, label):
    d = d.copy(); d["tgt"] = tgt(d); out = {"method": label}
    for t in ORDER:
        x = d[d.tgt == t]; ok = ((x[m] <= 0.05) & (x[a] >= 0.5)).sum(); out[t] = f"{int(ok)}/{len(x)}"
    return out
pr = []
w1r = pd.read_csv(os.path.join(T, "e2_wp1_runs.csv")); w1r = w1r[(w1r.model == "t3") & (w1r.task == "binary") & (w1r.limit == 0.05) & (w1r.rule == "A1")]
pr.append(runs_ok(w1r[w1r.method == "C1_APS"], "auto_share", "missed_destroyed_rate", "Conformal APS (Phase 5)"))
m2r = pd.read_csv(os.path.join(T, "e2_wp2_m2.csv")); m2r = m2r[(m2r.model == "t3") & (m2r.task == "binary") & (m2r.limit == 0.05) & (m2r.audit == 0.05)]
pr.append(runs_ok(m2r, "auto_mean", "missed_mean", "M2 learn as you go (5% audits), mean over 20 orders"))
mlr = pd.read_csv(os.path.join(T, "e2_wp2_m1_local.csv")); mlr = mlr[(mlr.model == "t3") & (mlr.task == "binary") & (mlr.n == 300) & (mlr.method == "M1_local")]
mlr = mlr.groupby(["fold", "seed", "target"])[["auto_share", "missed_destroyed_rate"]].mean().reset_index()
pr.append(runs_ok(mlr, "auto_share", "missed_destroyed_rate", "M1 local sample n = 300, mean over 20 samples"))
m5r = pd.read_csv(os.path.join(T, "e2_wp2_m5.csv")); m5r = m5r[(m5r.model == "t3") & (m5r.task == "binary") & (m5r.limit == 0.05)]
pr.append(runs_ok(m5r, "auto_share", "missed_destroyed_rate", "M5 look-alike weighting (scores)"))
if os.path.exists(os.path.join(T, "e2_wp2_m5_features.csv")):
    m5fr = pd.read_csv(os.path.join(T, "e2_wp2_m5_features.csv")); m5fr = m5fr[(m5fr.model == "t3") & (m5fr.task == "binary")]
    pr.append(runs_ok(m5fr, "auto_share", "missed_destroyed_rate", "M5 look-alike weighting (image features)"))
md.append("## Per-model robustness (T3, destroyed vs not, limit 5%)\n\nNumber of single models (fold × seed runs; Eaton: all 12 fold models) that are both safe (missed ≤ 5%) and useful (auto ≥ 50%). "
          "The summary tables above average over seeds, which can hide unsafe individual models.\n\n" + to_md(pd.DataFrame(pr)[["method"] + ORDER]) + "\n")

# sensitivity 2% / 10% (T3 binary): baseline APS, M1 calib, M2 5% audits
sens = []
w1 = pd.read_csv(os.path.join(T, "e2_wp1_runs.csv")); w1 = w1[(w1.model == "t3") & (w1.task == "binary") & (w1.rule == "A1") & (w1.method == "C1_APS")]
m2 = pd.read_csv(os.path.join(T, "e2_wp2_m2.csv")); m2 = m2[(m2.model == "t3") & (m2.task == "binary") & (m2.audit == 0.05)]
m1 = pd.read_csv(os.path.join(T, "e2_wp2_m1.csv")); m1 = m1[(m1.model == "t3") & (m1.task == "binary") & (m1.method == "M1_calib")]
for lim in E.LIMITS:
    for name, d, a, m in [("Conformal APS", w1[w1.limit == lim], "auto_share", "missed_destroyed_rate"),
                          ("M1 risk control (calib)", m1[m1.limit == lim], "auto_share", "missed_destroyed_rate"),
                          ("M2 (5% audits)", m2[m2.limit == lim], "auto_mean", "missed_mean")]:
        r = per_target(d.rename(columns={a: "auto", m: "missed"}), ["auto", "missed"], [])
        sens.append({"limit": f"{int(100 * lim)}%", "method": name, **{t: cell(x.auto, x.missed) for t, x in r.set_index("tgt").iterrows()}})
md.append("## Sensitivity to the limit (T3, destroyed vs not)\n\nCells: auto-labelled / missed-destroyed.\n\n" + to_md(pd.DataFrame(sens)[["limit", "method"] + ORDER]) + "\n")

# WP4
b = pd.read_csv(os.path.join(T, "e2_wp4_binary_summary.csv"))
b["AUROC"] = [f"{m:.3f}" for m in b.auroc_mean]; b["AUPRC"] = [f"{m:.3f}" for m in b.auprc_mean]; b["destroyed F1"] = [f"{m:.3f}" for m in b.f1_destroyed_binary_mean]
b["destroyed share"] = [f"{100 * m:.1f}%" for m in b.destroyed_share]
md.append("## Destroyed vs not: ranking quality (WP4)\n\n" + to_md(b[["model", "target", "destroyed share", "AUROC", "AUPRC", "destroyed F1"]]) + "\n")
# WP5
p5 = pd.read_csv(os.path.join(T, "e2_wp5_paired.csv"))
p5["T3 − T1 [95% CI]"] = [f"{d:+.3f} [{l:+.3f}, {h:+.3f}]" for d, l, h in zip(p5.diff_t3_minus_t1, p5.ci_lo, p5.ci_hi)]
md.append("## T1 vs T3, paired cluster bootstrap (WP5)\n\nSame resample of grid cells for both models. Equivalence on macro-F1: CI inside ±0.02. Routing = APS under A1.\n\n"
          + to_md(p5.pivot_table(index="metric", columns="target", values="T3 − T1 [95% CI]", aggfunc="first")[ORDER].reset_index()) + "\n")
# WP3
s = pd.read_csv(os.path.join(T, "e2_wp3_shift.csv")); s["tgt"] = tgt(s)
g = s.groupby(["model", "tgt"])[["energy", "mmd", "transfer_gap_pp", "destroyed_share"]].mean().reset_index().round(3)
md.append("## How different is each target? (WP3)\n\nEnergy distance and MMD between calib and target probability vectors; transfer gap of Phase 5 APS (A1) in percentage points.\n\n" + to_md(g) + "\n")
bs = pd.read_csv(os.path.join(T, "e2_wp3_blocks_spearman.csv")).round(3)
md.append("Within-target check (4 × 4-cell blocks with ≥ 10 destroyed): Spearman correlation between a block's distance to calib and its missed-destroyed rate.\n\n" + to_md(bs) + "\n")
# WP6
c = pd.read_csv(os.path.join(T, "e2_wp6_cost.csv"))
c["team-days (100/day)"] = c["team_days_at_100_per_day"].round(0).astype(int); c["days, 25 teams"] = c["calendar_days_25_teams_at_100"].round(1)
c["missed destroyed"] = c.destroyed_missed.round(0)
md.append("## Inspection workload (WP6), T3, destroyed vs not, limit 5%\n\nHouses to visit include M2 audits and the M1 local sample. One team checks 100 houses per day (50 and 150 in the CSV).\n\n"
          + to_md(c[["target", "method", "houses_to_visit", "team-days (100/day)", "days, 25 teams", "missed destroyed"]]) + "\n")
# WP8
f8 = os.path.join(T, "e2_wp8_summary.csv")
if os.path.exists(f8):
    w8 = pd.read_csv(f8)
    w8["macro-F1"] = w8.macro_f1.map(lambda v: f"{v:.3f}" if v == v else "–"); w8["ECE after"] = w8.ece_after.map(lambda v: f"{v:.3f}" if v == v else "–")
    w8["AUROC destroyed"] = w8.auroc_destroyed.map(lambda v: f"{v:.3f}"); w8["binary auto / missed"] = [cell(a, m) for a, m in zip(w8.binary_auto, w8.binary_missed)]
    md.append("## Fairer test of the vision-language models (WP8)\n\nT2 prompts v2–v4, a second VLM (Gemma 4 12B, zero-shot) and T3 with a 6-epoch cap. Routing = APS under A1 on destroyed vs not.\n\n"
              + to_md(w8[["label", "target", "macro-F1", "ECE after", "AUROC destroyed", "binary auto / missed"]]) + "\n")
    fv = os.path.join(T, "e2_wp8_t3e6_val.csv")
    if os.path.exists(fv):
        v = pd.read_csv(fv).pivot_table(index=["fold", "seed"], columns="run", values="best_val_macro_f1")
        md.append(f"T3 6-epoch cap, decided on validation only: mean best val macro-F1 {v['t3'].mean():.4f} (3-epoch) vs {v['t3e6'].mean():.4f} (6-epoch); "
                  + ("by the preset rule the 6-epoch models are preferred. " if v["t3e6"].mean() > v["t3"].mean() else "the original 3-epoch models are kept. ")
                  + f"{int((v['t3e6'] == v['t3']).sum())} of {len(v)} runs are identical to the originals (early stopping ended them by epoch 3); "
                  "test macro-F1 changes by at most 0.003 per target (table above), so the main results tables keep the original models.\n")
md.append("## Palisades (WP7)\n\nNot run. The only WorldView-3 pre-fire image in the Maxar Open Data collection covers 1,546 of 10,288 Palisades structures, "
          "and the pre/post alignment check failed its preset gate (median shift 5.93 m > 5 m).\n")
open(os.path.join(T, "e2_report_tables.md"), "w").write("\n".join(md))

# ---------------- figures ----------------
# F7: work saved vs homes missed, T3 destroyed vs not, one panel per target
sel = {"Conformal APS (Phase 5)": ("o", C1), "B1 top probability": ("s", C1), "Randomised APS (P1)": ("D", C1),
       "M1 risk control (local sample, n = 300)": ("^", C2), "M2 learn as you go (5% audits)": ("o", C2),
       "M5 look-alike weighting (scores)": ("s", C2), "M5 look-alike weighting (image features)": ("D", C2)}
fig, ax = plt.subplots(1, 5, figsize=(12, 3.4), sharey=True)
for j, t in enumerate(ORDER):
    a = ax[j]; a.axhline(5, color=INK2, lw=1, ls=":"); a.axvline(50, color=GRIDC, lw=1)
    for name, (mk, col) in sel.items():
        x = main_res[(main_res.method == name) & (main_res.tgt == t)]
        if len(x): a.plot(100 * x.auto, 100 * x.missed, marker=mk, color=col, ls="none", ms=6, mec=SURF, mew=0.8, label=name)
    a.set_title(t); a.set_xlim(0, 100); a.set_ylim(0, 50); a.set_xlabel("auto-labelled (%)")
    if j == 0: a.set_ylabel("destroyed homes missed (%)"); a.text(2, 6, "5% limit", color=INK2, fontsize=7)
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.12))
fig.suptitle("Work saved vs destroyed homes missed (T3, destroyed vs not, limit 5%). Blue: baselines; orange: repair methods. Safe and useful = bottom-right of the dotted and grey lines.", fontsize=8.5, color=INK)
fig.tight_layout(rect=(0, 0.04, 1, 0.93)); save(fig, "fig7_methods_tradeoff")
# F8: M2 audit rate
m2 = pd.read_csv(os.path.join(T, "e2_wp2_m2.csv")); m2 = per_target(m2[(m2.model == "t3") & (m2.task == "binary") & (m2.limit == 0.05)].rename(columns={"missed_mean": "missed", "auto_mean": "auto"}), ["auto", "missed"], ["audit"])
fig, ax = plt.subplots(1, 2, figsize=(8.5, 3.2))
mks = dict(zip(ORDER, ["o", "s", "^", "D", "v"]))
for t in ORDER:
    x = m2[m2.tgt == t].sort_values("audit")
    ax[0].plot(100 * x.audit, 100 * x.missed, marker=mks[t], color=C2, lw=1.2, ms=5, label=t)
    ax[1].plot(100 * x.audit, 100 * x.auto, marker=mks[t], color=C2, lw=1.2, ms=5, label=t)
ax[0].axhline(5, color=INK2, lw=1, ls=":"); ax[0].set_ylabel("destroyed homes missed (%)"); ax[1].set_ylabel("auto-labelled (%)")
for a in ax: a.set_xlabel("random audit rate (% of auto-labelled houses)"); a.set_xlim(-0.5, 10.5)
ax[1].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), title="target", title_fontsize=7)
fig.suptitle("M2 learn as you go (T3, destroyed vs not): without audits it never sees its own misses", fontsize=8.5, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.92)); save(fig, "fig8_m2_audits")
# F9: shift vs transfer gap
s = pd.read_csv(os.path.join(T, "e2_wp3_shift.csv")); s["tgt"] = tgt(s)
g = s.groupby(["model", "tgt"])[["energy", "transfer_gap_pp"]].mean().reset_index()
fig, a = plt.subplots(figsize=(5.2, 3.6))
for m, col, mk in [("t1", C1, "o"), ("t2", C2, "s"), ("t3", C3, "^")]:
    x = g[g.model == m]; a.plot(x.energy, x.transfer_gap_pp, marker=mk, color=col, ls="none", ms=7, mec=SURF, mew=0.8, label=m.upper())
    for _, r in x.iterrows(): a.annotate(r.tgt, (r.energy, r.transfer_gap_pp), xytext=(4, -9 if m == "t2" else 2), textcoords="offset points", fontsize=6.5, color=INK2)
a.axhline(0, color=AXC, lw=1); a.set_xlabel("energy distance, calib vs target predictions (no labels)"); a.set_ylabel("transfer gap (percentage points)")
a.legend(loc="upper right"); a.set_title("Prediction-based shift does not predict where the 5% rule slips", fontsize=8.5)
fig.tight_layout(); save(fig, "fig9_shift_vs_gap")
# F10: paired T3 - T1
p5 = pd.read_csv(os.path.join(T, "e2_wp5_paired.csv"))
fig, ax = plt.subplots(1, 3, figsize=(10, 2.8), sharey=True)
for a, met, lab in zip(ax, ["macro_f1", "f1_des", "missed_destroyed_rate"], ["macro-F1", "destroyed F1", "missed destroyed, pp (APS, A1)"]):
    x = p5[p5.metric == met].set_index("target").loc[ORDER[::-1]].copy(); yy = np.arange(len(x))
    if met == "missed_destroyed_rate": x[["diff_t3_minus_t1", "ci_lo", "ci_hi"]] *= 100
    a.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
    a.errorbar(x.diff_t3_minus_t1, yy, xerr=[x.diff_t3_minus_t1 - x.ci_lo, x.ci_hi - x.diff_t3_minus_t1], fmt="o", color=C3, ms=5, capsize=0, lw=1.5)
    a.axvline(0, color=AXC, lw=1)
    if met == "macro_f1": a.axvspan(-0.02, 0.02, color=GRIDC, alpha=0.6, lw=0)
    a.set_yticks(yy); a.set_yticklabels(x.index); a.set_title(f"T3 − T1: {lab}")
fig.suptitle("Paired comparison with 95% cluster-bootstrap CIs (grey band: ±0.02 equivalence margin for macro-F1)", fontsize=8.5, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.9)); save(fig, "fig10_t1_vs_t3")
print("wrote e2_report_tables.md and figures")
