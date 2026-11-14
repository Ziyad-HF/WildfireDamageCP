"""Phase 5: temperature scaling, conformal sets, routing, cluster bootstrap (preregistration rules 6-9, D7-D13).

Inputs : results/preds/{t1,t2}_fold{k}_seed{s}.csv, data/processed/splits/cells_xbd.csv
Outputs: results/tables/p5_calibration.csv, p5_conformal.csv, p5_routing.csv, p5_routing_binary.csv,
         p5_conformal_binary.csv, p5_bootstrap_ci.csv, p5_eaton_summary.csv, p5_temperatures.json  (preregistered)
         p5_routing_amended.csv, p5_routing_binary_amended.csv (amendment A1),
         p5_conformal_posthoc.csv, p5_routing_posthoc.csv (post-hoc P1),
         p5_bootstrap_ci_A1_posthoc.csv, p5_eaton_summary_A1_posthoc.csv (A1 + P1)
Only calib is used to fit anything (T, thresholds, alpha*). Test and Eaton are evaluated once.
"""
import os, glob, json, re, numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp, softmax

PROJ = os.environ.get("WDCP_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAB = f"{PROJ}/results/tables"
ALPHA = 0.10
GRID = np.round(np.arange(0.005, 0.5001, 0.005), 3)
NB, B_BOOT = 15, 1000
METHODS = ["LAC", "APS", "Ordinal", "Mondrian"]
POSTHOC = ["APS_rand", "Ordinal_rand"]  # P1: post-hoc, not preregistered
LOGIT = ["logit_no", "logit_dmg", "logit_des"]


# ---------------- calibration ----------------
def fit_T(z, y):
    def nll(lt):
        zz = z / np.exp(lt)
        return float(np.mean(logsumexp(zz, 1) - zz[np.arange(len(y)), y]))
    r = minimize_scalar(nll, bounds=(-3, 3), method="bounded", options={"xatol": 1e-6})
    return float(np.exp(r.x))


def nll(p, y): return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, None))))
def brier(p, y): return float(np.mean(((p - np.eye(p.shape[1])[y]) ** 2).sum(1)))


def bin_idx(conf):  # 15 equal-width bins on [0,1]; bin b covers (b/15, (b+1)/15], bin 0 also includes 0
    return np.clip(np.ceil(conf * NB).astype(int) - 1, 0, NB - 1)


def ece(p, y):
    conf, pred = p.max(1), p.argmax(1); b = bin_idx(conf); e = 0.0
    for k in range(NB):
        m = b == k
        if m.any(): e += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return float(e)


# ---------------- conformal ----------------
def scores(p, method, u=None):
    """P1 (post-hoc): "APS_rand"/"Ordinal_rand" = exclusive score + U * p_y (U per building, shared across labels).
    Score s(x, y) for every candidate label y: array [n, K].
    APS / Ordinal use the mass ranked strictly before y (non-randomised APS with U = 0): the top class scores 0,
    so sets {y : s <= q} are never empty, and the same score is used for thresholds and sets."""
    if method.endswith("_rand"):
        base = method[:-5]
        return _inclusive_scores(p, base) - p + u[:, None] * p
    if method in ("APS", "Ordinal"):
        return _inclusive_scores(p, method) - p
    return _inclusive_scores(p, method)


def _inclusive_scores(p, method):
    """LAC: 1 - p_y. APS / Ordinal: mass up to and including y (exclusive score = this - p_y)."""
    if method in ("LAC", "Mondrian"):
        return 1.0 - p
    if method == "APS":
        return (p[:, None, :] * (p[:, None, :] >= p[:, :, None])).sum(2)
    if method == "Ordinal":
        assert p.shape[1] == 3
        p0, p1, p2 = p[:, 0], p[:, 1], p[:, 2]; m = p.argmax(1); S = np.ones_like(p)
        a = m == 0; S[a, 0] = p0[a]; S[a, 1] = p0[a] + p1[a]; S[a, 2] = 1.0
        c = m == 2; S[c, 2] = p2[c]; S[c, 1] = p2[c] + p1[c]; S[c, 0] = 1.0
        bm = m == 1; left = bm & (p0 >= p2); right = bm & (p0 < p2)  # tie -> lower class added first
        S[bm, 1] = p1[bm]
        S[left, 0] = p1[left] + p0[left]; S[left, 2] = 1.0
        S[right, 2] = p1[right] + p2[right]; S[right, 0] = 1.0
        return S
    raise ValueError(method)


