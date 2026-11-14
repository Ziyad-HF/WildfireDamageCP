"""Phase 3: T1 siamese ConvNeXt-Tiny (timm convnext_tiny.fb_in1k, shared weights) on marked pre/post crops.
Head: [f_pre, f_post, f_post - f_pre] -> Linear(2304,512) -> GELU -> Dropout(0.2) -> Linear(512,3).
Loss: CE with inverse-sqrt-frequency class weights (train counts of the fold; normalised to mean 1).
AdamW lr 1e-4, weight decay 0.05, constant LR, batch 64, bf16 autocast for the encoder, fp32 head, <= 20 epochs,
early stopping on val macro-F1 (patience 4). Augmentation: identical random h/v flip + 90-degree rotation on pre and post.
Usage: t1_train.py --fold K --seed S [--smoke]  (smoke: 1 epoch, predicts val+calib only, writes to results/smoke)."""
import os, json, time, argparse, random, numpy as np, pandas as pd, torch, torch.nn as nn, timm
import torchvision.transforms.functional as TF
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score
from data import load_fold, load_pair, PROJ

ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, required=True); ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
BACKBONE, BS, LR, WD, MAX_EP, PAT = "convnext_tiny.fb_in1k", 64, 1e-4, 0.05, 20, 4
if a.smoke: MAX_EP = 1
random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
tag = f"t1_fold{a.fold}_seed{a.seed}"
OUTP = f"{PROJ}/results/smoke" if a.smoke else f"{PROJ}/results/preds"
OUTL = f"{PROJ}/results/smoke" if a.smoke else f"{PROJ}/results/t1_logs"
CK = f"{PROJ}/checkpoints/{'smoke_' if a.smoke else ''}{tag}_best.pt"
for p in (OUTP, OUTL, os.path.dirname(CK)): os.makedirs(p, exist_ok=True)
MEAN, STD = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1), torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class PairDS(Dataset):
    def __init__(self, df, train): self.df, self.train = df.reset_index(drop=True), train
    def __len__(self): return len(self.df)
    def __getitem__(self, i):
        r = self.df.iloc[i]; pre, post = load_pair(r, marker=True)
        x = torch.stack([TF.to_tensor(pre), TF.to_tensor(post)])  # [2,3,H,W]
        if self.train:
            if torch.rand(1) < 0.5: x = x.flip(-1)
            if torch.rand(1) < 0.5: x = x.flip(-2)
            x = torch.rot90(x, int(torch.randint(0, 4, (1,))), dims=(-2, -1))
        return (x - MEAN) / STD, int(r.y), i


class Siamese(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = timm.create_model(BACKBONE, pretrained=True, num_classes=0); d = self.enc.num_features
        self.head = nn.Sequential(nn.Linear(3 * d, 512), nn.GELU(), nn.Dropout(0.2), nn.Linear(512, 3))
    def forward(self, x):  # x [B,2,3,H,W]
        B = x.shape[0]; f = self.enc(x.flatten(0, 1)).view(B, 2, -1).float(); fa, fb = f[:, 0], f[:, 1]
        with torch.autocast("cuda", enabled=False):  # head in fp32 so logits are not bf16-quantised
            return self.head(torch.cat([fa, fb, fb - fa], 1))


def loader(df, train):
    g = torch.Generator(); g.manual_seed(a.seed)
    return DataLoader(PairDS(df, train), batch_size=BS, shuffle=train, num_workers=8, pin_memory=True,
                      persistent_workers=True, generator=g, drop_last=False,
                      worker_init_fn=lambda w: (np.random.seed(torch.initial_seed() % 2**32), random.seed(torch.initial_seed() % 2**32)))


@torch.no_grad()
def predict(model, dl):
    model.eval(); out = np.zeros((len(dl.dataset), 3), np.float32)
    for x, _, idx in dl:
        with torch.autocast("cuda", dtype=torch.bfloat16): lo = model(x.cuda(non_blocking=True))
        out[idx.numpy()] = lo.float().cpu().numpy()
    return out


f = load_fold(a.fold); tr, va = f[f.role == "train"], f[f.role == "val"]
cnt = np.bincount(tr.y, minlength=3); w = 1 / np.sqrt(cnt); w = w / w.mean()
print(f"{tag} smoke={a.smoke} train {cnt.tolist()} val {np.bincount(va.y, minlength=3).tolist()} class weights {np.round(w, 3).tolist()}", flush=True)
model = Siamese().cuda()
opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WD)
crit = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32).cuda())
dl_tr, dl_va = loader(tr, True), loader(va, False)
best, best_ep, hist, bad = -1, -1, [], 0
for ep in range(1, MAX_EP + 1):
    model.train(); t = time.time(); tot, n = 0.0, 0
    for x, y, _ in dl_tr:
        x, y = x.cuda(non_blocking=True), y.cuda(non_blocking=True)
        with torch.autocast("cuda", dtype=torch.bfloat16): loss = crit(model(x), y)
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        tot += loss.item() * len(y); n += len(y)
    t_tr = time.time() - t
    pv = predict(model, dl_va).argmax(1)
    mf1 = f1_score(va.y, pv, average="macro"); pc = f1_score(va.y, pv, average=None, labels=[0, 1, 2])
    hist.append({"epoch": ep, "train_loss": round(tot / n, 4), "val_macro_f1": round(mf1, 4), "val_f1": [round(v, 4) for v in pc],
                 "train_s": round(t_tr, 1), "total_s": round(time.time() - t, 1)})
    print(hist[-1], flush=True)
    if mf1 > best: best, best_ep, bad = mf1, ep, 0; torch.save(model.state_dict(), CK)
    else:
        bad += 1
        if bad >= PAT: print(f"early stop at epoch {ep}", flush=True); break

model.load_state_dict(torch.load(CK, map_location="cuda"))
roles = ["val", "calib"] if a.smoke else ["val", "calib", "test", "eaton"]
pf = f[f.role.isin(roles)].reset_index(drop=True)
lo = predict(model, loader(pf, False)); p = torch.softmax(torch.tensor(lo), 1).numpy()
o = pf[["id", "source", "role"]].copy(); o["label"] = pf.y.astype(int)
o[["logit_no", "logit_dmg", "logit_des"]] = lo; o[["p_no", "p_dmg", "p_des"]] = p
o.to_csv(f"{OUTP}/{tag}.csv", index=False)
summ = {"tag": tag, "smoke": a.smoke, "backbone": BACKBONE, "best_epoch": best_ep, "best_val_macro_f1": round(best, 4),
        "epochs_run": len(hist), "class_weights": np.round(w, 4).tolist(), "gpu": torch.cuda.get_device_name(0),
        "peak_mem_GB": round(torch.cuda.max_memory_allocated() / 1e9, 2), "pred_rows": o.role.value_counts().to_dict(), "history": hist}
json.dump(summ, open(f"{OUTL}/{tag}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != "history"}))
