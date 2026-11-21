"""E2 WP2: keeping the missed-destroyed limit on a new fire (implementation details I6-I10).

M1 risk control (calib / local sample / both), M2 adaptive stream with random audits, M3 label-shift reweighting
(BBSE), M4 shift alarm with fallbacks, M5 weighted conformal (logit features). Baseline = Phase 5 APS under A1.
Main comparison (E2): M2 with 5% audits vs APS-A1, T3, destroyed-vs-not, 4 test fires + Eaton.
Limits: 5% for every run and task; 2% and 10% for T3 on the destroyed-vs-not task (sensitivity).
Usage: e2_wp2.py [models]   (default t1,t2,t3)
Outputs (results/tables/): e2_wp2_m1.csv, e2_wp2_m1_local.csv, e2_wp2_m2.csv, e2_wp2_m3.csv, e2_wp2_m4.csv, e2_wp2_m5.csv
"""
import os, sys
import numpy as np, pandas as pd
from scipy.spatial.distance import cdist
from sklearn.linear_model import LogisticRegression
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_common as E
import e1_recalibration as E1
P = E.P
AUDITS = [0.0, 0.02, 0.05, 0.10]; GAMMAS = [0.01, 0.05, 0.10]; NORD = 20


def limits_for(model, task):
    return E.LIMITS if (model == "t3" and task == "binary") else [0.05]


# ---------------- M1 risk control ----------------
def crc_cut(sc, lab, y, des, limit, cand, w=None):
    """Smallest t in cand with (sum_w L(t) + 1) / (sum_w n_d + 1) <= limit; inf if none."""
    w = np.ones(len(y)) if w is None else w
    isd = y == des; nd = w[isd].sum(); wrong = isd & (lab != des)
    for t in np.sort(cand):
        if ((w * (wrong & (sc >= t))).sum() + 1) / (nd + 1) <= limit: return t
    return np.inf


# ---------------- M2 adaptive stream ----------------
def stream(sc, lab, y, cells, lam0, gamma, a, o, limit, des):
    uc = np.unique(cells); order = np.random.default_rng(500 + o).permutation(len(uc))
    pos = {c: i for i, c in enumerate(uc[order])}
    key = np.array([pos[c] for c in cells]); idx = np.argsort(key, kind="stable"); kk = key[idx]
    bounds = np.r_[0, np.flatnonzero(np.diff(kk)) + 1, len(kk)]
    audit_u = np.random.default_rng(900 + o).random(len(idx))
    lam = lam0; e_miss = e_des_routed = e_des_aud = 0.0; auto_all = np.zeros(len(y), bool); n_aud = 0
    for b0, b1 in zip(bounds[:-1], bounds[1:]):
        ii = idx[b0:b1]; auto = sc[ii] >= lam; auto_all[ii] = auto
        isd = y[ii] == des
        e_des_routed += (isd & ~auto).sum()
        if a > 0:
            aud = auto & (audit_u[b0:b1] < a); n_aud += int(aud.sum())
            e_miss += (aud & isd & (lab[ii] != des)).sum() / a; e_des_aud += (aud & isd).sum() / a
        est_d = e_des_routed + e_des_aud
        rate = e_miss / est_d if (a > 0 and est_d > 0) else 0.0
        lam = float(np.clip(lam + gamma * (rate - limit), 0.0, 1.0))
    isd = y == des; nd = isd.sum(); miss = (auto_all & isd & (lab != des)).sum()
    return {"missed": miss / nd if nd else 0.0, "auto": auto_all.mean(), "inspections": int((~auto_all).sum() + n_aud),
            "n_audit": n_aud, "lam_final": lam}