def qhat(s, alpha):
    n = len(s); k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else float(np.sort(s)[k - 1])


def thresholds(p_cal, y_cal, method, alpha, u=None):
    S = scores(p_cal, method, u); K = p_cal.shape[1]
    if method == "Mondrian":
        return np.array([qhat(S[y_cal == c, c], alpha) for c in range(K)])
    return np.full(K, qhat(S[np.arange(len(y_cal)), y_cal], alpha))


def sets(p, method, q, u=None): return scores(p, method, u) <= q[None, :]


def routing_stats(C, y, des=2):
    size = C.sum(1); auto = size == 1; lab = C.argmax(1)
    n_des = int((y == des).sum())
    missed = int((auto & (y == des) & (lab != des)).sum())
    return {"auto_share": float(auto.mean()), "missed_destroyed_rate": missed / n_des if n_des else np.nan,
            "n_missed": missed, "n_destroyed": n_des,
            "error_among_auto": float((lab[auto] != y[auto]).mean()) if auto.any() else np.nan}


def _feasible(p_cal, y_cal, method, des, u):
    ok = []
    for a in GRID:
        C = sets(p_cal, method, thresholds(p_cal, y_cal, method, a, u), u)
        r = routing_stats(C, y_cal, des)
        if r["missed_destroyed_rate"] <= 0.05: ok.append((a, r))
    return ok


def choose_alpha(p_cal, y_cal, method, des=2, u=None):
    """Original rule 8: largest grid alpha with calib missed-destroyed <= 5%."""
    ok = _feasible(p_cal, y_cal, method, des, u)
    return ok[-1] if ok else (None, None)


def choose_alpha_amended(p_cal, y_cal, method, des=2, u=None):
    """Amendment A1: grid alpha maximising calib auto share s.t. calib missed-destroyed <= 5% (ties -> larger alpha)."""
    ok = _feasible(p_cal, y_cal, method, des, u)
    if not ok: return (None, None)
    best = max(r["auto_share"] for _, r in ok)
    return [(a, r) for a, r in ok if r["auto_share"] == best][-1]


def set_stats(C, y):
    K = C.shape[1]; cov = C[np.arange(len(y)), y]; size = C.sum(1)
    out = {"coverage": float(cov.mean()), "mean_set_size": float(size.mean()),
           "empty_share": float((size == 0).mean()), "singleton_share": float((size == 1).mean())}
    for c in range(K): out[f"cov_c{c}"] = float(cov[y == c].mean()) if (y == c).any() else np.nan
    return out


# ---------------- bootstrap (cell-level sufficient statistics) ----------------
def suff_stats(p, y, C_alpha, C_route, K=3, C_route_am=None):
    """Per-building additive columns from which every bootstrapped metric is a ratio of sums."""
    pred = p.argmax(1); conf = p.max(1); b = bin_idx(conf); cols = {"n": np.ones(len(y))}
    for c in range(K):
        cols[f"tp{c}"] = (pred == c) & (y == c); cols[f"fp{c}"] = (pred == c) & (y != c); cols[f"fn{c}"] = (pred != c) & (y == c)
        cols[f"ny{c}"] = y == c; cols[f"cov{c}"] = C_alpha[np.arange(len(y)), y] & (y == c)
    for k in range(NB):
        cols[f"bn{k}"] = b == k; cols[f"bc{k}"] = (b == k) * (pred == y); cols[f"bp{k}"] = (b == k) * conf
    cols["brier"] = ((p - np.eye(K)[y]) ** 2).sum(1)
    cols["size"] = C_alpha.sum(1)
    if C_route is not None:
        auto = C_route.sum(1) == 1; lab = C_route.argmax(1)
        cols["auto"] = auto; cols["missed"] = auto & (y == 2) & (lab != 2)
    if C_route_am is not None:
        auto = C_route_am.sum(1) == 1; lab = C_route_am.argmax(1)
        cols["auto_am"] = auto; cols["missed_am"] = auto & (y == 2) & (lab != 2)
    return pd.DataFrame({k: np.asarray(v, float) for k, v in cols.items()})


