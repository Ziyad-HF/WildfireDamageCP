"""Phase 7 figures (static PNG + PDF for the report) -> outputs/figures/.

fig1_reliability      reliability diagrams, before/after temperature scaling; test fires + Eaton; seeds (and Eaton fold models) pooled
fig2_coverage_alpha   empirical vs nominal coverage (1 - alpha) for Mondrian sets: overall and destroyed class; seed mean
fig3_workload         auto-labelled share vs missed-destroyed rate traced over the alpha grid (APS, Mondrian), seed mean,
                      with each run's rule-8 operating point (alpha chosen on calib) marked
fig4_examples         Eaton example houses with their sets: T3 fold 1 seed 0, Mondrian, rule-8 alpha (fixed a priori);
                      one building per category drawn with numpy default_rng(0) (not hand-picked)
fig5_eaton_map        Eaton map of auto-labelled vs routed houses, same model, APS and Mondrian at their rule-8 alpha
Everything is fitted on calib only (phase5 functions); nothing is selected on test or Eaton.
Palette: dataviz reference categorical slots 1-3 (validated all-pairs, light); identity is never colour-only
(markers/line styles + legends).
"""
import glob, re, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import softmax
from phase5 import fit_T, thresholds, sets, routing_stats, choose_alpha, bin_idx, ece, NB, GRID, LOGIT
from data import load_index, load_pair, PROJ

OUT = f"{PROJ}/outputs/figures"
FIRE = {1: "Santa Rosa", 2: "Woolsey", 3: "Pinery", 4: "Portugal", "eaton": "Eaton (2025)"}
COL = {"t1": "#2a78d6", "t2": "#eb6834", "t3": "#1baf7a"}
MK = {"t1": "o", "t2": "s", "t3": "^"}
LS = {"t1": "-", "t2": "--", "t3": "-."}
NAME = {"t1": "T1 ConvNeXt", "t2": "T2 VLM zero-shot", "t3": "T3 VLM + LoRA"}
INK, INK2, MUTED, GRIDC, AXC, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
CLS = ["no damage", "damaged", "destroyed"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": AXC, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 9, "axes.titlecolor": INK,
                     "axes.grid": True, "grid.color": GRIDC, "grid.linewidth": 0.6, "axes.facecolor": SURF,
                     "figure.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.5})


def save(fig, name):
    for ext in ("png", "pdf"): fig.savefig(f"{OUT}/{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---- load all runs once; temperature on calib ----
runs = []
for fn in sorted(glob.glob(f"{PROJ}/results/preds/t[123]_fold*_seed*.csv")):
    m, k, s = re.search(r"(t\d)_fold(\d)_seed(\d)", fn).groups()
    d = pd.read_csv(fn); z = d[LOGIT].to_numpy(np.float64); y = d.label.to_numpy(); role = d.role.to_numpy()
    T = fit_T(z[role == "calib"], y[role == "calib"])
    runs.append(dict(model=m, fold=int(k), seed=int(s), d=d, y=y, role=role, p_raw=softmax(z, 1), p_ts=softmax(z / T, 1)))
print("runs", len(runs), flush=True)
cols5 = [1, 2, 3, 4, "eaton"]


def sel(r, c):  # building mask for a panel column
    return r["role"] == ("eaton" if c == "eaton" else "test")


def runs_for(m, c): return [r for r in runs if r["model"] == m and (c == "eaton" or r["fold"] == c)]


# ---- Fig 1: reliability ----
fig, ax = plt.subplots(3, 5, figsize=(11, 6.6), sharex=True, sharey=True)
for i, m in enumerate(["t1", "t2", "t3"]):
    for j, c in enumerate(cols5):
        a = ax[i, j]; a.plot([0, 1], [0, 1], color=AXC, lw=1, zorder=1)
        for key, style in (("p_raw", dict(color=MUTED, ls="--", marker="o", mfc="none", label="before scaling")),
                           ("p_ts", dict(color=COL[m], ls="-", marker=MK[m], label="after temperature scaling"))):
            P = np.concatenate([r[key][sel(r, c)] for r in runs_for(m, c)]); Y = np.concatenate([r["y"][sel(r, c)] for r in runs_for(m, c)])
            conf, cor = P.max(1), P.argmax(1) == Y; b = bin_idx(conf)
            xs, ys = [], []
            for k in range(NB):
                mm = b == k
                if mm.sum() >= 30: xs.append(conf[mm].mean()); ys.append(cor[mm].mean())
            a.plot(xs, ys, ms=4, zorder=3, **style)
            if key == "p_ts": e_after = ece(P, Y)
            else: e_before = ece(P, Y)
        a.text(0.03, 0.97, f"pooled ECE {e_before:.3f} → {e_after:.3f}", transform=a.transAxes, va="top", color=INK2, fontsize=7)
        if i == 0: a.set_title(FIRE[c] if c == "eaton" else f"Test: {FIRE[c]}")
        if j == 0: a.set_ylabel(f"{NAME[m]}\naccuracy")
        if i == 2: a.set_xlabel("confidence (top-class probability)")
        a.set_xlim(0.3, 1.0); a.set_ylim(0.0, 1.02)
h = [plt.Line2D([], [], color=MUTED, ls="--", marker="o", mfc="none", label="before scaling")] + \
    [plt.Line2D([], [], color=COL[m], marker=MK[m], label=f"{NAME[m]}, after temperature scaling") for m in COL]
fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.03))
fig.suptitle("Reliability diagrams (15 bins; bins with ≥ 30 buildings shown; T1/T3 seeds pooled, Eaton pools all fold models).\n"
             "ECE here is computed on the pooled predictions, so it differs from the per-run means in Table 3.", color=INK, fontsize=9)
