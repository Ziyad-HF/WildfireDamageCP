"""Check that fp32 lm_head logits (vlm_common.score_batch) match the model's bf16 logits up to bf16 rounding."""
import torch, pandas as pd
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from data import load_fold
from vlm_common import MODEL_ID, read_prompt, letter_ids, score_batch, messages, encode
proc = AutoProcessor.from_pretrained(MODEL_ID)
model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda").eval()
P, ids = read_prompt(), letter_ids(proc.tokenizer)
rows = [r for _, r in load_fold(1).query("role == 'val'").head(32).iterrows()]
abc32, mass, _ = score_batch(model, proc, rows, P, ids)
with torch.no_grad():
    proc.tokenizer.padding_side = "left"
    ref = model(**encode(proc, [messages(r, P) for r in rows]).to("cuda")).logits[:, -1, ids].float().cpu()
print("fp32 sample:", abc32[:3].tolist()); print("bf16 sample:", ref[:3].tolist())
print("max abs diff", (abc32 - ref).abs().max().item(), "argmax agree", (abc32.argmax(1) == ref.argmax(1)).float().mean().item(),
      "unique fp32 values", abc32.unique().numel(), "of", abc32.numel(), "| unique bf16", ref.unique().numel())
