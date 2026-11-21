"""E2 WP7: 2025 Palisades Fire as a second external test, built exactly like Eaton (I14).
  python scripts/data_prep/palisades.py download   # the chosen WV03 pre/post 'visual' tiles (see maxar_palisades_pair.py)
  python scripts/data_prep/palisades.py check      # alignment gate: 30 buildings (10 per class), median shift <= 5 m
  python scripts/data_prep/palisades.py crops      # 64 m crops -> 224 px JPEG, index_palisades.csv, buildings_palisades.csv
Label mapping, exclusions (Utility Misc Structure, Inaccessible), crop size, centring and window checks are copied
from extract_crops.py / eaton_overlay_check.py (Eaton). Images: Maxar Open Data (CC BY-NC 4.0).
"""
import os, sys, json, glob, csv, random, urllib.request, urllib.parse
import numpy as np, rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "raw", "maxar_palisades_2025")
DINS = os.path.join(ROOT, "data", "raw", "dins_palisades_2025", "DINS_2025_Palisades_Public_View.geojson")
CROPS = os.path.join(ROOT, "data", "processed", "crops")
BASE = "https://maxar-opendata.s3.amazonaws.com/events/WildFires-LosAngeles-Jan-2025/ard/11/"
CH = json.load(open(os.path.join(RAW, "pair_choice.json")))
PRE, POST = CH["pre"], CH["post"]
MAP = {"No Damage": "no damage", "Affected (1-9%)": "damaged", "Minor (10-25%)": "damaged",
       "Major (26-50%)": "damaged", "Destroyed (>50%)": "destroyed"}
GROUND_M, OUT_PX, Q = 64.0, 224, 95


def jsons(date):
    return [js for js in glob.glob(os.path.join(RAW, "*", date, "*.json")) if json.load(open(js))["properties"].get("platform") == "WV03"]


def scenes(date):
    return [rasterio.open(js[:-5] + "-visual.tif") for js in jsons(date) if os.path.exists(js[:-5] + "-visual.tif")]


def read(srcs, x, y, h):  # identical to Eaton
    for s in srcs:
        b = s.bounds
        if b.left <= x - h and x + h <= b.right and b.bottom <= y - h and y + h <= b.top:
            a = s.read(window=from_bounds(x - h, y - h, x + h, y + h, s.transform))
            if a.shape[1] > 10 and (a.max(axis=0) > 0).mean() > 0.95:
                return np.moveaxis(a[:3], 0, -1)
    return None


def points():
    tr = Transformer.from_crs(4326, 32611, always_xy=True); out = []
    for f in json.load(open(DINS))["features"]:
        p = f["properties"]
        if p.get("STRUCTURETYPE") == "Utility Misc Structure" or p.get("DAMAGE") not in MAP or not f.get("geometry"): continue
        lon, lat = f["geometry"]["coordinates"][:2]; x, y = tr.transform(lon, lat)
        out.append((f"pal{p['OBJECTID']}", MAP[p["DAMAGE"]], p["DAMAGE"], p.get("STRUCTURETYPE"), lon, lat, x, y))
    return out


def download():
    tiles = set(CH["pre_tiles"])
    for d in (PRE, POST):
        for js in jsons(d):
            t = js.split(os.sep)[-3]
            if t not in tiles: continue
            dst = js[:-5] + "-visual.tif"
            if os.path.exists(dst): continue
            rel = os.path.relpath(dst, RAW).replace(os.sep, "/")
            urllib.request.urlretrieve(BASE + urllib.parse.quote(rel), dst + ".part"); os.replace(dst + ".part", dst)
            print("downloaded", rel, round(os.path.getsize(dst) / 1e6), "MB", flush=True)


