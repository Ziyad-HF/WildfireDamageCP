"""WP7 (E2, I14): choose the Maxar WorldView-3 pre/post pair for the 2025 Palisades Fire before any prediction.
Downloads only the per-acquisition JSON metadata of the LA fires collection, intersects footprints with the
CAL FIRE DINS Palisades points (locations only, no labels), and picks one pre date (before 2025-01-07) and one
post date (after) of platform WV03 that cover the most structures; ties -> lower mean cloud cover -> closer to the fire.
Output: data/raw/maxar_palisades_2025/<tile>/<date>/*.json and data/raw/maxar_palisades_2025/pair_choice.json
"""
import os, re, json, urllib.request, urllib.parse, itertools, collections
import numpy as np
from shapely.geometry import shape, Point
from shapely.prepared import prep
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = "https://maxar-opendata.s3.amazonaws.com"; EVENT = "events/WildFires-LosAngeles-Jan-2025/ard/11/"
OUT = os.path.join(ROOT, "data", "raw", "maxar_palisades_2025")
FIRE = "2025-01-07"

def list_keys(prefix, delim=False):
    keys, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix}
        if delim: q["delimiter"] = "/"
        if token: q["continuation-token"] = token
        xml = urllib.request.urlopen(BASE + "/?" + urllib.parse.urlencode(q), timeout=60).read().decode()
        keys += re.findall(r"<Prefix>([^<]+)</Prefix>" if delim else r"<Key>([^<]+)</Key>", xml)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not m: return [k for k in keys if k != prefix]
        token = m.group(1)

feats = json.load(open(os.path.join(ROOT, "data/raw/dins_palisades_2025/DINS_2025_Palisades_Public_View.geojson")))["features"]
pts = [Point(f["geometry"]["coordinates"][:2]) for f in feats if f.get("geometry") and f["properties"].get("STRUCTURETYPE") != "Utility Misc Structure"]
lon = np.array([p.x for p in pts]); lat = np.array([p.y for p in pts])
bb = (lon.min() - 0.01, lat.min() - 0.01, lon.max() + 0.01, lat.max() + 0.01)
acq = []
for tile in list_keys(EVENT, delim=True):
    for k in [k for k in list_keys(tile) if k.endswith(".json")]:
        rel = k[len(EVENT):]; dst = os.path.join(OUT, *rel.split("/"))
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True); urllib.request.urlretrieve(BASE + "/" + urllib.parse.quote(k), dst)
        js = json.load(open(dst)); g = shape(js["geometry"]); x0, y0, x1, y1 = g.bounds
        if x1 < bb[0] or x0 > bb[2] or y1 < bb[1] or y0 > bb[3]:
            continue
        pr = js["properties"]
        acq.append({"tile": rel.split("/")[0], "date": rel.split("/")[1], "file": rel, "platform": pr.get("platform"),
                    "cloud": pr.get("eo:cloud_cover"), "datetime": pr.get("datetime"), "geom": g,
                    "off_nadir": pr.get("view:off_nadir")})
wv3 = [a for a in acq if a["platform"] == "WV03"]
print("acquisitions over the bbox:", len(acq), "WV03:", len(wv3))
cover = {}
for d, grp in itertools.groupby(sorted(wv3, key=lambda a: a["date"]), key=lambda a: a["date"]):
    grp = list(grp); m = np.zeros(len(pts), bool)
    for a in grp:
        pg = prep(a["geom"]); m |= np.array([pg.contains(p) for p in pts])
    cover[d] = (m, np.mean([a["cloud"] or 0 for a in grp]), [a["tile"] for a in grp], np.mean([a["off_nadir"] or np.nan for a in grp]))
    print(d, "tiles", len(grp), "covers", int(m.sum()), "of", len(pts), "mean cloud", round(cover[d][1], 2), "off-nadir", round(cover[d][3], 1))
pre = [d for d in cover if d < FIRE]; post = [d for d in cover if d > FIRE]
best = max(((a, b) for a in pre for b in post),
           key=lambda ab: ((cover[ab[0]][0] & cover[ab[1]][0]).sum(), -(cover[ab[0]][1] + cover[ab[1]][1]),
                           -(abs((np.datetime64(ab[0]) - np.datetime64(FIRE)).astype(int)) + abs((np.datetime64(ab[1]) - np.datetime64(FIRE)).astype(int)))))
both = cover[best[0]][0] & cover[best[1]][0]
choice = {"pre": best[0], "post": best[1], "platform": "WV03", "structures_covered_by_both": int(both.sum()), "structures_non_shed": len(pts),
          "pre_tiles": sorted(set(cover[best[0]][2])), "post_tiles": sorted(set(cover[best[1]][2])),
          "pre_cloud": cover[best[0]][1], "post_cloud": cover[best[1]][1], "pre_off_nadir": cover[best[0]][3], "post_off_nadir": cover[best[1]][3],
          "rule": "WV03; max structures covered by both; ties -> lower mean cloud -> closer to 2025-01-07"}
json.dump(choice, open(os.path.join(OUT, "pair_choice.json"), "w"), indent=1)
print(json.dumps(choice, indent=1))
