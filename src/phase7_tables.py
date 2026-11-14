"""Phase 7: report Tables 1-5 from existing Phase 1/3-6 outputs (no new fitting; reads results/tables only).

Outputs results/tables/table{1..5}*.csv and results/tables/report_tables.md.
Conventions: test = mean +- SD over seeds (T1, T3: 3 seeds; T2 deterministic) with 95% cluster-bootstrap CI where
available (rule 9); Eaton = mean +- SD across the 4 fold models (seed-averaged first).
Table 5 = preregistered rule 8; Table 5b = amendment A1; Table 5c = post-hoc P1 (labelled, not headline).
"""
import pandas as pd, numpy as np

from data import PROJ
T = f"{PROJ}/results/tables"
FIRE = {1: "Santa Rosa", 2: "Woolsey", 3: "Pinery", 4: "Portugal"}
MOD = {"t1": "T1 ConvNeXt", "t2": "T2 VLM zero-shot", "t3": "T3 VLM + LoRA"}
md = []


def pm(m, s, d=3):
    return f"{m:.{d}f}" if pd.isna(s) else f"{m:.{d}f} ± {s:.{d}f}"


def ci(lo, hi, d=3): return f"[{lo:.{d}f}, {hi:.{d}f}]"


def seed_ms(df, keys, cols):
    g = df.groupby(keys)[cols]; m, s = g.mean(), g.std(ddof=1)
    return m, s


def eaton_ms(df, keys, cols):  # seed-average within fold, then mean/SD across folds
    f = df.groupby(keys + ["fold"])[cols].mean().reset_index()
    g = f.groupby(keys)[cols]; return g.mean(), g.std(ddof=1)


def to_md(df):
    h = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return h + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))


def emit(name, title, df, note=""):
    df.to_csv(f"{T}/{name}.csv", index=False)
    md.append(f"## {title}\n\n{note}\n\n" + to_md(df) + "\n")


boot = pd.read_csv(f"{T}/p5_bootstrap_ci.csv")
bootA = pd.read_csv(f"{T}/p5_bootstrap_ci_A1_posthoc.csv")


def bci(model, fold, method, metric, src=boot):
    r = src[(src.model == model) & (src.fold == fold) & (src.method == method) & (src.metric == metric)]
    assert len(r) == 1, (model, fold, method, metric, len(r))
    return r.iloc[0]


# ---- Table 1: data per fold and role ----
sc = pd.read_csv(f"{T}/split_counts.csv")
t1 = sc.copy(); t1["test_fire"] = t1.fold.map(FIRE)
emit("table1_data", "Table 1. Buildings per fold and role (no damage / damaged / destroyed)", t1,
     "Grid-cell split 70/10/20 of the three training fires (rule 3); 138 xBD buildings excluded (rule 2). Eaton is scored by every fold model.")

# ---- Table 2: accuracy ----
acc = pd.read_csv(f"{T}/acc_runs.csv")
rows = []
for m in ["t1", "t2", "t3"]:
    for k in range(1, 5):
        a = acc[(acc.model == m) & (acc.fold == k) & (acc.role == "test")]
        b = bci(m, k, "LAC", "macro_f1")
        rows.append({"model": MOD[m], "evaluation": f"test: {FIRE[k]}", "n_runs": len(a),
                     "macro_F1": pm(a.macro_f1.mean(), a.macro_f1.std(ddof=1)), "macro_F1 95% CI": ci(b.ci_lo, b.ci_hi),
                     "F1 no damage": pm(a.f1_no.mean(), a.f1_no.std(ddof=1)),
                     "F1 damaged": pm(a.f1_dmg.mean(), a.f1_dmg.std(ddof=1)),
                     "F1 destroyed": pm(a.f1_des.mean(), a.f1_des.std(ddof=1))})
    e = acc[(acc.model == m) & (acc.role == "eaton")]
    em, es = eaton_ms(e.assign(k=0), ["k"], ["macro_f1", "f1_no", "f1_dmg", "f1_des"])
    rows.append({"model": MOD[m], "evaluation": "Eaton (4 fold models)", "n_runs": len(e),
                 "macro_F1": pm(em.macro_f1.iloc[0], es.macro_f1.iloc[0]), "macro_F1 95% CI": "–",
                 "F1 no damage": pm(em.f1_no.iloc[0], es.f1_no.iloc[0]), "F1 damaged": pm(em.f1_dmg.iloc[0], es.f1_dmg.iloc[0]),
                 "F1 destroyed": pm(em.f1_des.iloc[0], es.f1_des.iloc[0])})
