"""E2 safety check (WP0): e2_common must reproduce the published Phase 5 APS-under-A1 routing
(results/tables/p5_routing_amended.csv) for all 28 runs, test and Eaton, to 4 decimals. Exits 1 on any mismatch."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
import numpy as np, pandas as pd
import e2_common as E

ref = pd.read_csv(os.path.join(E.TAB, "p5_routing_amended.csv"))
ref = ref[ref.method.isin(["APS", "Mondrian", "LAC"])]
bad, n = [], 0
for model, k, s, fn in E.run_files():
    r = E.load_run(fn); cal = r["role"] == "calib"
    for meth in ["APS", "Mondrian", "LAC"]:
        for role in ["test", "eaton"]:
            m = r["role"] == role
            a, _, st = E.conformal_route(r["p"][cal], r["y"][cal], r["p"][m], r["y"][m], meth, "A1", 2)
            row = ref[(ref.model == model) & (ref.fold == k) & (ref.seed == s) & (ref.method == meth) & (ref.role == role)].iloc[0]
            n += 1
            for key, val in [("alpha_star", a), ("auto_share", st["auto_share"]), ("missed_destroyed_rate", st["missed_destroyed_rate"])]:
                if abs(round(float(val), 4) - round(float(row[key]), 4)) > 1e-4 + 1e-9:
                    bad.append((model, k, s, meth, role, key, val, row[key]))
print(f"compared {n} run x method x target rows")
print("MISMATCHES:" if bad else "ALL MATCH (4 decimals)", bad[:10])
sys.exit(1 if bad else 0)