def m2(sc, lab, y, cells, cal, tgt, lam0, limit, des):
    out = []
    for a in AUDITS:
        res = {}
        for g in GAMMAS:  # gamma chosen on the run's calib buildings (I7)
            rr = [stream(sc[cal], lab[cal], y[cal], cells[cal], lam0, g, a, o, limit, des) for o in range(NORD)]
            res[g] = (np.mean([r["auto"] for r in rr]), np.mean([r["missed"] for r in rr]))
        ok = [g for g in GAMMAS if res[g][1] <= limit]
        g = max(ok, key=lambda g: res[g][0]) if ok else min(GAMMAS, key=lambda g: res[g][1])
        rr = [stream(sc[tgt], lab[tgt], y[tgt], cells[tgt], lam0, g, a, o, limit, des) for o in range(NORD)]
        M = np.array([r["missed"] for r in rr]); A = np.array([r["auto"] for r in rr])
        out.append({"audit": a, "gamma": g, "calib_auto": res[g][0], "calib_missed": res[g][1],
                    "missed_mean": M.mean(), "missed_p10": np.quantile(M, .1), "missed_p90": np.quantile(M, .9),
                    "auto_mean": A.mean(), "auto_p10": np.quantile(A, .1), "auto_p90": np.quantile(A, .9),
                    "inspections_mean": np.mean([r["inspections"] for r in rr]), "audits_mean": np.mean([r["n_audit"] for r in rr]),
                    "lam_final_mean": np.mean([r["lam_final"] for r in rr]), "share_orders_missed_le_limit": float((M <= limit).mean())})
    return out


# ---------------- weighted conformal (M3, M5) ----------------
def wthresholds(s_cal_true, w_cal, w_query, alpha):
    """Per-query weighted split-conformal threshold (Tibshirani et al. 2019): smallest s with
    sum_{s_i <= s} w_i >= (1 - alpha)(W + w_query); inf if not reached."""
    o = np.argsort(s_cal_true); s = s_cal_true[o]; cw = np.cumsum(w_cal[o]); W = cw[-1]
    j = np.searchsorted(cw, (1 - alpha) * (W + w_query), side="left")
    return np.where(j < len(s), s[np.minimum(j, len(s) - 1)], np.inf)


def wroute(p_cal, y_cal, w_cal, p_q, w_q, alpha, meth="APS"):
    S_cal = P.scores(p_cal, meth); q = wthresholds(S_cal[np.arange(len(y_cal)), y_cal], w_cal, w_q, alpha)
    C = P.scores(p_q, meth) <= q[:, None]
    return C.sum(1) == 1, C.argmax(1)


def wpick_alpha(p_cal, y_cal, w_cal, des, limit):
    best = None
    for a in P.GRID:
        auto, lab = wroute(p_cal, y_cal, w_cal, p_cal, w_cal, a)
        isd = y_cal == des; nd = w_cal[isd].sum()
        miss = (w_cal * (auto & isd & (lab != des))).sum() / nd if nd > 0 else 0.0
        au = (w_cal * auto).sum() / w_cal.sum()
        if miss <= limit and (best is None or au >= best[1]): best = (a, au, miss)
    return best


def stats(auto, lab, y, des):
    isd = y == des; nd = isd.sum(); miss = (auto & isd & (lab != des)).sum()
    return {"auto_share": float(auto.mean()), "missed_destroyed_rate": float(miss / nd) if nd else 0.0, "n_destroyed": int(nd)}


def energy(X, Y):
    return 2 * cdist(X, Y).mean() - cdist(X, X).mean() - cdist(Y, Y).mean()


def sub(X, n, seed):
    if len(X) <= n: return X
    return X[np.random.default_rng(seed).choice(len(X), n, replace=False)]


