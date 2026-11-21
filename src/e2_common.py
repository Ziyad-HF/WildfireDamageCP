"""E2 shared helpers (added analysis E2, see configs/preregistration.md, implementation details I1-I14).

load_run(file)          -> dict with calibrated probabilities (Phase 5 temperature), labels, roles, ids, cells
task_probs(p, task)     -> probabilities for the 3-class task or the destroyed-vs-not task (I1)
pick_cutoff(...)        -> A1-style cut-off on a confidence score (I3)
cut_route(...)          -> routing stats for a cut-off rule
cell_bootstrap(...)     -> cluster bootstrap over grid cells (I5 / D12)
"""
import os, re, sys, glob
import numpy as np, pandas as pd
from scipy.special import softmax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import phase5 as P  # noqa: E402

PRED = os.path.join(ROOT, "results", "preds")
TAB = os.path.join(ROOT, "results", "tables")
FIRE = {1: "Santa Rosa", 2: "Woolsey", 3: "Pinery", 4: "Portugal", "eaton": "Eaton"}
LIMITS = [0.02, 0.05, 0.10]
_CELLS = None


def cell_map():
    """Grid cell per building id: xBD from cells_xbd.csv, Eaton from lon/lat (D1, as E1)."""
    global _CELLS
    if _CELLS is None:
        cx = pd.read_csv(os.path.join(ROOT, "data/processed/splits/cells_xbd.csv")).set_index("id").cell
        e = pd.read_csv(os.path.join(ROOT, "data/metadata/buildings_eaton.csv"))
        ce = pd.Series((np.floor(e.lon / 0.005).astype(int).astype(str) + "_" +
                        np.floor(e.lat / 0.005).astype(int).astype(str)).values, index=e.id)
        _CELLS = pd.concat([cx, ce])
    return _CELLS


def run_files(models=("t1", "t2", "t3")):
    out = []
    for fn in sorted(glob.glob(os.path.join(PRED, "t*_fold*_seed*.csv"))):
        m = re.search(r"/(t\d)_fold(\d)_seed(\d)\.csv$", fn)
        if m and m.group(1) in models:
            out.append((m.group(1), int(m.group(2)), int(m.group(3)), fn))
    return out


def load_run(fn):
    d = pd.read_csv(fn)
    z = d[P.LOGIT].to_numpy(np.float64); y = d.label.to_numpy(); role = d.role.to_numpy()
    cal = role == "calib"; T = P.fit_T(z[cal], y[cal])
    return {"id": d.id.to_numpy(), "role": role, "y": y, "z": z / T, "p": softmax(z / T, 1), "T": T,
            "cell": cell_map().reindex(d.id).to_numpy(), "u": np.random.default_rng(0).uniform(size=len(d))}


def task_probs(p, y, task):
    """I1: 3-class as is; binary = [1 - p_des, p_des], label 1 = destroyed. Returns probs, labels, destroyed index."""
    if task == "3class":
        return p, y, 2
    return np.stack([1 - p[:, 2], p[:, 2]], 1), (y == 2).astype(int), 1


# ---------------- cut-off rules (I3) ----------------
def score(p, kind):
    s = np.sort(p, 1)[:, ::-1]
    if kind == "B1": return s[:, 0]
    if kind == "B2": return s[:, 0] - s[:, 1]
    if kind == "B3": return (p * np.log(np.clip(p, 1e-12, None))).sum(1)  # minus entropy
    raise ValueError(kind)


def cut_stats(sc, lab, y, t, des, w=None):
    """Auto-label when sc >= t with label lab. Returns auto share, missed-destroyed rate, error among auto."""
    w = np.ones(len(y)) if w is None else w
    auto = sc >= t; isd = y == des
    nd = w[isd].sum()
    missed = (w * (auto & isd & (lab != des))).sum()
    return {"auto_share": float((w * auto).sum() / w.sum()), "missed_destroyed_rate": float(missed / nd) if nd > 0 else 0.0,
            "n_missed": int((auto & isd & (lab != des)).sum()), "n_destroyed": int(isd.sum()),
            "error_among_auto": float((lab[auto] != y[auto]).mean()) if auto.any() else np.nan}


def candidates(sc_fit):
    f = sc_fit[np.isfinite(sc_fit)]
    if len(f) == 0: return np.array([np.inf])
    return np.unique(np.append(np.quantile(f, np.arange(200) / 200, method="linear"), np.inf))


def pick_cutoff(sc, lab, y, des, limit, w=None, cand=None):
    """I3 A1 rule: max calib auto share s.t. calib missed <= limit (ties -> smaller t). inf = route all.
    Also returns the original-rule-8 analogue (most permissive feasible = smallest feasible t)."""
    cand = candidates(sc) if cand is None else cand
    best, best_auto, smallest = np.inf, -1.0, np.inf
    for t in cand:  # ascending
        r = cut_stats(sc, lab, y, t, des, w)
        if r["missed_destroyed_rate"] <= limit + 1e-12:
            smallest = min(smallest, t)
            if r["auto_share"] > best_auto + 1e-15:
                best, best_auto = t, r["auto_share"]
    return {"A1": best, "orig": smallest}


# ---------------- conformal (C1, reusing Phase 5) ----------------
def conformal_route(p_cal, y_cal, p_tgt, y_tgt, meth, rule, des, u_cal=None, u_tgt=None, limit=0.05):
    ok = [(a, r) for a, r in _feasible_lim(p_cal, y_cal, meth, des, u_cal, limit)]
    if not ok:
        return None, None, {"auto_share": 0.0, "missed_destroyed_rate": 0.0, "n_missed": 0,
                            "n_destroyed": int((y_tgt == des).sum()), "error_among_auto": np.nan}
    if rule == "orig":
        a, rc = ok[-1]
    else:
        best = max(r["auto_share"] for _, r in ok); a, rc = [(a, r) for a, r in ok if r["auto_share"] == best][-1]
    q = P.thresholds(p_cal, y_cal, meth, a, u_cal)
    return a, rc, P.routing_stats(P.sets(p_tgt, meth, q, u_tgt), y_tgt, des)


def _feasible_lim(p_cal, y_cal, meth, des, u, limit):
    out = []
    for a in P.GRID:
        r = P.routing_stats(P.sets(p_cal, meth, P.thresholds(p_cal, y_cal, meth, a, u), u), y_cal, des)
        if r["missed_destroyed_rate"] <= limit: out.append((a, r))
    return out


# ---------------- bootstrap (I5) ----------------
def boot_weights(cells, B=1000, seed=0):
    uc, inv = np.unique(cells.astype(str), return_inverse=True)
    rng = np.random.default_rng(seed)
    W = np.stack([np.bincount(rng.integers(0, len(uc), len(uc)), minlength=len(uc)) for _ in range(B)]).astype(float)
    return uc, inv, W


def ratio_ci(num_list, den_list, inv, W):
    """num/den per building, possibly one array per seed; metric = seed mean of sum(num)/sum(den) per resample."""
    vals = []
    for num, den in zip(num_list, den_list):
        cn = np.bincount(inv, weights=num, minlength=W.shape[1]); cd = np.bincount(inv, weights=den, minlength=W.shape[1])
        with np.errstate(invalid="ignore", divide="ignore"):
            vals.append((W @ cn) / (W @ cd))
    b = np.nanmean(np.stack(vals), 0)
    return float(np.nanpercentile(b, 2.5)), float(np.nanpercentile(b, 97.5))