def shift_m(a, b, px):  # identical to Eaton
    ga, gb = a.mean(-1), b.mean(-1)
    n = min(ga.shape[0], gb.shape[0], ga.shape[1], gb.shape[1]); ga, gb = ga[:n, :n], gb[:n, :n]
    ga = (ga - ga.mean()) * np.hanning(n)[:, None] * np.hanning(n)[None]
    gb = (gb - gb.mean()) * np.hanning(n)[:, None] * np.hanning(n)[None]
    R = np.fft.fft2(ga) * np.conj(np.fft.fft2(gb)); R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real; dy, dx = np.unravel_index(r.argmax(), r.shape)
    dy = dy - n if dy > n // 2 else dy; dx = dx - n if dx > n // 2 else dx
    return float(np.hypot(dx, dy) * px), float(r.max())


def check():
    pre, post = scenes(PRE), scenes(POST); pts = points(); random.seed(0); random.shuffle(pts)
    picked = {"no damage": 0, "damaged": 0, "destroyed": 0}; rows = []
    for bid, c, orig, st, lon, lat, x, y in pts:
        if picked[c] >= 10: continue
        if read(pre, x, y, 40.0) is None or read(post, x, y, 40.0) is None: continue
        ra, rb = read(pre, x, y, 100.0), read(post, x, y, 100.0)
        s, q = shift_m(ra, rb, pre[0].res[0]) if ra is not None and rb is not None else (float("nan"), 0)
        picked[c] += 1; rows.append([bid, c, round(s, 2), round(q, 3)])
        if all(v >= 10 for v in picked.values()): break
    sh = [r[2] for r in rows if r[2] == r[2]]
    out = os.path.join(ROOT, "outputs", "gates", "palisades"); os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "alignment_buildings.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "class", "pre_post_shift_m", "phasecorr_peak"]); w.writerows(rows)
    txt = (f"Palisades alignment: pre {PRE} ({len(pre)} WV03 scenes), post {POST} ({len(post)}); sampled {len(rows)} buildings {picked}; "
           f"pre-vs-post shift over 200 m windows: median {np.median(sh):.2f} m, max {np.max(sh):.2f} m; gate (median <= 5 m): "
           f"{'PASS' if np.median(sh) <= 5 else 'FAIL'}")
    open(os.path.join(out, "alignment_summary.txt"), "w").write(txt); print(txt)


def crops():
    pre, post = scenes(PRE), scenes(POST); od = os.path.join(CROPS, "palisades", "palisades-fire"); os.makedirs(od, exist_ok=True)
    rows, meta, skipped = [], [], 0
    for bid, c, orig, st, lon, lat, x, y in points():
        a, b = read(pre, x, y, GROUND_M / 2), read(post, x, y, GROUND_M / 2)
        if a is None or b is None: skipped += 1; continue
        pa, pb = os.path.join(od, f"{bid}_pre.jpg"), os.path.join(od, f"{bid}_post.jpg")
        for arr, pth in ((a, pa), (b, pb)):
            Image.fromarray(np.ascontiguousarray(arr[..., :3]).astype(np.uint8)).resize((OUT_PX, OUT_PX), Image.BILINEAR).save(pth, quality=Q)
        rows.append(["palisades", "palisades", "palisades-fire", bid, c, orig, os.path.relpath(pa, CROPS), os.path.relpath(pb, CROPS), OUT_PX // 2, OUT_PX // 2])
        meta.append([bid, lon, lat, orig, st])
    with open(os.path.join(CROPS, "index_palisades.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["source", "fold", "event", "id", "label", "orig_label", "pre", "post", "bx", "by"]); w.writerows(rows)
    md = os.path.join(ROOT, "data", "metadata"); os.makedirs(md, exist_ok=True)
    with open(os.path.join(md, "buildings_palisades.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "lon", "lat", "damage", "structure_type"]); w.writerows(meta)
    lab = [r[4] for r in rows]
    print(f"palisades crops: {len(rows)} buildings, {skipped} outside the pair footprint; classes",
          {c: lab.count(c) for c in ("no damage", "damaged", "destroyed")})


if __name__ == "__main__":
    {"download": download, "check": check, "crops": crops}[sys.argv[1]]()