emit("table2_accuracy", "Table 2. Accuracy (macro-F1 and per-class F1)", pd.DataFrame(rows),
     "Test: mean ± SD over seeds; CI = cluster bootstrap over test-fire grid cells (1,000 resamples, seed-pooled). "
     "Eaton: mean ± SD across the 4 fold models. T2 is deterministic (one run per fold; same model in every fold).")

# ---- Table 3: calibration ----
cal = pd.read_csv(f"{T}/p5_calibration.csv")
rows = []
for m in ["t1", "t2", "t3"]:
    for k in range(1, 5):
        c = cal[(cal.model == m) & (cal.fold == k) & (cal.role == "test")]
        b = bci(m, k, "LAC", "ece")
        rows.append({"model": MOD[m], "evaluation": f"test: {FIRE[k]}", "T": pm(c["T"].mean(), c["T"].std(ddof=1), 2),
                     "ECE before": pm(c.ece_before.mean(), c.ece_before.std(ddof=1)),
                     "ECE after": pm(c.ece_after.mean(), c.ece_after.std(ddof=1)), "ECE after 95% CI": ci(b.ci_lo, b.ci_hi),
                     "Brier before": pm(c.brier_before.mean(), c.brier_before.std(ddof=1)),
                     "Brier after": pm(c.brier_after.mean(), c.brier_after.std(ddof=1))})
    e = cal[(cal.model == m) & (cal.role == "eaton")].assign(k=0)
    em, es = eaton_ms(e, ["k"], ["T", "ece_before", "ece_after", "brier_before", "brier_after"])
    rows.append({"model": MOD[m], "evaluation": "Eaton (4 fold models)", "T": pm(em["T"].iloc[0], es["T"].iloc[0], 2),
                 "ECE before": pm(em.ece_before.iloc[0], es.ece_before.iloc[0]), "ECE after": pm(em.ece_after.iloc[0], es.ece_after.iloc[0]),
                 "ECE after 95% CI": "–", "Brier before": pm(em.brier_before.iloc[0], es.brier_before.iloc[0]),
                 "Brier after": pm(em.brier_after.iloc[0], es.brier_after.iloc[0])})
emit("table3_calibration", "Table 3. Calibration before/after temperature scaling (T fitted on calib)", pd.DataFrame(rows),
     "ECE: 15 equal-width bins on the top-class probability. Bootstrap ECE is biased upward, so the point estimate can sit near the lower CI edge.")

# ---- Table 4: conformal at alpha = 0.10 ----
def conf_table(df, methods, boot_src, posthoc=False):
    rows = []
    cols = ["coverage", "cov_c0", "cov_c1", "cov_c2", "mean_set_size"]
    for m in ["t1", "t2", "t3"]:
        for meth in methods:
            for k in list(range(1, 5)) + ["eaton"]:
                if k == "eaton":
                    d = df[(df.model == m) & (df.method == meth) & (df.role == "eaton")].assign(kk=0)
                    mm, ss = eaton_ms(d, ["kk"], cols); mm, ss = mm.iloc[0], ss.iloc[0]; cov_ci = "–"; ev = "Eaton (4 fold models)"
                else:
                    d = df[(df.model == m) & (df.method == meth) & (df.role == "test") & (df.fold == k)]
                    mm, ss = d[cols].mean(), d[cols].std(ddof=1); ev = f"test: {FIRE[k]}"
                    b = bci(m, k, meth, "coverage", boot_src); cov_ci = ci(b.ci_lo, b.ci_hi)
                rows.append({"model": MOD[m], "method": meth + (" (post-hoc)" if posthoc else ""), "evaluation": ev,
                             "coverage": pm(mm.coverage, ss.coverage), "coverage 95% CI": cov_ci,
                             "cov no damage": pm(mm.cov_c0, ss.cov_c0), "cov damaged": pm(mm.cov_c1, ss.cov_c1),
                             "cov destroyed": pm(mm.cov_c2, ss.cov_c2), "mean set size": pm(mm.mean_set_size, ss.mean_set_size, 2)})
    return pd.DataFrame(rows)

