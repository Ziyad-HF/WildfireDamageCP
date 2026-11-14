"""Gate G2: building-centred pre/post crops on a common grid (64 m ground size -> 224 px JPEG).
  python scripts/data_prep/extract_crops.py eaton <project_root> [--budget SECONDS]
  python scripts/data_prep/extract_crops.py xbd   <project_root>
Output: <root>/data/processed/crops/<source>/<event>/<id>_{pre,post}.jpg and <root>/data/processed/crops/index_<source>.csv (xBD: index_xbd_v2.csv)\nbx, by = building centre in the 224 px crop (xBD windows are shifted inside the tile, not padded).
Classes: no damage / damaged / destroyed (xBD minor+major and DINS Affected/Minor/Major -> damaged;
xBD un-classified and DINS Inaccessible are skipped). Re-running skips crops that already exist.
"""
import sys, os, io, json, csv, glob, re, time, tarfile, math
import numpy as np, rasterio
from rasterio.io import MemoryFile
from rasterio.windows import from_bounds
from PIL import Image

GROUND_M, OUT_PX, Q = 64.0, 224, 95
mode, ROOT = sys.argv[1], sys.argv[2]
BUDGET = float(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 1e9
T0 = time.time()
CROPS = os.path.join(ROOT, "data", "processed", "crops")

def save(arr, path):
    Image.fromarray(np.ascontiguousarray(arr[..., :3]).astype(np.uint8)).resize((OUT_PX, OUT_PX), Image.BILINEAR).save(path, quality=Q)

def index_writer(source):
    p = os.path.join(CROPS, f"index_{source}_v2.csv" if source == "xbd" else f"index_{source}.csv"); new = not os.path.exists(p)
    os.makedirs(CROPS, exist_ok=True)
    f = open(p, "a", newline=""); w = csv.writer(f)
    if new: w.writerow(["source", "fold", "event", "id", "label", "orig_label", "pre", "post", "bx", "by"])
    done = set()
    if not new:
        for r in csv.DictReader(open(p)): done.add(r["id"])
    return f, w, done

if mode == "eaton":
    from pyproj import Transformer
    MAP = {"No Damage": "no damage", "Affected (1-9%)": "damaged", "Minor (10-25%)": "damaged",
           "Major (26-50%)": "damaged", "Destroyed (>50%)": "destroyed"}
    def scenes(date, sat):
        out = []
        for js in glob.glob(os.path.join(ROOT, "data", "raw", "maxar_eaton_2025", "*", date, "*.json")):
            if json.load(open(js))["properties"].get("platform") == sat and os.path.exists(js[:-5] + "-visual.tif"):
                out.append(rasterio.open(js[:-5] + "-visual.tif"))
        return out
    def read(srcs, x, y, h):
        for s in srcs:
            b = s.bounds
            if b.left <= x-h and x+h <= b.right and b.bottom <= y-h and y+h <= b.top:
                a = s.read(window=from_bounds(x-h, y-h, x+h, y+h, s.transform))
                if a.shape[1] > 10 and (a.max(axis=0) > 0).mean() > 0.95:
                    return np.moveaxis(a[:3], 0, -1)
        return None
    pre, post = scenes("2025-01-01", "WV03"), scenes("2025-01-14", "WV03")
    tr = Transformer.from_crs(4326, 32611, always_xy=True)
    f, w, done = index_writer("eaton"); od = os.path.join(CROPS, "eaton", "eaton-fire"); os.makedirs(od, exist_ok=True)
    feats = json.load(open(os.path.join(ROOT, "data", "raw", "dins_eaton_2025", "DINS_2025_Eaton_Public_View.geojson")))["features"]
    n = skipped = 0
    for ft in feats:
        p = ft["properties"]; bid = f"dins{p['OBJECTID']}"
        if p["STRUCTURETYPE"] == "Utility Misc Structure" or p["DAMAGE"] not in MAP or bid in done: continue
        if time.time() - T0 > BUDGET: print("budget reached; re-run to continue"); break
        x, y = tr.transform(*ft["geometry"]["coordinates"][:2])
        a, b = read(pre, x, y, GROUND_M/2), read(post, x, y, GROUND_M/2)
        if a is None or b is None:
            skipped += 1; done.add(bid); continue   # outside the WV03 pair footprint
        pa, pb = os.path.join(od, f"{bid}_pre.jpg"), os.path.join(od, f"{bid}_post.jpg")
        save(a, pa); save(b, pb)
        w.writerow(["eaton", "eaton", "eaton-fire", bid, MAP[p["DAMAGE"]], p["DAMAGE"], os.path.relpath(pa, CROPS), os.path.relpath(pb, CROPS), OUT_PX // 2, OUT_PX // 2])
        n += 1; done.add(bid)
    f.close(); print(f"eaton: wrote {n} buildings this run, {skipped} outside footprint, {time.time()-T0:.0f}s")

elif mode == "xbd":
    MAP = {"no-damage": "no damage", "minor-damage": "damaged", "major-damage": "damaged", "destroyed": "destroyed"}
    FOLD = {"socal-fire": "woolsey", "woolsey-fire": "woolsey", "santa-rosa-wildfire": "santa-rosa",
            "pinery-bushfire": "pinery", "portugal-wildfire": "portugal"}
    lab = {}
    for p in glob.glob(os.path.join(ROOT, "data", "raw", "xbd_labels_post", "*_post_disaster.json")):
        split, name = os.path.basename(p).split("__", 1); ev = name.split("_")[0]
        if ev not in FOLD: continue
        blds = []
        for ft in json.load(open(p))["features"]["xy"]:
            st = ft["properties"].get("subtype")
            if st not in MAP: continue
            xy = np.array(re.findall(r"(-?[\d.]+) (-?[\d.]+)", ft["wkt"]), float)
            blds.append((ft["properties"]["uid"], st, xy[:, 0].mean(), xy[:, 1].mean()))
        lab[(split, name.replace("_post_disaster.json", ""))] = blds
    f, w, done = index_writer("xbd")
    XDIR = os.path.join(ROOT, "data", "raw", "xbd_archive")
    parts = sorted((p for p in os.listdir(XDIR) if p[-7:-1] == "part-a"), key=lambda s: s[-2:])
    class Chain(io.RawIOBase):
        def __init__(s, ps): s.ps, s.i, s.f = ps, 0, None
        def readable(s): return True
        def readinto(s, b):
            while s.i < len(s.ps):
                if s.f is None: s.f = open(s.ps[s.i], "rb")
                k = s.f.readinto(b)
                if k: return k
                s.f.close(); s.f = None; s.i += 1
            return 0
    stream = io.BufferedReader(Chain([os.path.join(XDIR, p) for p in parts]), 16 * 2**20)
    seen = {}; n = 0
    with tarfile.open(fileobj=stream, mode="r|gz") as tar:
        for m in tar:
            if not (m.isfile() and m.name.endswith(".tif") and "/images/" in m.name): continue
            split = m.name.split("/")[1]; base = os.path.basename(m.name)[:-4]
            key = (split, base.replace("_pre_disaster", "").replace("_post_disaster", ""))
            if key not in lab or not lab[key]: continue
            phase = "pre" if base.endswith("_pre_disaster") else "post"
            with MemoryFile(tar.extractfile(m).read()) as mf, mf.open() as s:
                img = np.moveaxis(s.read()[:3], 0, -1); t = s.transform; crs = s.crs
            if crs and crs.is_geographic:
                lat = t.f + t.e * img.shape[0] / 2
                px_m = abs(t.a) * 111320 * math.cos(math.radians(lat))
            else:
                px_m = abs(t.a)
            half = max(8, int(round(GROUND_M / 2 / px_m)))
            H, W = img.shape[:2]; S = 2 * half
            if H < S or W < S:
                img = np.pad(img, ((0, max(0, S - H)), (0, max(0, S - W)), (0, 0))); H, W = img.shape[:2]
            ev = key[1].split("_")[0]; od = os.path.join(CROPS, "xbd", ev); os.makedirs(od, exist_ok=True)
            for uid, st, cx, cy in lab[key]:
                bid = f"{split}_{uid}"
                # shift the window inside the image instead of padding; record where the building sits
                x0 = int(min(max(cx - half, 0), W - S)); y0 = int(min(max(cy - half, 0), H - S))
                c = img[y0:y0 + S, x0:x0 + S]
                bx, by = round((cx - x0) / S * OUT_PX), round((cy - y0) / S * OUT_PX)
                save(c, os.path.join(od, f"{bid}_{phase}.jpg"))
                seen.setdefault(bid, set()).add(phase)
                if seen[bid] == {"pre", "post"} and bid not in done:
                    w.writerow(["xbd", FOLD[ev], ev, bid, MAP[st], st, f"xbd/{ev}/{bid}_pre.jpg", f"xbd/{ev}/{bid}_post.jpg", bx, by])
                    done.add(bid); n += 1
            if n and n % 5000 == 0: print(f"{n} buildings, {time.time()-T0:.0f}s")
    f.close(); print(f"xbd: indexed {n} buildings in {time.time()-T0:.0f}s")
