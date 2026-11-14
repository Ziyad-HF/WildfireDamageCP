"""Phase 1: build leave-one-fire-out split files per preregistration rule 3.

Grid cell = (floor(lon/0.005), floor(lat/0.005)) on WGS84 lon/lat from buildings_xbd.csv.
Role assignment (train/val/calib) is done ONCE per fire group with seed 0 and reused in every
fold where that fire is a training fire: cells shuffled with numpy default_rng(0), then assigned
in order to train until cumulative buildings >= 70%, then val until >= 80%, rest calib.
The 138 buildings with bx/by outside 0-223 are excluded from every role (rule 2).
Outputs: data/processed/splits/fold{k}.csv (id, source, event, role), cells_xbd.csv (id, fold_fire, cell).
"""
import os, sys, numpy as np, pandas as pd

R = sys.argv[1] if len(sys.argv) > 1 else "."
CELL, SEED, FR = 0.005, 0, (0.70, 0.80)
FOLDS = {1: "santa-rosa", 2: "woolsey", 3: "pinery", 4: "portugal"}

x = pd.read_csv(f"{R}/data/processed/crops/index_xbd_v2.csv")
m = pd.read_csv(f"{R}/data/metadata/buildings_xbd.csv")[["id", "lon", "lat"]]
e = pd.read_csv(f"{R}/data/processed/crops/index_eaton.csv")
x = x.merge(m, on="id", how="left", validate="1:1")
assert x[["lon", "lat"]].notna().all().all()

oob = (x.bx < 0) | (x.bx > 223) | (x.by < 0) | (x.by > 223)
print("excluded (rule 2):", int(oob.sum()), x[oob].groupby("fold").size().to_dict())
x = x[~oob].copy()
x["cell"] = (np.floor(x.lon / CELL).astype(int).astype(str) + "_" + np.floor(x.lat / CELL).astype(int).astype(str))
# cell must belong to a single fire group
cf = x.groupby("cell").fold.nunique()
assert (cf == 1).all(), f"cells spanning fire groups: {cf[cf > 1].index.tolist()[:5]}"

role_of = {}
for fire in sorted(x.fold.unique()):
    sub = x[x.fold == fire]
    sizes = sub.groupby("cell").size()
    cells = sizes.index.to_numpy()
    rng = np.random.default_rng(SEED)
    cells = cells[rng.permutation(len(cells))]
    cum = sizes.loc[cells].cumsum().to_numpy() / len(sub)
    start = np.concatenate([[0.0], cum[:-1]])  # share of buildings already assigned before this cell
    roles = np.where(start < FR[0], "train", np.where(start < FR[1], "val", "calib"))
    role_of.update(dict(zip(cells, roles)))
    print(f"{fire}: {len(cells)} cells, {len(sub)} buildings")
x["pool_role"] = x.cell.map(role_of)

out = f"{R}/data/processed/splits"
os.makedirs(out, exist_ok=True)
x[["id", "fold", "cell"]].rename(columns={"fold": "fold_fire"}).to_csv(f"{out}/cells_xbd.csv", index=False)
for k, test_fire in FOLDS.items():
    a = x[["id", "source", "event", "fold", "pool_role"]].copy()
    a["role"] = np.where(a.fold == test_fire, "test", a.pool_role)
    ea = e[["id", "source", "event"]].assign(role="eaton")
    pd.concat([a[["id", "source", "event", "role"]], ea]).to_csv(f"{out}/fold{k}.csv", index=False)
print("wrote", out)
