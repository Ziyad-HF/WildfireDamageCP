"""G3 part 1: frozen-prompt Qwen3-VL-8B on 200 val buildings (class-balanced 67/67/66, seed 0).
Logs runtime per building, peak GPU memory, accuracy, macro-F1, and p-sum check. No prompt tuning."""
import os, sys, time, json, numpy as np, pandas as pd, torch
from sklearn.metrics import f1_score, confusion_matrix, accuracy_score
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from data import load_fold, PROJ
from vlm_common import MODEL_ID, read_prompt, letter_ids, score_batch

BS = int(os.environ.get("BS", 16)); OUT = f"{PROJ}/results/pilot"; os.makedirs(OUT, exist_ok=True)
# pool val = val role in any fold (D2: a fire's val buildings are the same in every fold where it trains)
val = pd.concat([load_fold(k).query("role == 'val'") for k in (1, 2)]).drop_duplicates("id")
n_per = {0: 67, 1: 67, 2: 66}
samp = pd.concat([val[val.y == c].sample(n, random_state=0) for c, n in n_per.items()]).reset_index(drop=True)
print("pilot sample by fire x class:\n", pd.crosstab(samp.fold, samp.label), flush=True)

t0 = time.time()
proc = AutoProcessor.from_pretrained(MODEL_ID)
model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda").eval()
t_load = time.time() - t0; print(f"model load {t_load:.1f}s", flush=True)
P, ids = read_prompt(), letter_ids(proc.tokenizer)
torch.cuda.reset_peak_memory_stats()
rows = [r for _, r in samp.iterrows()]; L, M, tb = [], [], []
torch.cuda.synchronize(); t1 = time.time()
for i in range(0, len(rows), BS):
    tt = time.time(); abc, mass, seqlen = score_batch(model, proc, rows[i:i + BS], P, ids); torch.cuda.synchronize()
    tb.append(time.time() - tt); L.append(abc); M.append(mass)
t_inf = time.time() - t1
L = torch.cat(L); M = torch.cat(M); p = torch.softmax(L, -1).numpy()
samp[["logit_no", "logit_dmg", "logit_des"]] = L.numpy(); samp[["p_no", "p_dmg", "p_des"]] = p; samp["abc_mass"] = M.numpy()
pred = p.argmax(1)
res = {"n": len(samp), "batch_size": BS, "seq_len": int(seqlen), "model_load_s": round(t_load, 1),
       "inference_s": round(t_inf, 2), "s_per_building": round(t_inf / len(samp), 4),
       "s_per_building_excl_first_batch": round(sum(tb[1:]) / (len(samp) - BS), 4),
       "peak_mem_alloc_GB": round(torch.cuda.max_memory_allocated() / 1e9, 2),
       "peak_mem_reserved_GB": round(torch.cuda.max_memory_reserved() / 1e9, 2),
       "accuracy": round(accuracy_score(samp.y, pred), 4), "macro_f1": round(f1_score(samp.y, pred, average="macro"), 4),
       "per_class_f1": [round(v, 4) for v in f1_score(samp.y, pred, average=None, labels=[0, 1, 2])],
       "confusion_rows_true_cols_pred": confusion_matrix(samp.y, pred, labels=[0, 1, 2]).tolist(),
       "pred_counts": np.bincount(pred, minlength=3).tolist(),
       "p_sum_max_abs_dev": float(np.abs(p.sum(1) - 1).max()),
       "abc_mass_min_median": [round(float(M.min()), 4), round(float(M.median()), 4)],
       "gpu": torch.cuda.get_device_name(0)}
print(json.dumps(res, indent=1))
samp.drop(columns=["pre", "post"]).to_csv(f"{OUT}/t2_pilot_preds.csv", index=False)
json.dump(res, open(f"{OUT}/t2_pilot_summary.json", "w"), indent=1)
