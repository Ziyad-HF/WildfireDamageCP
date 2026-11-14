"""T2/T3 helpers: frozen prompt, chat messages, answer-token ids, batched A/B/C scoring."""
import re, torch
from data import load_pair, PROJ

MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"
PROMPT_FILE = f"{PROJ}/configs/t2_prompt.txt"
LETTERS = ["A", "B", "C"]  # -> no damage, damaged, destroyed


def read_prompt(path=PROMPT_FILE):
    txt = "\n".join(l for l in open(path).read().splitlines() if not l.startswith("#"))
    parts = dict(re.findall(r"\[(\w+)\]\n(.*?)(?=\n\[\w+\]|\Z)", txt, flags=re.S))
    return {k: v.strip() for k, v in parts.items()}


def messages(row, P, answer=None):
    pre, post = load_pair(row, marker=True)
    m = [{"role": "user", "content": [
        {"type": "text", "text": P["TEXT_BEFORE"]}, {"type": "image", "image": pre},
        {"type": "text", "text": P["TEXT_BETWEEN"]}, {"type": "image", "image": post},
        {"type": "text", "text": P["QUESTION"]}]}]
    if answer is not None:
        m.append({"role": "assistant", "content": [{"type": "text", "text": answer}]})
    return m


def letter_ids(tok):
    ids = [tok.encode(l, add_special_tokens=False) for l in LETTERS]
    assert all(len(i) == 1 for i in ids), ids
    return [i[0] for i in ids]


def encode(processor, convs, gen_prompt=True):
    return processor.apply_chat_template(convs, tokenize=True, add_generation_prompt=gen_prompt,
                                         return_dict=True, return_tensors="pt", padding=True)


@torch.no_grad()
def score_batch(model, processor, rows, P, ids):
    """Return (abc_logits [B,3] float32, mass of A+B+C in the full-vocab softmax [B])."""
    processor.tokenizer.padding_side = "left"
    enc = encode(processor, [messages(r, P) for r in rows]).to(model.device)
    # last hidden state -> lm_head in fp32 (the bf16 lm_head output quantises logits; matters for calibration/conformal)
    h = model.model(**enc).last_hidden_state[:, -1, :].float()
    if not hasattr(model, "_lm_w32"):
        model._lm_w32 = model.lm_head.weight.detach().float()
        assert getattr(model.lm_head, "bias", None) is None
    logits = h @ model._lm_w32.T
    abc = logits[:, ids]
    mass = torch.softmax(logits, -1)[:, ids].sum(-1)
    return abc.cpu(), mass.cpu(), enc["input_ids"].shape[1]
