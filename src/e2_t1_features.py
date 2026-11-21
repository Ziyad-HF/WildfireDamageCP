"""E2 WP2-M5 (image-feature version, I10): T1 penultimate features (512-d, after the head's Linear + GELU) for the
calib, test and Eaton buildings of one fold/seed, from the saved best checkpoint. Also recomputes the logits and
checks them against the published prediction file.
Usage: e2_t1_features.py --fold K --seed S  ->  results/features/t1_fold{K}_seed{S}.npz (ids, roles, feats float16)
"""
import os, argparse, numpy as np, pandas as pd, torch, torch.nn as nn, timm
import torchvision.transforms.functional as TF
from torch.utils.data import Dataset, DataLoader
from data import load_fold, load_pair, PROJ
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int); ap.add_argument("--seed", type=int); a = ap.parse_args()
MEAN, STD = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1), torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class DS(Dataset):
    def __init__(s, df): s.df = df.reset_index(drop=True)
    def __len__(s): return len(s.df)
    def __getitem__(s, i):
        pre, post = load_pair(s.df.iloc[i], marker=True)
        return (torch.stack([TF.to_tensor(pre), TF.to_tensor(post)]) - MEAN) / STD


class Siamese(nn.Module):  # same as src/t1_train.py
    def __init__(self):
        super().__init__()
        self.enc = timm.create_model("convnext_tiny.fb_in1k", pretrained=False, num_classes=0); d = self.enc.num_features
        self.head = nn.Sequential(nn.Linear(3 * d, 512), nn.GELU(), nn.Dropout(0.2), nn.Linear(512, 3))
    def forward(self, x):
        B = x.shape[0]; f = self.enc(x.flatten(0, 1)).view(B, 2, -1).float(); fa, fb = f[:, 0], f[:, 1]
        with torch.autocast("cuda", enabled=False):
            h = self.head[1](self.head[0](torch.cat([fa, fb, fb - fa], 1)))
            return h, self.head[3](h)


tag = f"t1_fold{a.fold}_seed{a.seed}"
m = Siamese().cuda().eval(); m.load_state_dict(torch.load(f"{PROJ}/checkpoints/{tag}_best.pt", map_location="cuda"))
f = load_fold(a.fold); f = f[f.role.isin(["calib", "test", "eaton"])].reset_index(drop=True)
H, L = [], []
with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
    for x in DataLoader(DS(f), batch_size=128, num_workers=8):
        h, lo = m(x.cuda()); H.append(h.float().cpu()); L.append(lo.float().cpu())
H = torch.cat(H).numpy(); L = torch.cat(L).numpy()
ref = pd.read_csv(f"{PROJ}/results/preds/{tag}.csv").set_index("id").loc[f.id, ["logit_no", "logit_dmg", "logit_des"]].to_numpy()
print(tag, "max |logit - published|:", float(np.abs(L - ref).max()), "argmax agree:", float((L.argmax(1) == ref.argmax(1)).mean()))
os.makedirs(f"{PROJ}/results/features", exist_ok=True)
np.savez_compressed(f"{PROJ}/results/features/{tag}.npz", ids=f.id.to_numpy(), roles=f.role.to_numpy(), feats=H.astype(np.float16))
