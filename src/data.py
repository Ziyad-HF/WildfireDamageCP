"""Shared data helpers: split loading, crop loading with the preregistered marker (rule 5)."""
import os
import pandas as pd
from PIL import Image, ImageDraw

PROJ = os.environ.get("WDCP_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CROPS = f"{PROJ}/data/processed/crops"
CLASSES = ["no damage", "damaged", "destroyed"]  # rule 1: 0, 1, 2
LABEL2ID = {c: i for i, c in enumerate(CLASSES)}
MARK_R, MARK_W = 9, 2  # rule 5


def load_index():
    cols = ["id", "fold", "event", "label", "pre", "post", "bx", "by"]
    x = pd.read_csv(f"{CROPS}/index_xbd_v2.csv", usecols=cols)
    e = pd.read_csv(f"{CROPS}/index_eaton.csv", usecols=cols)
    d = pd.concat([x, e], ignore_index=True)
    d["y"] = d.label.map(LABEL2ID)
    return d


def load_fold(k):
    s = pd.read_csv(f"{PROJ}/data/processed/splits/fold{k}.csv")
    return s.merge(load_index().drop(columns=["event"]), on="id", how="left", validate="1:1")


def mark(img, bx, by):
    img = img.convert("RGB").copy()
    ImageDraw.Draw(img).ellipse([bx - MARK_R, by - MARK_R, bx + MARK_R, by + MARK_R], outline=(255, 0, 0), width=MARK_W)
    return img


def load_pair(row, marker=True):
    pre = Image.open(f"{CROPS}/{row['pre']}")
    post = Image.open(f"{CROPS}/{row['post']}")
    if marker:
        pre, post = mark(pre, row["bx"], row["by"]), mark(post, row["bx"], row["by"])
    else:
        pre, post = pre.convert("RGB"), post.convert("RGB")
    return pre, post