fig.tight_layout(rect=(0, 0.03, 1, 0.95)); save(fig, "fig1_reliability")
print("fig1", flush=True)

# ---- curves over alpha (test + eaton), Mondrian + APS ----
AL = GRID  # 0.005..0.5
curves = []
for r in runs:
    cal = r["role"] == "calib"; pc, yc = r["p_ts"][cal], r["y"][cal]
    for meth in ["Mondrian", "APS"]:
        qs = [thresholds(pc, yc, meth, a) for a in AL]
        for c in ([r["fold"], "eaton"]):
            msk = sel(r, c); p, y = r["p_ts"][msk], r["y"][msk]
            for a, q in zip(AL, qs):
                C = sets(p, meth, q); cov = C[np.arange(len(y)), y]; rs = routing_stats(C, y)
                curves.append(dict(model=r["model"], fold=r["fold"], seed=r["seed"], col=c, method=meth, alpha=a,
                                   coverage=cov.mean(), cov_des=cov[y == 2].mean(), auto=rs["auto_share"], missed=rs["missed_destroyed_rate"]))
cv = pd.DataFrame(curves); cv.to_csv(f"{PROJ}/results/tables/fig_curves_alpha.csv", index=False)
# Eaton: seed-average within fold model, then average over the 4 fold models (rule 9 convention); test: seed mean
agg = cv.groupby(["model", "col", "method", "alpha", "fold"])[["coverage", "cov_des", "auto", "missed"]].mean().reset_index() \
        .groupby(["model", "col", "method", "alpha"])[["coverage", "cov_des", "auto", "missed"]].mean().reset_index()
print("curves", len(cv), flush=True)

# ---- Fig 2: coverage vs nominal ----
fig, ax = plt.subplots(2, 5, figsize=(11, 4.8), sharex=True, sharey=True)
for j, c in enumerate(cols5):
    for i, (met, lab) in enumerate([("coverage", "overall coverage"), ("cov_des", "destroyed-class coverage")]):
        a = ax[i, j]; a.plot([0.5, 1], [0.5, 1], color=AXC, lw=1)
        a.axvline(0.9, color=GRIDC, lw=1, ls=":")
        for m in COL:
            g = agg[(agg.model == m) & (agg.col.astype(str) == str(c)) & (agg.method == "Mondrian")].sort_values("alpha")
            a.plot(1 - g.alpha, g[met], color=COL[m], ls=LS[m], label=NAME[m])
            g9 = g[np.isclose(g.alpha, 0.10)]; a.plot(1 - g9.alpha, g9[met], marker=MK[m], color=COL[m], ms=5, ls="none")
        if i == 0: a.set_title(FIRE[c] if c == "eaton" else f"Test: {FIRE[c]}")
        if j == 0: a.set_ylabel(lab)
        if i == 1: a.set_xlabel("nominal coverage 1 − α")
        a.set_xlim(0.5, 1.0); a.set_ylim(0.0, 1.02)