emit("table4_conformal", "Table 4. Conformal sets at α = 0.10 (target coverage 0.90): coverage per class and set size",
     conf_table(pd.read_csv(f"{T}/p5_conformal.csv"), ["LAC", "APS", "Ordinal", "Mondrian"], boot),
     "Preregistered methods (rule 7, D9). Non-randomised APS/Ordinal are degenerate (q̂ = 0, every set = top-1 class) for T1 and T3 because their calib accuracy exceeds 0.90.")
emit("table4b_conformal_posthoc", "Table 4b. POST-HOC (P1): randomised APS / Ordinal at α = 0.10",
     conf_table(pd.read_csv(f"{T}/p5_conformal_posthoc.csv"), ["APS_rand", "Ordinal_rand"], bootA, posthoc=True),
     "Added after seeing Phase 5 results (approved by Ziyad, 2026-11-10). Not a preregistered result.")

# ---- Table 5: routing ----
def route_table(df, methods, boot_src, met_auto, met_miss, label):
    rows = []
    cols = ["alpha_star", "auto_share", "missed_destroyed_rate", "error_among_auto"]
    for m in ["t1", "t2", "t3"]:
        for meth in methods:
            for k in list(range(1, 5)) + ["eaton"]:
                if k == "eaton":
                    d = df[(df.model == m) & (df.method == meth) & (df.role == "eaton")].assign(kk=0)
                    mm, ss = eaton_ms(d, ["kk"], cols); mm, ss = mm.iloc[0], ss.iloc[0]; ca = cm = "–"; ev = "Eaton (4 fold models)"
                    nm, nd = d.n_missed.sum(), d.n_destroyed.sum()
                else:
                    d = df[(df.model == m) & (df.method == meth) & (df.role == "test") & (df.fold == k)]
                    mm, ss = d[cols].mean(), d[cols].std(ddof=1); ev = f"test: {FIRE[k]}"
                    a = bci(m, k, meth, met_auto, boot_src); b = bci(m, k, meth, met_miss, boot_src)
                    ca, cm = ci(a.ci_lo, a.ci_hi), ci(b.ci_lo, b.ci_hi); nm, nd = d.n_missed.sum(), d.n_destroyed.sum()
                rows.append({"model": MOD[m], "method": meth, "rule": label, "evaluation": ev,
                             "alpha* (per run)": ", ".join(f"{v:.3f}" for v in d.alpha_star),
                             "auto-labelled share": pm(mm.auto_share, ss.auto_share), "auto 95% CI": ca,
                             "missed destroyed": pm(mm.missed_destroyed_rate, ss.missed_destroyed_rate), "missed 95% CI": cm,
                             "missed / destroyed (summed over runs)": f"{int(nm)} / {int(nd)}",
                             "error among auto": pm(mm.error_among_auto, ss.error_among_auto)})
    return pd.DataFrame(rows)

emit("table5_routing", "Table 5. Routing: auto-label singletons, α chosen on calib by rule 8 as preregistered (largest α with calib missed-destroyed ≤ 5%)",
     route_table(pd.read_csv(f"{T}/p5_routing.csv"), ["LAC", "APS", "Ordinal", "Mondrian"], boot, "auto_share", "missed_destroyed_rate", "rule 8"),
     "For LAC the rule picks the grid edge α = 0.5 (larger α gives more empty sets, so fewer auto-labels); see Table 5b.")
emit("table5b_routing_A1", "Table 5b. Routing under amendment A1 (max calib auto share s.t. calib missed-destroyed ≤ 5%)",
     route_table(pd.read_csv(f"{T}/p5_routing_amended.csv"), ["LAC", "APS", "Ordinal", "Mondrian"], bootA, "auto_share_A1", "missed_destroyed_rate_A1", "A1"),
     "A1 was proposed after seeing test results and is disclosed as such; Table 5 (original rule) is kept.")
rph = pd.read_csv(f"{T}/p5_routing_posthoc.csv")
emit("table5c_routing_posthoc", "Table 5c. POST-HOC (P1): routing with randomised APS / Ordinal under A1",
     route_table(rph[rph.rule == "A1"], ["APS_rand", "Ordinal_rand"], bootA, "auto_share_A1", "missed_destroyed_rate_A1", "A1, post-hoc"),
     "Not a preregistered result; never the headline.")

open(f"{T}/report_tables.md", "w").write("# Report tables (generated by src/phase7_tables.py)\n\n" + "\n".join(md))
print("written", len(md), "tables")
