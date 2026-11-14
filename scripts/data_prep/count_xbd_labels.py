"""Gate G1: count xBD buildings per damage class for every event, without unpacking the images.

Streams the 6 downloaded parts (*.part-aa ... *.part-af) as one .tgz, extracts ONLY the
post-disaster label JSON files into Data/xView2/labels_post/, and writes:
  - xbd_counts_by_event.csv  (split, event, no-damage, minor, major, destroyed, un-classified)
  - xbd_counts_report.txt    (wildfire summary)
Reads ~55 GB sequentially, so it can take a while. Read-only for the archive parts.
Run:  python scripts/data_prep/count_xbd_labels.py
"""
import os, io, json, tarfile, collections, csv, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root (WildfireDamageCP)
XDIR = os.path.join(ROOT, "data", "raw", "xbd_archive")  # put the 6 *.part-a? files here to re-run
OUTDIR = os.path.join(ROOT, "data", "raw", "xbd_labels_post")
CLASSES = ["no-damage", "minor-damage", "major-damage", "destroyed", "un-classified"]


class Chain(io.RawIOBase):
    """Read several files back to back as one stream."""
    def __init__(self, paths):
        self.paths, self.i, self.f, self.done = paths, 0, None, 0
    def readable(self):
        return True
    def readinto(self, b):
        while self.i < len(self.paths):
            if self.f is None:
                self.f = open(self.paths[self.i], "rb")
            n = self.f.readinto(b)
            if n:
                self.done += n
                return n
            self.f.close(); self.f = None; self.i += 1
        return 0


parts = sorted((f for f in os.listdir(XDIR) if f[-7:-1] == "part-a"), key=lambda f: f[-2:])
assert [p[-2:] for p in parts] == ["aa", "ab", "ac", "ad", "ae", "af"], parts
paths = [os.path.join(XDIR, p) for p in parts]
total = sum(os.path.getsize(p) for p in paths)
os.makedirs(OUTDIR, exist_ok=True)

counts = collections.defaultdict(collections.Counter)  # (split, event) -> Counter
stream = io.BufferedReader(Chain(paths), buffer_size=16 * 1024 * 1024)
t0, last = time.time(), 0
with tarfile.open(fileobj=stream, mode="r|gz") as tar:
    for m in tar:
        if m.isfile() and m.name.endswith("_post_disaster.json"):
            data = tar.extractfile(m).read()
            name = os.path.basename(m.name)
            split = m.name.split("/")[1] if m.name.count("/") >= 2 else "?"
            with open(os.path.join(OUTDIR, f"{split}__{name}"), "wb") as out:
                out.write(data)
            event = name.split("_")[0]
            for feat in json.loads(data)["features"]["xy"]:
                counts[(split, event)][feat["properties"].get("subtype", "NA")] += 1
        done = stream.raw.done
        if done - last > 2e9:
            last = done
            print(f"{done/1e9:5.1f}/{total/1e9:.1f} GB read, {time.time()-t0:.0f}s")

with open(os.path.join(ROOT, "data", "metadata", "xbd_counts_by_event.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["split", "event"] + CLASSES)
    for (split, event), c in sorted(counts.items()):
        w.writerow([split, event] + [c.get(k, 0) for k in CLASSES])

fire = collections.defaultdict(collections.Counter)
for (split, event), c in counts.items():
    if "fire" in event:
        fire[event].update(c)
lines = ["Wildfire events, all splits combined:"]
for event, c in sorted(fire.items()):
    dmg = c["minor-damage"] + c["major-damage"]
    lines.append(f"{event}: no={c['no-damage']} damaged(minor+major)={dmg} "
                 f"destroyed={c['destroyed']} unclassified={c['un-classified']}")
lines.append(f"Done in {time.time()-t0:.0f}s")
open(os.path.join(ROOT, "data", "metadata", "xbd_counts_report.txt"), "w").write("\n".join(lines))
print("\n".join(lines))