h, l = ax[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.04))
fig.suptitle("Mondrian (class-conditional) conformal sets: empirical vs nominal coverage; markers at α = 0.10; diagonal = exact coverage", color=INK, fontsize=9)
fig.tight_layout(rect=(0, 0.03, 1, 0.96)); save(fig, "fig2_coverage_alpha")
print("fig2", flush=True)

# ---- Fig 3: workload curve with rule-8 operating points ----
rt = pd.read_csv(f"{PROJ}/results/tables/p5_routing.csv")
fig, ax = plt.subplots(2, 5, figsize=(11, 4.8), sharex=True, sharey=True)
for i, meth in enumerate(["APS", "Mondrian"]):
    for j, c in enumerate(cols5):
        a = ax[i, j]; a.axhline(0.05, color=INK2, lw=1, ls=":")
        for m in COL:
            g = agg[(agg.model == m) & (agg.col.astype(str) == str(c)) & (agg.method == meth)].sort_values("alpha")
            a.plot(g.auto, g.missed, color=COL[m], ls=LS[m], label=NAME[m])
            role = "eaton" if c == "eaton" else "test"
            op = rt[(rt.model == m) & (rt.method == meth) & (rt.role == role) & ((rt.fold == c) if c != "eaton" else True)]
            a.plot(op.auto_share, op.missed_destroyed_rate, ls="none", marker=MK[m], ms=5, mfc=COL[m], mec=SURF, mew=0.8)
        if i == 0: a.set_title(FIRE[c] if c == "eaton" else f"Test: {FIRE[c]}")
        if j == 0: a.set_ylabel(f"{meth}\nmissed-destroyed rate")
        if i == 1: a.set_xlabel("auto-labelled share")
        a.set_xlim(0, 1.0); a.set_ylim(0, 0.6)
ax[0, 0].text(0.02, 0.065, "5% target", color=INK2, fontsize=7)
h, l = ax[0, 0].get_legend_handles_labels()
h.append(plt.Line2D([], [], ls="none", marker="o", color=MUTED, label="run's operating point (α chosen on calib, rule 8)"))
fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.04))
fig.suptitle("Inspector workload: share auto-labelled vs share of destroyed homes missed, traced over α ∈ [0.005, 0.5] (seed mean).\n"
             "Mondrian curves turn back at large α because sets become empty and empty sets count as routed.", color=INK, fontsize=9)
fig.tight_layout(rect=(0, 0.03, 1, 0.94)); save(fig, "fig3_workload")
print("fig3", flush=True)

# ---- Fig 4/5: fixed model T3 fold 1 seed 0 on Eaton, rule-8 alpha ----
r = [x for x in runs if x["model"] == "t3" and x["fold"] == 1 and x["seed"] == 0][0]
cal = r["role"] == "calib"; e = r["role"] == "eaton"
idx = load_index().set_index("id"); meta = pd.read_csv(f"{PROJ}/data/metadata/buildings_eaton.csv").set_index("id")
de = r["d"][e].reset_index(drop=True); pe, ye = r["p_ts"][e], r["y"][e]
Cs, alphas = {}, {}
for meth in ["APS", "Mondrian"]:
    a_star, _ = choose_alpha(r["p_ts"][cal], r["y"][cal], meth)
    alphas[meth] = a_star; Cs[meth] = sets(pe, meth, thresholds(r["p_ts"][cal], r["y"][cal], meth, a_star))
print("alpha*", alphas, flush=True)

C = Cs["Mondrian"]; size = C.sum(1); lab = C.argmax(1); auto = size == 1
cats = [("auto-labelled, correct", lambda c: auto & (lab == c) & (ye == c), [0, 1, 2]),
        ("routed to inspector (set ≥ 2 classes)", lambda c: (size >= 2) & (ye == c), [0, 1, 2]),
        ("auto-labelled, wrong", lambda c: auto & (lab != c) & (ye == c), [2, 0])]