def metrics_from_sums(T, K=3):
    """T: dict of arrays (one entry per resample). Returns dict of metric arrays."""
    f1 = []
    for c in range(K):
        den = 2 * T[f"tp{c}"] + T[f"fp{c}"] + T[f"fn{c}"]
        f1.append(np.where(den > 0, 2 * T[f"tp{c}"] / np.where(den > 0, den, 1), 0.0))
    out = {"macro_f1": np.mean(f1, 0), "f1_dmg": f1[1], "f1_des": f1[2]}
    out["ece"] = sum(np.abs(T[f"bc{k}"] - T[f"bp{k}"]) for k in range(NB)) / T["n"]
    out["brier"] = T["brier"] / T["n"]
    out["coverage"] = sum(T[f"cov{c}"] for c in range(K)) / T["n"]
    for c in range(K): out[f"cov_c{c}"] = T[f"cov{c}"] / np.where(T[f"ny{c}"] > 0, T[f"ny{c}"], np.nan)
    out["mean_set_size"] = T["size"] / T["n"]
    if "auto" in T:
        out["auto_share"] = T["auto"] / T["n"]
        out["missed_destroyed_rate"] = T["missed"] / np.where(T["ny2"] > 0, T["ny2"], np.nan)
    if "auto_am" in T:
        out["auto_share_A1"] = T["auto_am"] / T["n"]
        out["missed_destroyed_rate_A1"] = T["missed_am"] / np.where(T["ny2"] > 0, T["ny2"], np.nan)
    return out


