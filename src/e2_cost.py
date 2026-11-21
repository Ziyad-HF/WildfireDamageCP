"""E2 WP6: routing results as inspection workload (implementation detail I13). T3, destroyed-vs-not, limit 5%.
Houses to visit = routed (+ audits for M2); inspector-days at 50 / 100 / 150 houses per team-day; calendar days
for 10 / 25 / 50 teams; destroyed homes missed (count and per 1,000 destroyed). Test fires: mean over seeds;
Eaton: mean over the 4 fold models and seeds. Reference row: inspect everything.
Output: results/tables/e2_wp6_cost.csv
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
T = E.TAB
RATES, TEAMS = [50, 100, 150], [10, 25, 50]


def tgt(d): return np.where(d.target == "eaton", "Eaton", d.fold.map(E.FIRE))


# building and destroyed counts per target, from any T3 prediction file
counts = {}
for model, k, s, fn in E.run_files(("t3",)):
    if s: continue
    d = pd.read_csv(fn)
    for target in ["test", "eaton"]:
        x = d[d.role == target]; name = "Eaton" if target == "eaton" else E.FIRE[k]
        counts[name] = (len(x), int((x.label == 2).sum()))

rows = []
w1 = pd.read_csv(os.path.join(T, "e2_wp1_runs.csv"))
w1 = w1[(w1.model == "t3") & (w1.task == "binary") & (w1.limit == 0.05) & (w1.rule == "A1") & w1.method.isin(["C1_APS", "B1", "C1_APS_rand"])]
w1["tgt"] = tgt(w1)
for (meth, t), g in w1.groupby(["method", "tgt"]):
    rows.append({"method": {"C1_APS": "Conformal APS (Phase 5, A1)", "B1": "B1 top probability", "C1_APS_rand": "Randomised APS (P1)"}[meth],
                 "target": t, "auto_share": g.auto_share.mean(), "missed_rate": g.missed_destroyed_rate.mean(), "audits": 0.0})
m1 = pd.read_csv(os.path.join(T, "e2_wp2_m1.csv")); m1 = m1[(m1.model == "t3") & (m1.task == "binary") & (m1.limit == 0.05) & (m1.method == "M1_calib")]
m1["tgt"] = tgt(m1)
for t, g in m1.groupby("tgt"):
    rows.append({"method": "M1 risk control (calib)", "target": t, "auto_share": g.auto_share.mean(), "missed_rate": g.missed_destroyed_rate.mean(), "audits": 0.0})
ml = pd.read_csv(os.path.join(T, "e2_wp2_m1_local.csv")); ml = ml[(ml.model == "t3") & (ml.task == "binary") & (ml.n == 300) & (ml.method == "M1_local")]
ml["tgt"] = tgt(ml)
for t, g in ml.groupby("tgt"):  # the 300-house sample itself is inspected too
    rows.append({"method": "M1 risk control (local sample, n = 300)", "target": t, "auto_share": g.auto_share.mean(),
                 "missed_rate": g.missed_destroyed_rate.mean(), "audits": g.n_sample.mean(), "auto_is_share_of_rest": True})
m2 = pd.read_csv(os.path.join(T, "e2_wp2_m2.csv")); m2 = m2[(m2.model == "t3") & (m2.task == "binary") & (m2.limit == 0.05) & (m2.audit == 0.05)]
m2["tgt"] = tgt(m2)
for t, g in m2.groupby("tgt"):
    rows.append({"method": "M2 learn as you go (5% audits)", "target": t, "auto_share": g.auto_mean.mean(), "missed_rate": g.missed_mean.mean(),
                 "audits": g.audits_mean.mean()})
m5 = pd.read_csv(os.path.join(T, "e2_wp2_m5.csv")); m5 = m5[(m5.model == "t3") & (m5.task == "binary") & (m5.limit == 0.05)]
m5["tgt"] = tgt(m5)
for t, g in m5.groupby("tgt"):
    rows.append({"method": "M5 look-alike weighting (scores)", "target": t, "auto_share": g.auto_share.mean(), "missed_rate": g.missed_destroyed_rate.mean(), "audits": 0.0})
for t in counts:
    rows.append({"method": "Inspect everything", "target": t, "auto_share": 0.0, "missed_rate": 0.0, "audits": 0.0})

out = []
for r in rows:
    n, nd = counts[r["target"]]
    if r.get("auto_is_share_of_rest"):
        rest = n - r["audits"]; visit = r["audits"] + rest * (1 - r["auto_share"]); auto_n = rest * r["auto_share"]
    else:
        visit = n * (1 - r["auto_share"]) + r["audits"]; auto_n = n * r["auto_share"]
    miss = r["missed_rate"] * nd if r["missed_rate"] == r["missed_rate"] else np.nan
    row = {"method": r["method"], "target": r["target"], "buildings": n, "destroyed": nd, "auto_labelled": round(auto_n),
           "houses_to_visit": round(visit), "share_visited": visit / n, "destroyed_missed": miss,
           "missed_per_1000_destroyed": 1000 * r["missed_rate"] if miss == miss else np.nan, "safe_5pct": bool(r["missed_rate"] <= 0.05) if miss == miss else False}
    for rate in RATES:
        row[f"team_days_at_{rate}_per_day"] = visit / rate
        for teams in TEAMS:
            row[f"calendar_days_{teams}_teams_at_{rate}"] = visit / rate / teams
    out.append(row)
df = pd.DataFrame(out)
df.to_csv(os.path.join(T, "e2_wp6_cost.csv"), index=False, float_format="%.3f")
print(df[["method", "target", "houses_to_visit", "share_visited", "destroyed_missed", "team_days_at_100_per_day"]].round(2).to_string())
