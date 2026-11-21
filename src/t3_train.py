"""Phase 6: T3 = Qwen3-VL-8B-Instruct + LoRA, supervised on the fold's train buildings, early stopping on val.

Design (fixed 2026-11-10, before any T3 run):
- Same frozen prompt and red-circle marker as T2 (configs/t2_prompt.txt, rule 5); no image augmentation.
- LoRA r=16, alpha=32, dropout 0.05 on the language model's attention + MLP projections; vision tower and lm_head frozen.
  LoRA weights kept in fp32, forward under bf16 autocast.
- Loss: 3-way cross-entropy on the A/B/C logits (last hidden state -> fp32 lm_head rows for A, B, C; the same
  probability definition as T2), class weights 1/sqrt(train count) normalised to mean 1 (as T1).
- AdamW lr 1e-4, weight decay 0, constant LR, batch 8, shuffled with numpy default_rng(seed).
- Val macro-F1 every half epoch; stop after 2 checks without improvement; at most 3 epochs; keep the best adapter.
- Predictions (fp32 A/B/C logits) for val, calib, test, eaton -> results/preds/t3_fold{k}_seed{s}.csv.
Usage: t3_train.py --fold K --seed S [--smoke]  (smoke: 40 steps, 2 checks on 200 val buildings,
       predicts 100 val + 100 calib only, writes to results/smoke and checkpoints/smoke_*).
"""
import os, json, time, argparse, random, numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score
from peft import LoraConfig, get_peft_model
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from data import load_fold, PROJ
from vlm_common import MODEL_ID, read_prompt, messages, encode, letter_ids

ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, required=True); ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--smoke", action="store_true")
ap.add_argument("--max-epochs", type=int, default=3)  # E2 WP8-C: 6; outputs then use the tag t3e{N}
a = ap.parse_args()
BS, LR, PAT, CHECKS_PER_EP = 8, 1e-4, 2, 2
MAX_EP = a.max_epochs
random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
tag = (f"t3" if MAX_EP == 3 else f"t3e{MAX_EP}") + f"_fold{a.fold}_seed{a.seed}"
OUTP = f"{PROJ}/results/smoke" if a.smoke else f"{PROJ}/results/preds"
OUTL = f"{PROJ}/results/smoke" if a.smoke else f"{PROJ}/results/t3_logs"
CK = f"{PROJ}/checkpoints/{'smoke_' if a.smoke else ''}{tag}_best"
for p in (OUTP, OUTL): os.makedirs(p, exist_ok=True)

proc = AutoProcessor.from_pretrained(MODEL_ID); proc.tokenizer.padding_side = "left"; P = read_prompt()
IDS = letter_ids(proc.tokenizer)


class Collate:
    def __call__(self, rows):
        enc = encode(proc, [messages(r, P) for r in rows])
        return enc, torch.tensor([int(r["y"]) for r in rows]), [r["id"] for r in rows]


def loader(df, shuffle_seed=None):
    rows = df.to_dict("records")
    if shuffle_seed is not None:
        rows = [rows[i] for i in np.random.default_rng(shuffle_seed).permutation(len(rows))]
    return DataLoader(rows, batch_size=BS if shuffle_seed is not None else 32, shuffle=False, num_workers=6,
                      collate_fn=Collate(), persistent_workers=False, prefetch_factor=4)


model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                 target_modules=r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)")
model = get_peft_model(model, cfg)
for n, p_ in model.named_parameters():
    if p_.requires_grad: p_.data = p_.data.float()
model.print_trainable_parameters()
base = model.base_model.model  # Qwen3VLForConditionalGeneration with LoRA layers injected
W_ABC = base.lm_head.weight[IDS].detach().float()  # [3, hidden], frozen


def abc_logits(enc):
    with torch.autocast("cuda", dtype=torch.bfloat16):
        h = base.model(**enc).last_hidden_state[:, -1, :]
    return h.float() @ W_ABC.T


@torch.no_grad()
def predict(df):
    model.eval(); out, ids = [], []
    for enc, _, bid in loader(df):
        out.append(abc_logits(enc.to("cuda")).cpu()); ids += bid
    model.train()
    return pd.Series(range(len(ids)), index=ids), torch.cat(out).numpy()


