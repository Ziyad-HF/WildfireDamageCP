"""Download Maxar Open Data 'visual' (RGB, ~0.3 m) tiles covering the 2025 Eaton Fire.
Source: s3://maxar-opendata/events/WildFires-LosAngeles-Jan-2025/ard/ (public, CC BY-NC 4.0).
The 6 tile IDs below were computed from the DINS Eaton bounding box
(lon -118.164..-118.018, lat 34.161..34.232) in the UTM 11N ARD grid.
Saves to data/raw/maxar_eaton_2025/<tile>/<date>/ and skips files already present.
Run:  python scripts/data_prep/download_maxar_eaton.py
"""
import os, re, urllib.request, urllib.parse

BASE = "https://maxar-opendata.s3.amazonaws.com"
EVENT = "events/WildFires-LosAngeles-Jan-2025/ard/11/"
TILES = ["031311103030", "031311103031", "031311103120",
         "031311103032", "031311103033", "031311103122"]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root (WildfireDamageCP)
OUT = os.path.join(ROOT, "data", "raw", "maxar_eaton_2025")


def list_keys(prefix):
    keys, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix}
        if token:
            q["continuation-token"] = token
        xml = urllib.request.urlopen(BASE + "/?" + urllib.parse.urlencode(q), timeout=60).read().decode()
        keys += re.findall(r"<Key>([^<]+)</Key>", xml)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not m:
            return keys
        token = m.group(1)


total = 0
for tile in TILES:
    keys = [k for k in list_keys(EVENT + tile + "/") if k.endswith("-visual.tif") or k.endswith(".json")]
    print(f"{tile}: {len(keys)} files")
    for k in keys:
        rel = k[len(EVENT):]
        dst = os.path.join(OUT, *rel.split("/"))
        if os.path.exists(dst):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".part"
        urllib.request.urlretrieve(BASE + "/" + urllib.parse.quote(k), tmp)
        os.replace(tmp, dst)
        total += os.path.getsize(dst)
        print(f"  {rel}  ({os.path.getsize(dst)/1e6:.0f} MB)")
print(f"Done. Downloaded {total/1e9:.2f} GB this run.")
