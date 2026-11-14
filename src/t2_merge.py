"""Merge T2 chunks and write per-fold prediction files (val, calib, test, eaton roles; T2 deterministic -> seed0)."""
import glob, pandas as pd, numpy as np
from data import load_fold, PROJ
P = f"{PROJ}/results/preds"
raw = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{P}/t2_raw/chunk*.csv"))])
assert raw.id.is_unique and len(raw) == 83079, len(raw)
assert np.allclose(raw[["p_no", "p_dmg", "p_des"]].sum(1), 1, atol=1e-5)
print("abc_mass min/median:", raw.abc_mass.min(), raw.abc_mass.median())
COLS = ["id", "source", "role", "label", "logit_no", "logit_dmg", "logit_des", "p_no", "p_dmg", "p_des"]
for k in range(1, 5):
    f = load_fold(k).query("role != 'train'").merge(raw, on="id", how="left", validate="1:1")
    assert f.p_no.notna().all()
    f["label"] = f.y.astype(int)
    f[COLS].to_csv(f"{P}/t2_fold{k}_seed0.csv", index=False)
    print(f"fold{k}:", f.role.value_counts().to_dict())
