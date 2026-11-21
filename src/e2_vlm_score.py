"""E2 WP7/WP8: score buildings with a vision-language model and a prompt file, chunked.

Usage: e2_vlm_score.py --model qwen|gemma --prompt v1|v2|v3|v4 --name NAME CHUNK NCHUNKS
                       [--adapter DIR] [--index main|palisades] [--smoke N]
  v1 = configs/t2_prompt.txt (the frozen T2 prompt); vN = configs/t2_prompt_vN.txt.
  --adapter: a T3 LoRA adapter directory (Qwen only), for WP7 inference with the saved T3 models.
Writes results/preds/e2_raw/NAME/chunk{CHUNK}.csv with id, logit_no, logit_dmg, logit_des (letters mapped to
classes by the prompt's [MAP]; a class with no letter gets -1e4), abc_mass (probability mass of the letters).
Logits: last hidden state x fp32 output-layer rows (as Phase 4), plus the model's final soft-cap if it has one.
"""
import os, sys, re, time, argparse, numpy as np, pandas as pd, torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from data import load_index, load_pair, PROJ

ap = argparse.ArgumentParser()
ap.add_argument("--model", choices=["qwen", "gemma"], required=True)
ap.add_argument("--prompt", default="v1"); ap.add_argument("--name", required=True)
ap.add_argument("--adapter"); ap.add_argument("--index", default="main"); ap.add_argument("--smoke", type=int, default=0)
ap.add_argument("chunk", type=int); ap.add_argument("nchunks", type=int)
a = ap.parse_args()
MODELS = {"qwen": ("Qwen/Qwen3-VL-8B-Instruct", None),
          "gemma": ("google/gemma-4-12B-it", "43c9d014b231474fa7212dbb48a762566c2b255d")}
mid, rev = MODELS[a.model]
BS = 16 if a.model == "gemma" else 32
CLS = {"no": 0, "dmg": 1, "des": 2}


def read_prompt(name):
    path = f"{PROJ}/configs/t2_prompt.txt" if name == "v1" else f"{PROJ}/configs/t2_prompt_{name}.txt"
    txt = "\n".join(l for l in open(path).read().splitlines() if not l.startswith("#"))
    parts = {k: v.strip() for k, v in re.findall(r"\[(\w+)\]\n(.*?)(?=\n\[\w+\]|\Z)", txt, flags=re.S)}
    mp = parts.pop("MAP", "A=no,B=dmg,C=des")
    return parts, [(kv.split("=")[0], CLS[kv.split("=")[1]]) for kv in mp.split(",")]


P, MAP = read_prompt(a.prompt)
if a.index == "main":
    keep = set(pd.read_csv(f"{PROJ}/data/processed/splits/fold1.csv", usecols=["id"]).id)
    d = load_index(); d = d[d.id.isin(keep)].sort_values("id").reset_index(drop=True)
    assert len(d) == 83079, len(d)
else:
    d = pd.read_csv(f"{PROJ}/data/processed/crops/index_{a.index}.csv").sort_values("id").reset_index(drop=True)
if a.smoke:
    d = d[d.id.str.startswith("dins")].sample(a.smoke, random_state=0) if a.index == "main" else d.head(a.smoke)
d = d.iloc[np.array_split(np.arange(len(d)), a.nchunks)[a.chunk]]
print(f"{a.name}: model {mid} prompt {a.prompt} adapter {a.adapter} chunk {a.chunk}/{a.nchunks}: {len(d)} buildings", flush=True)

proc = AutoProcessor.from_pretrained(mid, revision=rev)
model = AutoModelForImageTextToText.from_pretrained(mid, revision=rev, dtype=torch.bfloat16, attn_implementation="sdpa",
                                                    device_map="cuda").eval()
if a.adapter:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, a.adapter).eval()
    base = model.base_model.model
else:
    base = model
tok = proc.tokenizer; tok.padding_side = "left"
ids = []
for letter, _ in MAP:
    t = tok.encode(letter, add_special_tokens=False)
    assert len(t) == 1, (letter, t)  # WP8 check: each answer letter must be a single token
    ids.append(t[0])
W = base.get_output_embeddings().weight[ids].detach().float()  # [L, hidden]
cfg = base.config.get_text_config() if hasattr(base.config, "get_text_config") else base.config
cap = getattr(cfg, "final_logit_softcapping", None)
Wall = None


def messages(row):
    pre, post = load_pair(row, marker=True)
    return [{"role": "user", "content": [
        {"type": "text", "text": P["TEXT_BEFORE"]}, {"type": "image", "image": pre},
        {"type": "text", "text": P["TEXT_BETWEEN"]}, {"type": "image", "image": post},
        {"type": "text", "text": P["QUESTION"]}]}]


@torch.no_grad()
def score(rows):
    global Wall
    enc = proc.apply_chat_template([messages(r) for r in rows], tokenize=True, add_generation_prompt=True,
                                   return_dict=True, return_tensors="pt", padding=True).to("cuda")
    if a.smoke and "n_img_checked" not in globals():  # two-image check (WP8): both images reach the model
        n_img = int((enc["input_ids"] == getattr(model.config, "image_token_id", getattr(base.config, "image_token_id", -1))).sum())
        print("image tokens in batch:", n_img, "| pixel_values:", tuple(enc["pixel_values"].shape) if "pixel_values" in enc else None, flush=True)
        globals()["n_img_checked"] = True
    h = base.model(**enc).last_hidden_state[:, -1, :].float()
    lg = h @ W.T
    if Wall is None:
        Wall = base.get_output_embeddings().weight.detach().float()
    full = h @ Wall.T
    if cap is not None:
        lg = cap * torch.tanh(lg / cap); full = cap * torch.tanh(full / cap)
    mass = torch.softmax(full, -1)[:, ids].sum(-1)
    return lg.cpu(), mass.cpu()


rows = [r for _, r in d.iterrows()]; L, M = [], []; t0 = time.time()
for i in range(0, len(rows), BS):
    lg, ms = score(rows[i:i + BS]); L.append(lg); M.append(ms)
    if (i // BS) % 100 == 0: print(f"{i + len(lg)}/{len(rows)} {time.time() - t0:.0f}s", flush=True)
L = torch.cat(L).numpy(); out = np.full((len(L), 3), -1e4)
for j, (_, c) in enumerate(MAP): out[:, c] = L[:, j]
o = d[["id"]].copy(); o[["logit_no", "logit_dmg", "logit_des"]] = out; o["abc_mass"] = torch.cat(M).numpy()
OUT = f"{PROJ}/results/{'smoke' if a.smoke else 'preds/e2_raw'}/{a.name}"; os.makedirs(OUT, exist_ok=True)
o.to_csv(f"{OUT}/chunk{a.chunk}.csv", index=False)
print(f"done {len(o)} in {time.time() - t0:.0f}s ({(time.time() - t0) / len(o):.4f} s/building), peak "
      f"{torch.cuda.max_memory_allocated() / 1e9:.1f} GB, letter mass min/median {o.abc_mass.min():.4f}/{o.abc_mass.median():.4f}", flush=True)
