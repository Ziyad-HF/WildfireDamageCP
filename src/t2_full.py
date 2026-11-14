"""Phase 4: frozen-prompt Qwen3-VL-8B on all 83,079 non-excluded buildings, chunked.
Usage: t2_full.py CHUNK NCHUNKS -> results/preds/t2_raw/chunk{CHUNK}.csv (id, logits, p, abc_mass)."""
import os, sys, time, numpy as np, pandas as pd, torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from data import load_index, PROJ
from vlm_common import MODEL_ID, read_prompt, letter_ids, score_batch

ci, nc = int(sys.argv[1]), int(sys.argv[2]); BS = 32
OUT = f"{PROJ}/results/preds/t2_raw"; os.makedirs(OUT, exist_ok=True)
keep = set(pd.read_csv(f"{PROJ}/data/processed/splits/fold1.csv", usecols=["id"]).id)  # all non-excluded xBD + Eaton
d = load_index(); d = d[d.id.isin(keep)].sort_values("id").reset_index(drop=True)
assert len(d) == 83079, len(d)
d = d.iloc[np.array_split(np.arange(len(d)), nc)[ci]]
print(f"chunk {ci}/{nc}: {len(d)} buildings", flush=True)
proc = AutoProcessor.from_pretrained(MODEL_ID)
model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda").eval()
P, ids = read_prompt(), letter_ids(proc.tokenizer)
rows = [r for _, r in d.iterrows()]; L, M = [], []; t = time.time()
for i in range(0, len(rows), BS):
    abc, mass, _ = score_batch(model, proc, rows[i:i + BS], P, ids); L.append(abc); M.append(mass)
    if (i // BS) % 100 == 0: print(f"{i + len(abc)}/{len(rows)} {time.time() - t:.0f}s", flush=True)
L = torch.cat(L); p = torch.softmax(L, -1).numpy()
o = d[["id"]].copy(); o[["logit_no", "logit_dmg", "logit_des"]] = L.numpy(); o[["p_no", "p_dmg", "p_des"]] = p
o["abc_mass"] = torch.cat(M).numpy()
o.to_csv(f"{OUT}/chunk{ci}.csv", index=False)
print(f"done {len(o)} in {time.time() - t:.0f}s, {(time.time() - t) / len(o):.4f} s/building, peak {torch.cuda.max_memory_allocated() / 1e9:.1f} GB")