f = load_fold(a.fold); tr, va = f[f.role == "train"], f[f.role == "val"]
if a.smoke: va = pd.concat([va[va.y == c].sample(min(int((va.y == c).sum()), 67), random_state=0) for c in range(3)])
cnt = np.bincount(tr.y, minlength=3); w = 1 / np.sqrt(cnt); w = w / w.mean()
crit = torch.nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32, device="cuda"))
opt = torch.optim.AdamW([p_ for p_ in model.parameters() if p_.requires_grad], lr=LR, weight_decay=0.0)
steps_per_ep = int(np.ceil(len(tr) / BS)); check_every = 20 if a.smoke else steps_per_ep // CHECKS_PER_EP
max_steps = 40 if a.smoke else MAX_EP * steps_per_ep
print(f"{tag} smoke={a.smoke} train {cnt.tolist()} val {np.bincount(va.y, minlength=3).tolist()} weights {np.round(w, 3).tolist()} "
      f"steps/epoch {steps_per_ep} check every {check_every} max steps {max_steps}", flush=True)

best, best_step, bad, hist, step, t0 = -1.0, 0, 0, [], 0, time.time()
best_state = None; losses = []; model.train(); torch.cuda.reset_peak_memory_stats(); stop = False
for ep in range(MAX_EP):
    for enc, y, _ in loader(tr, shuffle_seed=a.seed * 1000 + ep):
        loss = crit(abc_logits(enc.to("cuda")), y.cuda())
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        step += 1; losses.append(loss.item())
        if step % 200 == 0: print(f"step {step} loss(avg200) {np.mean(losses[-200:]):.4f} {time.time() - t0:.0f}s", flush=True)
        if step % check_every == 0 or step == max_steps:
            idx, lo = predict(va); pv = lo.argmax(1); assert list(idx.index) == list(va.id); yv = va.y.to_numpy()
            mf1 = f1_score(yv, pv, average="macro"); pc = f1_score(yv, pv, average=None, labels=[0, 1, 2])
            hist.append({"step": step, "epoch": round(step / steps_per_ep, 2), "train_loss_recent": round(float(np.mean(losses[-check_every:])), 4),
                         "val_macro_f1": round(mf1, 4), "val_f1": [round(float(v), 4) for v in pc], "elapsed_s": round(time.time() - t0)})
            print(hist[-1], flush=True)
            if mf1 > best:
                best, best_step, bad = mf1, step, 0
                best_state = {n: p_.detach().cpu().clone() for n, p_ in model.named_parameters() if p_.requires_grad}
            else:
                bad += 1
                if bad >= PAT: print(f"early stop at step {step}", flush=True); stop = True
        if stop or step >= max_steps: break
    if stop or step >= max_steps: break

# restore best adapter, save it, predict
with torch.no_grad():
    for n, p_ in model.named_parameters():
        if n in best_state: p_.copy_(best_state[n].to(p_.device))
model.save_pretrained(CK)
roles = ["val", "calib"] if a.smoke else ["val", "calib", "test", "eaton"]
pf = f[f.role.isin(roles)]
if a.smoke: pf = pd.concat([pf[pf.role == r].head(100) for r in roles])
idx, lo = predict(pf)
pf = pf.reset_index(drop=True); assert list(idx.index) == list(pf.id), "prediction order mismatch"
p = torch.softmax(torch.tensor(lo), 1).numpy()
o = pf[["id", "source", "role"]].copy(); o["label"] = pf.y.astype(int)
o[["logit_no", "logit_dmg", "logit_des"]] = lo; o[["p_no", "p_dmg", "p_des"]] = p
o.to_csv(f"{OUTP}/{tag}.csv", index=False)
summ = {"tag": tag, "smoke": a.smoke, "best_step": best_step, "best_epoch": round(best_step / steps_per_ep, 2),
        "best_val_macro_f1": round(best, 4), "steps_run": step, "class_weights": np.round(w, 4).tolist(),
        "gpu": torch.cuda.get_device_name(0), "peak_mem_GB": round(torch.cuda.max_memory_allocated() / 1e9, 2),
        "total_s": round(time.time() - t0), "pred_rows": o.role.value_counts().to_dict(), "history": hist}
json.dump(summ, open(f"{OUTL}/{tag}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != "history"}))
