import os, glob, json, re, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAB = {"no damage": 0, "damaged": 1, "destroyed": 2}
idx = pd.concat([pd.read_csv(f"{R}/data/processed/crops/index_xbd_v2.csv", usecols=["id", "label"]),
                 pd.read_csv(f"{R}/data/processed/crops/index_eaton.csv", usecols=["id", "label"])]).set_index("id").label.map(LAB)
def mf1(y, p):
    f = []
    for c in range(3):
        tp = ((p == c) & (y == c)).sum(); fp = ((p == c) & (y != c)).sum(); fn = ((p != c) & (y == c)).sum()
        f.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return np.mean(f), f
acc = pd.read_csv(f"{R}/results/tables/acc_runs.csv")
problems, t2vals, eat = [], {}, {}
for fn in sorted(glob.glob(f"{R}/results/preds/t[123]_fold*_seed*.csv")):
    m, k, s = re.search(r"(t\d)_fold(\d)_seed(\d)", fn).groups(); k, s = int(k), int(s)
    d = pd.read_csv(fn); sp = pd.read_csv(f"{R}/data/processed/splits/fold{k}.csv")
    exp = sp[sp.role != "train"].set_index("id").role
    chk = {
        "ids_unique": d.id.is_unique,
        "same_id_set_as_split_nontrain": set(d.id) == set(exp.index),
        "roles_match_split": (d.set_index("id").role == exp.reindex(d.id).values).all(),
        "no_train_ids": not d.id.isin(sp[sp.role == "train"].id).any(),
        "labels_match_index": (d.label.values == idx.reindex(d.id).values).all(),
        "no_nan": not d.isna().any().any(),
        "p_equals_softmax_logits": np.allclose(np.exp(d[["logit_no","logit_dmg","logit_des"]].values - d[["logit_no","logit_dmg","logit_des"]].values.max(1, keepdims=True)) /
                                               np.exp(d[["logit_no","logit_dmg","logit_des"]].values - d[["logit_no","logit_dmg","logit_des"]].values.max(1, keepdims=True)).sum(1, keepdims=True),
                                               d[["p_no","p_dmg","p_des"]].values, atol=1e-5),
        "logits_not_quantised": d.logit_no.nunique() > 0.95 * len(d)}
    bad = [c for c, v in chk.items() if not v]
    if bad: problems.append((fn.split("/")[-1], bad))
    pred = d[["p_no","p_dmg","p_des"]].values.argmax(1)
    for role in ["val", "test", "eaton"]:
        msk = (d.role == role).values; v, pc = mf1(d.label.values[msk], pred[msk])
        ref = acc[(acc.model == m) & (acc.fold == k) & (acc.seed == s) & (acc.role == role)].macro_f1.item()
        if abs(v - ref) > 6e-5: problems.append((fn, role, "macroF1 mismatch", v, ref))
        if role == "eaton": eat.setdefault(m, {}).setdefault(k, []).append(v)
    if m == "t2": t2vals[k] = d.set_index("id")[["logit_no","logit_dmg","logit_des"]]
# T2 deterministic: same logits for the same building in every fold file
base = t2vals[1]
for k in (2, 3, 4):
    common = base.index.intersection(t2vals[k].index)
    if not np.array_equal(base.loc[common].values, t2vals[k].loc[common].values): problems.append(("t2 fold", k, "differs from fold1"))
# T1 checkpoint selection: best epoch = first argmax of val macro-F1; stop after 4 non-improving epochs (or epoch 20)
for fn in sorted(glob.glob(f"{R}/results/t1_logs/*.json")):
    j = json.load(open(fn)); v = [h["val_macro_f1"] for h in j["history"]]
    be = int(np.argmax(v)) + 1; ok_stop = len(v) == 20 or len(v) - be == 4
    if be != j["best_epoch"] or not ok_stop or j["gpu"] != "NVIDIA H200": problems.append((j["tag"], be, j["best_epoch"], len(v), j["gpu"]))
# T3 checkpoint selection: best step = first argmax of val macro-F1 over checks; a run ends early only after 2 non-improving checks
for fn in sorted(glob.glob(f"{R}/results/t3_logs/*.json")):
    j = json.load(open(fn)); v = [h["val_macro_f1"] for h in j["history"]]; st = [h["step"] for h in j["history"]]
    bi = int(np.argmax(v)); after = len(v) - 1 - bi
    ok_stop = after == 2 or (after < 2 and abs(j["steps_run"] / (j["best_step"] / j["best_epoch"]) - 3) < 0.01)
    if st[bi] != j["best_step"] or not ok_stop or j["gpu"] != "NVIDIA H200": problems.append((j["tag"], st[bi], j["best_step"], len(v), j["gpu"]))
for m in eat:
    per_fold = [np.mean(v) for v in eat[m].values()]
    print(f"{m} Eaton macro-F1 per fold model {np.round(per_fold, 3).tolist()} -> {np.mean(per_fold):.3f} ± {np.std(per_fold, ddof=1):.3f}")
print("files checked:", len(glob.glob(f"{R}/results/preds/t[123]_fold*_seed*.csv")), "| T1 logs:", len(glob.glob(f"{R}/results/t1_logs/*.json")), "| T3 logs:", len(glob.glob(f"{R}/results/t3_logs/*.json")))
print("PROBLEMS:" if problems else "NO PROBLEMS FOUND", problems)