def main(models):
    cmap = E.cell_map()
    m1, m1l, m2r, m3, m4, m5 = [], [], [], [], [], []
    for model, k, s, fn in E.run_files(models):
        r = E.load_run(fn); cal = r["role"] == "calib"; val = r["role"] == "val"; cache = {}
        for task in ["binary", "3class"]:
            p, y, des = E.task_probs(r["p"], r["y"], task)
            sc, lab = p.max(1), p.argmax(1); cand = E.candidates(sc[cal])
            for limit in limits_for(model, task):
                lam0 = crc_cut(sc[cal], lab[cal], y[cal], des, limit, cand)
                for target in ["test", "eaton"]:
                    tg = r["role"] == target
                    key = {"model": model, "fold": k, "seed": s, "task": task, "limit": limit, "target": target}
                    # baseline APS-A1 (Phase 5 rule) and M1(a)
                    a_b, rc_b, st_b = E.conformal_route(p[cal], y[cal], p[tg], y[tg], "APS", "A1", des, limit=limit)
                    st1 = stats(sc[tg] >= lam0, lab[tg], y[tg], des)
                    m1.append({**key, "method": "baseline_APS_A1", "setting": a_b, **{k_: st_b[k_] for k_ in ("auto_share", "missed_destroyed_rate")}})
                    m1.append({**key, "method": "M1_calib", "setting": lam0, **{k_: st1[k_] for k_ in ("auto_share", "missed_destroyed_rate")}})
                    # M2 stream
                    for row in m2(sc, lab, y, r["cell"].astype(str), cal, tg, lam0, limit, des):
                        m2r.append({**key, "lam0": lam0, **row})
                    if limit != 0.05: continue
                    # M1(b)/(c) local samples (E1 scheme B, seeds), evaluated on target minus sample
                    ii = np.where(tg)[0]; ii = ii[np.argsort(r["id"][ii])]
                    cells = cmap.reindex(r["id"][ii]).to_numpy()
                    for n in E1.NS:
                        for rep in range(E1.R):
                            S = E1.draw(ii, cells, "B", n, rep); smp, rest = ii[S], ii[~S]
                            lb = crc_cut(sc[smp], lab[smp], y[smp], des, limit, E.candidates(sc[smp]))
                            w = np.r_[np.ones(cal.sum()), np.full(len(smp), 10.0)]
                            both = np.r_[np.where(cal)[0], smp]
                            lc = crc_cut(sc[both], lab[both], y[both], des, limit, cand, w=w)
                            for name, lam in [("M1_local", lb), ("M1_both", lc), ("M1_calib", lam0)]:
                                st = stats(sc[rest] >= lam, lab[rest], y[rest], des)
                                m1l.append({**key, "n": n, "rep": rep, "method": name, "lam": lam, "n_sample": len(smp),
                                            "n_des_sample": int((y[smp] == des).sum()), **st})
                            C = None
                            if a_b is not None:
                                q = P.thresholds(p[cal], y[cal], "APS", a_b); C = P.sets(p[rest], "APS", q)
                                stb = stats(C.sum(1) == 1, C.argmax(1), y[rest], des)
                            else:
                                stb = {"auto_share": 0.0, "missed_destroyed_rate": 0.0, "n_destroyed": int((y[rest] == des).sum())}
                            m1l.append({**key, "n": n, "rep": rep, "method": "baseline_APS_A1", "lam": a_b, "n_sample": len(smp),
                                        "n_des_sample": int((y[smp] == des).sum()), **stb})
                    # M4 alarm (I9): energy distance calib vs target; null = calib vs bootstrapped val
                    Xc = sub(p[cal], 2000, 0); Xt = sub(p[tg], 2000, 0)
                    if (task, "null") not in cache:
                        Xv_all = p[val]; rng = np.random.default_rng(1)
                        null = [energy(Xc, sub(Xv_all[rng.integers(0, len(Xv_all), len(Xv_all))], 2000, int(rng.integers(1 << 30)))) for _ in range(200)]
                        cache[(task, "null")] = float(np.quantile(null, 0.99))
                    stat = energy(Xc, Xt); thr = cache[(task, "null")]; alarm = stat > thr
                    m4.append({**key, "energy": stat, "threshold_q99": thr, "alarm": bool(alarm),
                               "d_mean_top": float(p[tg].max(1).mean() - p[cal].max(1).mean()),
                               "d_pred_destroyed": float((p[tg].argmax(1) == des).mean() - (p[cal].argmax(1) == des).mean()),
                               "no_alarm_auto": st_b["auto_share"], "no_alarm_missed": st_b["missed_destroyed_rate"]})
                    # M5 weighted conformal on scaled logits (I10)
                    Z = np.r_[r["z"][cal], r["z"][tg]]; dlab = np.r_[np.zeros(cal.sum()), np.ones(tg.sum())]
                    clf = LogisticRegression(C=1.0, max_iter=1000).fit(Z, dlab); pr = clf.predict_proba(Z)[:, 1]
                    wv = pr / (1 - pr) * cal.sum() / tg.sum(); lo, hi = np.quantile(wv[:cal.sum()], [0.01, 0.99]); wv = np.clip(wv, lo, hi)
                    wc, wt = wv[:cal.sum()], wv[cal.sum():]
                    pick = wpick_alpha(p[cal], y[cal], wc, des, limit)
                    if pick is None: st5 = {"auto_share": 0.0, "missed_destroyed_rate": 0.0}; a5 = None
                    else:
                        a5 = pick[0]; auto, lb5 = wroute(p[cal], y[cal], wc, p[tg], wt, a5); st5 = stats(auto, lb5, y[tg], des)
                    m5.append({**key, "alpha": a5, "auto_share": st5["auto_share"], "missed_destroyed_rate": st5["missed_destroyed_rate"],
                               "domain_auc_proxy": float(np.mean(pr[cal.sum():]) - np.mean(pr[:cal.sum()]))})
                    # M3 label shift (BBSE), destroyed-vs-not only (I8)
                    if task == "binary":
                        Cm = np.zeros((2, 2))
                        for i_ in range(2):
                            for j_ in range(2): Cm[i_, j_] = np.mean((lab[cal] == i_) & (y[cal] == j_))
                        qt = np.bincount(lab[tg], minlength=2) / tg.sum(); pi = np.bincount(y[cal], minlength=2) / cal.sum()
                        try:
                            raw = np.linalg.solve(Cm, qt) / pi; ok = bool((raw >= 0).all())
                        except np.linalg.LinAlgError:
                            raw = np.ones(2); ok = False
                        wcls = np.clip(raw, 0, 10) if ok else np.ones(2)
                        w3c = wcls[y[cal]]; w3t = np.full(tg.sum(), wcls.max())
                        pick = wpick_alpha(p[cal], y[cal], w3c, des, limit)
                        if pick is None: st3 = {"auto_share": 0.0, "missed_destroyed_rate": 0.0}; a3 = None
                        else:
                            a3 = pick[0]; auto, lb3 = wroute(p[cal], y[cal], w3c, p[tg], w3t, a3); st3 = stats(auto, lb3, y[tg], des)
                        t3c = E.pick_cutoff(sc[cal], lab[cal], y[cal], des, limit, w=w3c, cand=cand)["A1"]
                        stb1 = stats(sc[tg] >= t3c, lab[tg], y[tg], des)
                        m3.append({**key, "estimable": ok, "w_not": wcls[0], "w_destroyed": wcls[1],
                                   "est_destroyed_share": float(np.clip(raw[1] * pi[1], 0, 1)) if ok else np.nan,
                                   "true_destroyed_share": float((y[tg] == des).mean()), "alpha_APS": a3,
                                   "APS_auto": st3["auto_share"], "APS_missed": st3["missed_destroyed_rate"],
                                   "B1_cut": t3c, "B1_auto": stb1["auto_share"], "B1_missed": stb1["missed_destroyed_rate"]})
        print(f"{model} fold{k} seed{s} done", flush=True)
    for name, rows in [("m1", m1), ("m1_local", m1l), ("m2", m2r), ("m3", m3), ("m4", m4), ("m5", m5)]:
        pd.DataFrame(rows).to_csv(os.path.join(E.TAB, f"e2_wp2_{name}.csv"), index=False, float_format="%.5f")
    print("done")


if __name__ == "__main__":
    main(tuple(sys.argv[1].split(",")) if len(sys.argv) > 1 else ("t1", "t2", "t3"))
