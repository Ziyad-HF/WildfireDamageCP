"""Phase 1 checks: no cell in two roles, test fire only in test, Eaton only as eaton; class counts per fold x role."""
import sys, pandas as pd
R = sys.argv[1] if len(sys.argv) > 1 else "."
S = f"{R}/data/processed/splits"
FOLDS = {1: "santa-rosa", 2: "woolsey", 3: "pinery", 4: "portugal"}
lab = pd.concat([pd.read_csv(f"{R}/data/processed/crops/index_xbd_v2.csv", usecols=["id", "fold", "label"]),
                 pd.read_csv(f"{R}/data/processed/crops/index_eaton.csv", usecols=["id", "fold", "label"])])
cells = pd.read_csv(f"{S}/cells_xbd.csv")
rows, ok = [], True
for k, tf in FOLDS.items():
    f = pd.read_csv(f"{S}/fold{k}.csv").merge(lab, on="id", how="left", validate="1:1")
    assert f.id.is_unique and f.label.notna().all()
    c = f.merge(cells[["id", "cell"]], on="id", how="inner")
    multi = c[c.role.isin(["train", "val", "calib"])].groupby("cell").role.nunique()
    chk = {"cells_in_2_roles": int((multi > 1).sum()),
           "test_fire_outside_test": int(((f.fold == tf) & (f.role != "test")).sum()),
           "non_test_fire_in_test": int(((f.fold != tf) & (f.role == "test")).sum()),
           "eaton_not_eaton_role": int(((f.fold == "eaton") != (f.role == "eaton")).sum()),
           "n_rows": len(f)}
    ok &= all(v == 0 for kk, v in chk.items() if kk != "n_rows")
    print(f"fold{k} ({tf}) checks:", chk)
    ct = pd.crosstab(f.role, f.label).reindex(index=["train", "val", "calib", "test", "eaton"],
                                              columns=["no damage", "damaged", "destroyed"]).fillna(0).astype(int)
    ct["total"] = ct.sum(axis=1)
    for role, r in ct.iterrows():
        rows.append({"fold": k, "test_fire": tf, "role": role, **r.to_dict()})
t = pd.DataFrame(rows)
t.to_csv(f"{R}/results/tables/split_counts.csv", index=False)
pd.set_option("display.width", 200); print(t.to_string(index=False))
print("ALL CHECKS PASS" if ok else "CHECK FAILURES")
