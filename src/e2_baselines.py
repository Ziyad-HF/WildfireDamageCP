"""E2 WP1 (+ WP4 re-run): simple confidence rules vs conformal routing (implementation detail I3).

Rules: B1 top probability, B2 margin, B3 minus entropy, B4 seed agreement, B5 T1-T3 agreement,
C1 conformal (LAC, APS, APS_rand, Mondrian; Phase 5), C2 conformal APS on seed-averaged probabilities.
Every rule: setting chosen on calib by the A1 rule (and the original rule 8) under a missed-destroyed limit
of 2%, 5% or 10%; locked; applied to the test fire and Eaton. Tasks: 3-class and destroyed-vs-not.
Outputs: results/tables/e2_wp1_runs.csv (one row per run x task x limit x method x rule x target)
         results/tables/e2_wp1_ci.csv  (cluster-bootstrap CIs on the test fires, limit 5%)
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
P = E.P

TASKS = ["3class", "binary"]
CMETH = ["LAC", "APS", "APS_rand", "Mondrian"]


def conformal_all(pc, yc, des, uc, meths=CMETH):
    """Routing stats on calib for every alpha of the D10 grid (computed once, filtered per limit)."""
    out = {}
    for meth in meths:
        uu = uc if meth == "APS_rand" else None
        out[meth] = [(a, P.routing_stats(P.sets(pc, meth, P.thresholds(pc, yc, meth, a, uu), uu), yc, des)) for a in P.GRID]
    return out


def choose(stats, limit, rule):
    ok = [(a, r) for a, r in stats if r["missed_destroyed_rate"] <= limit]
    if not ok: return None, None
    if rule == "orig": return ok[-1]
    best = max(r["auto_share"] for _, r in ok)
    return [(a, r) for a, r in ok if r["auto_share"] == best][-1]


def decisions_conformal(pc, yc, pt, meth, a, uc, ut):
    if a is None: return np.zeros(len(pt), bool), pt.argmax(1)
    uu, ut_ = (uc, ut) if meth == "APS_rand" else (None, None)
    C = P.sets(pt, meth, P.thresholds(pc, yc, meth, a, uu), ut_)
    return C.sum(1) == 1, C.argmax(1)


def summarise(auto, lab, y, des):
    isd = y == des; nd = int(isd.sum()); miss = auto & isd & (lab != des)
    return {"auto_share": float(auto.mean()), "missed_destroyed_rate": float(miss.sum() / nd) if nd else 0.0,
            "n_missed": int(miss.sum()), "n_destroyed": nd,
            "error_among_auto": float((lab[auto] != y[auto]).mean()) if auto.any() else np.nan}


def main():
    runs = {}
    for model, k, s, fn in E.run_files():
        runs[(model, k, s)] = E.load_run(fn)
    rows, store = [], {}  # store[(model,k,task,method,rule,target)] -> list of (auto, missed) per seed, limit 5%

    def record(key, setting, rc, target_stats, auto, miss_ind, cells):
        model, k, s, task, limit, method, rule, target = key
        rows.append({"model": model, "fold": k, "seed": s, "task": task, "limit": limit, "method": method, "rule": rule,
                     "target": target, "setting": setting, "calib_auto": rc["auto_share"] if rc else 0.0,
                     "calib_missed": rc["missed_destroyed_rate"] if rc else 0.0, **target_stats,
                     "transfer_gap_pp": 100 * (target_stats["missed_destroyed_rate"] - (rc["missed_destroyed_rate"] if rc else 0.0))})
        if limit == 0.05 and target == "test":
            store.setdefault((model, k, task, method, rule), []).append((auto.astype(float), miss_ind.astype(float), cells))

    # ---- single-run rules: B1-B3, C1 ----
    for (model, k, s), r in runs.items():
        cal = r["role"] == "calib"
        for task in TASKS:
            p, y, des = E.task_probs(r["p"], r["y"], task)
            pc, yc, uc = p[cal], y[cal], r["u"][cal]
            cstats = conformal_all(pc, yc, des, uc)
            scores = {b: E.score(p, b) for b in ["B1", "B2", "B3"]}
            cands = {b: E.candidates(scores[b][cal]) for b in scores}
            for limit in E.LIMITS:
                for b, sc in scores.items():
                    pick = E.pick_cutoff(sc[cal], p[cal].argmax(1), yc, des, limit, cand=cands[b])
                    for rule in ["A1", "orig"]:
                        t = pick[rule]; rc = E.cut_stats(sc[cal], pc.argmax(1), yc, t, des)
                        for target in ["test", "eaton"]:
                            m = r["role"] == target; lab = p[m].argmax(1); auto = sc[m] >= t
                            st = summarise(auto, lab, y[m], des)
                            record((model, k, s, task, limit, b, rule, target), t, rc, st, auto,
                                   auto & (y[m] == des) & (lab != des), r["cell"][m])
                for meth in CMETH:
                    for rule in ["A1", "orig"]:
                        a, rc = choose(cstats[meth], limit, rule)
                        for target in ["test", "eaton"]:
                            m = r["role"] == target
                            auto, lab = decisions_conformal(pc, yc, p[m], meth, a, uc, r["u"][m])
                            st = summarise(auto, lab, y[m], des)
                            record((model, k, s, task, limit, "C1_" + meth, rule, target), a, rc, st, auto,
                                   auto & (y[m] == des) & (lab != des), r["cell"][m])
        print(f"{model} fold{k} seed{s} done", flush=True)

    # ---- multi-run rules: B4 (seed agreement), C2 (conformal on seed average), B5 (T1-T3 agreement) ----
    for k in range(1, 5):
        avg = {}
        for model in ["t1", "t3"]:
            rs = [runs[(model, k, s)] for s in range(3)]
            assert all((x["id"] == rs[0]["id"]).all() for x in rs)
            r0 = rs[0]; cal = r0["role"] == "calib"
            for task in TASKS:
                ps = [E.task_probs(x["p"], x["y"], task)[0] for x in rs]; _, y, des = E.task_probs(r0["p"], r0["y"], task)
                pm = np.mean(ps, 0); avg[(model, task)] = (pm, y, des, r0)
                tops = np.stack([q.argmax(1) for q in ps]); agree = (tops == tops[0]).all(0)
                sc4 = np.where(agree, np.mean([q.max(1) for q in ps], 0), -np.inf); lab4 = tops[0]
                cst = conformal_all(pm[cal], y[cal], des, None, meths=["APS"])
                for limit in E.LIMITS:
                    pick = E.pick_cutoff(sc4[cal], lab4[cal], y[cal], des, limit)
                    for rule in ["A1", "orig"]:
                        t = pick[rule]; rc = E.cut_stats(sc4[cal], lab4[cal], y[cal], t, des)
                        a, rcc = choose(cst["APS"], limit, rule)
                        for target in ["test", "eaton"]:
                            m = r0["role"] == target
                            auto = sc4[m] >= t; st = summarise(auto, lab4[m], y[m], des)
                            record((model, k, "avg", task, limit, "B4", rule, target), t, rc, st, auto,
                                   auto & (y[m] == des) & (lab4[m] != des), r0["cell"][m])
                            auto2, lab2 = decisions_conformal(pm[cal], y[cal], pm[m], "APS", a, None, None)
                            st2 = summarise(auto2, lab2, y[m], des)
                            record((model, k, "avg", task, limit, "C2_APS", rule, target), a, rcc, st2, auto2,
                                   auto2 & (y[m] == des) & (lab2 != des), r0["cell"][m])
        for task in TASKS:
            p1, y, des, r1 = avg[("t1", task)]; p3, _, _, r3 = avg[("t3", task)]
            assert (r1["id"] == r3["id"]).all()
            cal = r1["role"] == "calib"
            agree = p1.argmax(1) == p3.argmax(1); sc5 = np.where(agree, np.minimum(p1.max(1), p3.max(1)), -np.inf); lab5 = p1.argmax(1)
            for limit in E.LIMITS:
                pick = E.pick_cutoff(sc5[cal], lab5[cal], y[cal], des, limit)
                for rule in ["A1", "orig"]:
                    t = pick[rule]; rc = E.cut_stats(sc5[cal], lab5[cal], y[cal], t, des)
                    for target in ["test", "eaton"]:
                        m = r1["role"] == target; auto = sc5[m] >= t; st = summarise(auto, lab5[m], y[m], des)
                        record(("t1+t3", k, "avg", task, limit, "B5", rule, target), t, rc, st, auto,
                               auto & (y[m] == des) & (lab5[m] != des), r1["cell"][m])
        print(f"fold{k} multi-run rules done", flush=True)

    df = pd.DataFrame(rows); df.to_csv(os.path.join(E.TAB, "e2_wp1_runs.csv"), index=False, float_format="%.5f")
    # ---- cluster-bootstrap CIs on test fires, limit 5% (seed mean within each resample) ----
    ci = []
    for (model, k, task, method, rule), lst in store.items():
        uc, inv, W = E.boot_weights(lst[0][2])
        isd_list = []
        for auto, miss, cells in lst: assert (cells == lst[0][2]).all()
        lo_a, hi_a = E.ratio_ci([x[0] for x in lst], [np.ones_like(x[0]) for x in lst], inv, W)
        # missed-destroyed denominator = destroyed buildings; recover from labels via the runs table
        sub = df[(df.model == model) & (df.fold == k) & (df.task == task) & (df.method == method) & (df.rule == rule) & (df.limit == 0.05) & (df.target == "test")]
        y_des = _destroyed_indicator(runs, model, k, task)
        lo_m, hi_m = E.ratio_ci([x[1] for x in lst], [y_des for _ in lst], inv, W)
        ci.append({"model": model, "fold": k, "task": task, "method": method, "rule": rule,
                   "auto_share": sub.auto_share.mean(), "auto_lo": lo_a, "auto_hi": hi_a,
                   "missed": sub.missed_destroyed_rate.mean(), "missed_lo": lo_m, "missed_hi": hi_m, "n_runs": len(lst)})
    pd.DataFrame(ci).to_csv(os.path.join(E.TAB, "e2_wp1_ci.csv"), index=False, float_format="%.5f")
    print("wrote e2_wp1_runs.csv", len(df), "rows; e2_wp1_ci.csv", len(ci), "rows")


def _destroyed_indicator(runs, model, k, task):
    m0 = "t1" if model == "t1+t3" else model
    r = runs[(m0, k, 0)]; m = r["role"] == "test"
    return (r["y"][m] == 2).astype(float)


if __name__ == "__main__":
    main()
