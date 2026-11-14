"""G3 part 2: 50 LoRA steps (bf16, r=16, alpha=32, LM attention+MLP only, vision frozen) on fold-1 train buildings.
Class-balanced sampling, batch 8, AdamW lr 1e-4. Loss only on the answer tokens. Logs loss per step, peak memory, s/step."""
import os, time, json, numpy as np, pandas as pd, torch
from peft import LoraConfig, get_peft_model
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from data import load_fold, PROJ, CLASSES
from vlm_common import MODEL_ID, read_prompt, messages, encode, LETTERS

STEPS, BS, LR = 50, 8, 1e-4; OUT = f"{PROJ}/results/pilot"; os.makedirs(OUT, exist_ok=True)
torch.manual_seed(0); rng = np.random.default_rng(0)
tr = load_fold(1).query("role == 'train'")
by_c = {c: tr[tr.y == c] for c in range(3)}
proc = AutoProcessor.from_pretrained(MODEL_ID); P = read_prompt()
model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                 target_modules=r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)")
model = get_peft_model(model, cfg); model.print_trainable_parameters()
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
model.train(); torch.cuda.reset_peak_memory_stats(); log = []
proc.tokenizer.padding_side = "right"
for step in range(STEPS):
    cls = rng.integers(0, 3, BS)
    rows = [by_c[c].iloc[rng.integers(len(by_c[c]))] for c in cls]
    full = encode(proc, [messages(r, P, answer=LETTERS[int(r.y)]) for r in rows], gen_prompt=False)
    plen = encode(proc, [messages(r, P) for r in rows])["attention_mask"].sum(1)
    labels = full["input_ids"].clone()
    for i in range(BS):
        labels[i, :plen[i]] = -100
        labels[i, plen[i] + 2:] = -100  # keep letter + <|im_end|> only
    labels[full["attention_mask"] == 0] = -100
    full = full.to("cuda"); torch.cuda.synchronize(); t = time.time()
    loss = model(**full, labels=labels.to("cuda")).loss
    loss.backward(); opt.step(); opt.zero_grad(set_to_none=True); torch.cuda.synchronize()
    log.append({"step": step + 1, "loss": round(loss.item(), 4), "s": round(time.time() - t, 3)})
    print(log[-1], flush=True)
    assert torch.isfinite(loss), "non-finite loss"
L = [r["loss"] for r in log]
res = {"steps": STEPS, "batch_size": BS, "lr": LR, "lora": "r16 a32 d0.05 LM attn+MLP",
       "loss_first10_mean": round(float(np.mean(L[:10])), 4), "loss_last10_mean": round(float(np.mean(L[-10:])), 4),
       "s_per_step_median": round(float(np.median([r["s"] for r in log[1:]])), 3),
       "peak_mem_alloc_GB": round(torch.cuda.max_memory_allocated() / 1e9, 2),
       "peak_mem_reserved_GB": round(torch.cuda.max_memory_reserved() / 1e9, 2), "gpu": torch.cuda.get_device_name(0)}
print(json.dumps(res, indent=1))
json.dump({"summary": res, "log": log}, open(f"{OUT}/t3_lora_pilot.json", "w"), indent=1)