rng = np.random.default_rng(0); picks = []
for title, f, cl in cats:
    for c in cl:
        cand = np.flatnonzero(f(c))
        picks.append((title, c, int(rng.choice(cand)) if len(cand) else None, len(cand)))
fig, ax = plt.subplots(4, 4, figsize=(8.6, 11.0), gridspec_kw={"hspace": 0.45})
for n, (title, c, i, ncand) in enumerate(picks):
    a1, a2 = ax[n // 2, (n % 2) * 2], ax[n // 2, (n % 2) * 2 + 1]
    for a in (a1, a2): a.axis("off")
    if i is None:
        a1.text(0, 0.5, f"{title}\ntrue {CLS[c]}: none", color=INK2); continue
    bid = de.id[i]; pre, post = load_pair(idx.loc[bid].to_dict() | {"id": bid})
    a1.imshow(pre); a2.imshow(post)
    S = "{" + ", ".join(CLS[k] for k in range(3) if C[i, k]) + "}"
    a1.set_title(f"{title}\ntrue: {CLS[c]}  (n = {ncand:,})", fontsize=7, loc="left", color=INK)
    a2.set_title(f"set {S}\np = {pe[i, 0]:.2f} / {pe[i, 1]:.2f} / {pe[i, 2]:.2f}", fontsize=7, loc="left", color=INK2)
    a1.text(3, 220, "pre", color="white", fontsize=7); a2.text(3, 220, "post", color="white", fontsize=7)
fig.suptitle(f"Eaton examples: T3 fold 1 seed 0, Mondrian sets at rule-8 α = {alphas['Mondrian']:.3f} (chosen on calib); "
             "one random building per category (rng 0)\np = calibrated probability of no damage / damaged / destroyed; red circle = building of interest; 224 px = 64 m",
             fontsize=8, color=INK)
fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.02, wspace=0.05); save(fig, "fig4_examples")
print("fig4", flush=True)

lon, lat = meta.loc[de.id, "lon"].to_numpy(), meta.loc[de.id, "lat"].to_numpy()
x = (lon - lon.mean()) * 111.32 * np.cos(np.radians(lat.mean())); yk = (lat - lat.mean()) * 110.57  # km, equirectangular
fig, ax = plt.subplots(2, 1, figsize=(10, 8.4), sharex=True, sharey=True)
for a, meth in zip(ax, ["APS", "Mondrian"]):
    C = Cs[meth]; size = C.sum(1); lab = C.argmax(1); auto = size == 1
    groups = [("routed to inspector", size != 1, COL["t3"], "o", 3),
              ("auto-labelled, correct", auto & (lab == ye), COL["t1"], "o", 3),
              ("auto-labelled, wrong (not missed-destroyed)", auto & (lab != ye) & ~(ye == 2), COL["t2"], "o", 5),
              ("missed destroyed (destroyed auto-labelled as not)", auto & (ye == 2) & (lab != 2), COL["t2"], "X", 18)]
    for name, msk, col, mk, s in groups:
        a.scatter(x[msk], yk[msk], s=s, c=col, marker=mk, linewidths=0.3 if mk == "X" else 0, edgecolors=SURF,
                  label=f"{name}: {msk.sum():,} ({msk.mean():.1%})")
    rs = routing_stats(C, ye)
    a.set_title(f"{meth}, rule-8 α = {alphas[meth]:.3f}: auto {rs['auto_share']:.0%}, missed destroyed {rs['n_missed']}/{rs['n_destroyed']} "
                f"({rs['missed_destroyed_rate']:.1%})", fontsize=8)
    a.set_aspect("equal"); a.set_ylabel("north (km from centroid)")
    a.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=7, markerscale=2)
ax[1].set_xlabel("east (km from centroid)")
fig.suptitle("Eaton Fire 2025 (CAL FIRE DINS, n = 8,457): auto-labelled vs routed buildings, T3 fold 1 seed 0\nlegend % = share of all buildings; title missed-destroyed % = share of destroyed buildings", color=INK, fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.95)); save(fig, "fig5_eaton_map")
print("done", flush=True)
