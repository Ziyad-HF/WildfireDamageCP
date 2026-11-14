"""Gate G4 (automated): do CAL FIRE DINS Eaton points land on buildings in the Maxar pre/post images?
Usage: python scripts/data_prep/eaton_overlay_check.py <project_root>
Outputs (in <project_root>/outputs/gates/g4/): contact sheet PNG, per-building CSV, summary TXT.
"""
import sys, os, json, glob, csv, random
import numpy as np, rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
from PIL import Image, ImageDraw

ROOT = sys.argv[1]
OUT = os.path.join(ROOT, "outputs", "gates", "g4"); os.makedirs(OUT, exist_ok=True)
MAXAR = os.path.join(ROOT, "data", "raw", "maxar_eaton_2025")
DINS = os.path.join(ROOT, "data", "raw", "dins_eaton_2025", "DINS_2025_Eaton_Public_View.geojson")
PRE, POST = ("2025-01-01", "WV03"), ("2025-01-14", "WV03")
CLS = {"No Damage": "no damage", "Affected (1-9%)": "damaged", "Minor (10-25%)": "damaged",
       "Major (26-50%)": "damaged", "Destroyed (>50%)": "destroyed"}
HALF, HALF_REG, N_PER_CLASS = 40.0, 100.0, 10   # crop half-width (m), registration window half-width (m)

def scenes(date, sat):
    out = []
    for js in glob.glob(os.path.join(MAXAR, "*", date, "*.json")):
        if json.load(open(js))["properties"].get("platform") != sat: continue
        tif = js[:-5] + "-visual.tif"
        if os.path.exists(tif): out.append(rasterio.open(tif))
    return out

def read(srcs, x, y, half):
    for s in srcs:
        b = s.bounds
        if b.left <= x - half and x + half <= b.right and b.bottom <= y - half and y + half <= b.top:
            a = s.read(window=from_bounds(x-half, y-half, x+half, y+half, s.transform), boundless=False)
            if a.shape[1] > 10 and (a.max(axis=0) > 0).mean() > 0.95:
                return np.moveaxis(a[:3], 0, -1)
    return None

def shift_m(a, b, px):
    ga, gb = a.mean(-1), b.mean(-1)
    n = min(ga.shape[0], gb.shape[0], ga.shape[1], gb.shape[1]); ga, gb = ga[:n, :n], gb[:n, :n]
    ga = (ga - ga.mean()) * np.hanning(n)[:, None] * np.hanning(n)[None]
    gb = (gb - gb.mean()) * np.hanning(n)[:, None] * np.hanning(n)[None]
    R = np.fft.fft2(ga) * np.conj(np.fft.fft2(gb)); R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real; dy, dx = np.unravel_index(r.argmax(), r.shape)
    dy = dy - n if dy > n // 2 else dy; dx = dx - n if dx > n // 2 else dx
    return float(np.hypot(dx, dy) * px), float(r.max())

pre, post = scenes(*PRE), scenes(*POST)
tr = Transformer.from_crs(4326, 32611, always_xy=True)
feats = json.load(open(DINS))["features"]
pts = []
for f in feats:
    p = f["properties"]
    if p["STRUCTURETYPE"] == "Utility Misc Structure" or p["DAMAGE"] not in CLS: continue
    x, y = tr.transform(*f["geometry"]["coordinates"][:2])
    pts.append((p["OBJECTID"], CLS[p["DAMAGE"]], p["STRUCTURETYPE"], x, y))
random.seed(0); random.shuffle(pts)
picked, rows = {"no damage": [], "damaged": [], "destroyed": []}, []
for oid, c, st, x, y in pts:
    if len(picked[c]) >= N_PER_CLASS: continue
    a, b = read(pre, x, y, HALF), read(post, x, y, HALF)
    if a is None or b is None: continue
    ra, rb = read(pre, x, y, HALF_REG), read(post, x, y, HALF_REG)
    px = pre[0].res[0]
    s, q = shift_m(ra, rb, px) if ra is not None and rb is not None else (float("nan"), 0)
    picked[c].append((oid, c, st, a, b)); rows.append([oid, c, st, round(x, 1), round(y, 1), round(s, 2), round(q, 3)])
    if all(len(v) >= N_PER_CLASS for v in picked.values()): break

T = 220
def tile(img, label):
    im = Image.fromarray(img.astype(np.uint8)).resize((T, T))
    d = ImageDraw.Draw(im); m = T // 2
    d.line([(m-10, m), (m+10, m)], fill=(255, 0, 0), width=2); d.line([(m, m-10), (m, m+10)], fill=(255, 0, 0), width=2)
    d.rectangle([0, 0, T, 14], fill=(0, 0, 0)); d.text((3, 1), label, fill=(255, 255, 255))
    return im
items = [b for c in ("no damage", "damaged", "destroyed") for b in picked[c]]
cols = 3; sheet = Image.new("RGB", (cols * 2 * T + cols * 6, ((len(items) + cols - 1) // cols) * T), "white")
for i, (oid, c, st, a, b) in enumerate(items):
    r, k = divmod(i, cols); x0 = k * (2 * T + 6)
    sheet.paste(tile(a, f"{oid} {c} PRE"), (x0, r * T)); sheet.paste(tile(b, "POST 2025-01-14"), (x0 + T, r * T))
sheet.save(os.path.join(OUT, "g4_contact_sheet.png"))
with open(os.path.join(OUT, "g4_buildings.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["objectid", "class", "structure", "utm_x", "utm_y", "pre_post_shift_m", "phasecorr_peak"]); w.writerows(rows)
sh = [r[5] for r in rows if r[5] == r[5]]
txt = (f"pre scenes {len(pre)}, post scenes {len(post)}; sampled {len(items)} buildings "
       f"({ {c: len(v) for c, v in picked.items()} }); crop {2*HALF:.0f} m\n"
       f"pre-vs-post image shift over {2*HALF_REG:.0f} m windows: median {np.median(sh):.2f} m, max {np.max(sh):.2f} m")
open(os.path.join(OUT, "g4_summary.txt"), "w").write(txt); print(txt)