# ---------------- main ----------------
def main():
    cells = pd.read_csv(f"{PROJ}/data/processed/splits/cells_xbd.csv").set_index("id").cell
    files = sorted(glob.glob(f"{PROJ}/results/preds/t[123]_fold*_seed*.csv"))
    cal_rows, conf_rows, rout_rows, rb_rows, cb_rows, temps = [], [], [], [], [], {}
    rout_am_rows, rb_am_rows, conf_ph_rows, rout_ph_rows = [], [], [], []
    boot_store = {}  # (model, fold, method) -> list over seeds of (cell-sum DataFrame)
    for fn in files:
        model, k, s = re.search(r"(t\d)_fold(\d)_seed(\d)", fn).groups(); k, s = int(k), int(s)
        d = pd.read_csv(fn); z = d[LOGIT].to_numpy(np.float64); y = d.label.to_numpy()
        role = d.role.to_numpy(); cal = role == "calib"
        T = fit_T(z[cal], y[cal]); temps[f"{model}_fold{k}_seed{s}"] = T
        p_raw, p_ts = softmax(z, 1), softmax(z / T, 1)
        for r in ["calib", "test", "eaton"]:
            m = role == r
            cal_rows.append({"model": model, "fold": k, "seed": s, "role": r, "T": T,
                             "ece_before": ece(p_raw[m], y[m]), "ece_after": ece(p_ts[m], y[m]),
                             "brier_before": brier(p_raw[m], y[m]), "brier_after": brier(p_ts[m], y[m]),
                             "nll_before": nll(p_raw[m], y[m]), "nll_after": nll(p_ts[m], y[m])})
        test = role == "test"
        u_all = np.random.default_rng(0).uniform(size=len(d))  # P1: one U per building (post-hoc methods only)
        for meth in METHODS + POSTHOC:
            ph = meth in POSTHOC; u = u_all if ph else None
            uc = u[cal] if ph else None
            q = thresholds(p_ts[cal], y[cal], meth, ALPHA, uc)
            sel = {"original": choose_alpha(p_ts[cal], y[cal], meth, u=uc),
                   "A1": choose_alpha_amended(p_ts[cal], y[cal], meth, u=uc)}
            qs = {rule: (thresholds(p_ts[cal], y[cal], meth, a, uc) if a is not None else None) for rule, (a, _) in sel.items()}
            for r in ["test", "eaton"]:
                m = role == r; um = u[m] if ph else None
                row = {"model": model, "fold": k, "seed": s, "method": meth, "role": r, "alpha": ALPHA,
                       "q": json.dumps(np.round(q, 6).tolist()), **set_stats(sets(p_ts[m], meth, q, um), y[m])}
                (conf_ph_rows if ph else conf_rows).append({**row, "posthoc": True} if ph else row)
                for rule, (a_star, r_cal) in sel.items():
                    rr = {"model": model, "fold": k, "seed": s, "method": meth, "role": r, "alpha_star": a_star,
                          "calib_auto_share": r_cal["auto_share"] if r_cal else np.nan,
                          "calib_missed_destroyed_rate": r_cal["missed_destroyed_rate"] if r_cal else np.nan}
                    if a_star is not None:
                        rr.update(routing_stats(sets(p_ts[m], meth, qs[rule], um), y[m]))
                    else:
                        rr.update({"auto_share": 0.0, "missed_destroyed_rate": 0.0, "n_missed": 0,
                                   "n_destroyed": int((y[m] == 2).sum()), "error_among_auto": np.nan})
                    if ph: rout_ph_rows.append({**rr, "rule": rule, "posthoc": True})
                    elif rule == "original": rout_rows.append(rr)
                    else: rout_am_rows.append({**rr, "rule": "A1"})
            # bootstrap sufficient statistics on the test fire (cells)
            ut = u[test] if ph else None
            C_a = sets(p_ts[test], meth, q, ut)
            C_r = sets(p_ts[test], meth, qs["original"], ut) if qs["original"] is not None else np.zeros_like(C_a)
            C_am = sets(p_ts[test], meth, qs["A1"], ut) if qs["A1"] is not None else np.zeros_like(C_a)
            ss = suff_stats(p_ts[test], y[test], C_a, C_r, C_route_am=C_am)
            ss["cell"] = cells.reindex(d.id[test]).to_numpy()
            assert ss.cell.notna().all()
            boot_store.setdefault((model, k, meth), []).append(ss.groupby("cell").sum())
        # secondary: destroyed vs not (D13)
        pb = np.stack([1 - p_ts[:, 2], p_ts[:, 2]], 1); yb = (y == 2).astype(int)
        for meth in ["LAC", "Mondrian"]:
            q = thresholds(pb[cal], yb[cal], meth, ALPHA)
            sel = {"original": choose_alpha(pb[cal], yb[cal], meth, des=1),
                   "A1": choose_alpha_amended(pb[cal], yb[cal], meth, des=1)}
            for r in ["test", "eaton"]:
                m = role == r
                cb_rows.append({"model": model, "fold": k, "seed": s, "method": meth, "role": r, "alpha": ALPHA,
                                "ece_binary": ece(pb[m], yb[m]), **set_stats(sets(pb[m], meth, q), yb[m])})
                for rule, (a_star, r_cal) in sel.items():
                    rr = {"model": model, "fold": k, "seed": s, "method": meth, "role": r, "alpha_star": a_star,
                          "calib_auto_share": r_cal["auto_share"] if r_cal else np.nan}
                    rr.update(routing_stats(sets(pb[m], meth, thresholds(pb[cal], yb[cal], meth, a_star)), yb[m], des=1) if a_star is not None else
                              {"auto_share": 0.0, "missed_destroyed_rate": 0.0, "n_missed": 0, "n_destroyed": int(yb[m].sum()), "error_among_auto": np.nan})
                    if rule == "original": rb_rows.append(rr)
                    else: rb_am_rows.append({**rr, "rule": "A1"})
        print(f"{model} fold{k} seed{s}: T={T:.3f}", flush=True)

    pd.DataFrame(cal_rows).round(5).to_csv(f"{TAB}/p5_calibration.csv", index=False)
    pd.DataFrame(conf_rows).round(5).to_csv(f"{TAB}/p5_conformal.csv", index=False)
    pd.DataFrame(rout_rows).round(5).to_csv(f"{TAB}/p5_routing.csv", index=False)
    pd.DataFrame(cb_rows).round(5).to_csv(f"{TAB}/p5_conformal_binary.csv", index=False)
    pd.DataFrame(rb_rows).round(5).to_csv(f"{TAB}/p5_routing_binary.csv", index=False)
    json.dump(temps, open(f"{TAB}/p5_temperatures.json", "w"), indent=1)
    # amendment A1 and post-hoc P1 outputs (separate files; original files unchanged)
    pd.DataFrame(rout_am_rows).round(5).to_csv(f"{TAB}/p5_routing_amended.csv", index=False)
    pd.DataFrame(rb_am_rows).round(5).to_csv(f"{TAB}/p5_routing_binary_amended.csv", index=False)
    pd.DataFrame(conf_ph_rows).round(5).to_csv(f"{TAB}/p5_conformal_posthoc.csv", index=False)
    pd.DataFrame(rout_ph_rows).round(5).to_csv(f"{TAB}/p5_routing_posthoc.csv", index=False)

    # cluster bootstrap over test-fire cells (D12). Original methods: same rng(0) stream and order as the
    # preregistered run; post-hoc methods: separate rng(1) so the original CIs are unchanged.
    def boot(keys, rng):
        out = []
        for key in keys:
            model, k, meth = key; per_seed = boot_store[key]; idx = per_seed[0].index
            assert all(ps.index.equals(idx) for ps in per_seed)
            nc = len(idx); W = np.stack([np.bincount(rng.integers(0, nc, nc), minlength=nc) for _ in range(B_BOOT)]).astype(float)
            point, bt = [], []
            for ps in per_seed:
                A = ps.to_numpy(); cols = ps.columns
                point.append(metrics_from_sums({c: A[:, j].sum() for j, c in enumerate(cols)}))
                TB = W @ A; bt.append(metrics_from_sums({c: TB[:, j] for j, c in enumerate(cols)}))
            for met in point[0]:
                pt = np.mean([p_[met] for p_ in point]); bs = np.nanmean([b_[met] for b_ in bt], 0)
                out.append({"model": model, "fold": k, "method": meth, "metric": met, "n_seeds": len(per_seed),
                            "n_cells": nc, "point_seed_mean": pt,
                            "seed_sd": float(np.std([p_[met] for p_ in point], ddof=1)) if len(point) > 1 else np.nan,
                            "ci_lo": float(np.nanpercentile(bs, 2.5)), "ci_hi": float(np.nanpercentile(bs, 97.5))})
        return pd.DataFrame(out)
    keys = sorted(boot_store)
    ci = boot([k_ for k_ in keys if k_[2] in METHODS], np.random.default_rng(0))
    a1 = ci.metric.str.endswith("_A1")
    ci[~a1].round(5).to_csv(f"{TAB}/p5_bootstrap_ci.csv", index=False)
    ci_ph = boot([k_ for k_ in keys if k_[2] in POSTHOC], np.random.default_rng(1)).assign(posthoc=True)
    pd.concat([ci[a1].assign(posthoc=False), ci_ph]).round(5).to_csv(f"{TAB}/p5_bootstrap_ci_A1_posthoc.csv", index=False)

    # Eaton: mean +- SD across the 4 fold models (T1 seed-averaged first) (rule 9)
    def eaton_summary(specs):
        rows = []
        for name, df, keys_, mets in specs:
            e = df[df.role == "eaton"].groupby(["model"] + keys_ + ["fold"])[mets].mean().reset_index()
            for key, g in e.groupby(["model"] + keys_):
                key = key if isinstance(key, tuple) else (key,)
                for met in mets:
                    rows.append({"table": name, "model": key[0], "method": key[1] if len(key) > 1 else "",
                                 "metric": met, "mean": g[met].mean(), "sd_across_folds": g[met].std(ddof=1)})
        return pd.DataFrame(rows).round(5)
    RM = ["auto_share", "missed_destroyed_rate", "error_among_auto"]
    CM = ["coverage", "cov_c0", "cov_c1", "cov_c2", "mean_set_size"]
    eaton_summary([("calibration", pd.DataFrame(cal_rows), [], ["ece_before", "ece_after", "brier_before", "brier_after"]),
                   ("conformal", pd.DataFrame(conf_rows), ["method"], CM),
                   ("routing", pd.DataFrame(rout_rows), ["method"], RM)]).to_csv(f"{TAB}/p5_eaton_summary.csv", index=False)
    rph = pd.DataFrame(rout_ph_rows)
    eaton_summary([("routing_A1", pd.DataFrame(rout_am_rows), ["method"], RM),
                   ("conformal_posthoc", pd.DataFrame(conf_ph_rows), ["method"], CM),
                   ("routing_posthoc_original", rph[rph.rule == "original"], ["method"], RM),
                   ("routing_posthoc_A1", rph[rph.rule == "A1"], ["method"], RM)]).to_csv(f"{TAB}/p5_eaton_summary_A1_posthoc.csv", index=False)
    print("done")


if __name__ == "__main__":
    main()
