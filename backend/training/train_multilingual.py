
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import json
import time
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.cuda.amp import GradScaler, autocast

from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, roc_curve
from scipy.optimize import brentq
from scipy.interpolate import interp1d

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.models.voiceclone_model import VoiceCloneDetector

LANG_ID = {"te": 0, "hi": 1, "ta": 2, "kn": 3, "mr": 4, "en": 5,
           "multi": 6, "unknown": 6}
LANG_NAME = {0:"Telugu", 1:"Hindi", 2:"Tamil", 3:"Kannada",
             4:"Marathi", 5:"English", 6:"Other"}


class MultilingualDataset(Dataset):
    def __init__(self, proc_dir: Path, sources: list, split: str = "train",
                 val_ratio=0.15, test_ratio=0.10, augment=False, seed=42):
        self.augment = augment
        all_mel, all_mfcc, all_labels, all_lang_ids = [], [], [], []

        for src in sources:
            src_dir = proc_dir / src
            mel_f   = src_dir / "mel.npy"
            lbl_f   = src_dir / "labels.npy"
            meta_f  = src_dir / "metadata.csv"

            if not mel_f.exists():
                continue

            mel    = np.load(mel_f)
            mfcc   = np.load(src_dir / "mfcc.npy")
            labels = np.load(lbl_f)

            if meta_f.exists():
                df    = pd.read_csv(meta_f)
                langs = [LANG_ID.get(l, 6) for l in df["language"].fillna("unknown")]
            else:
                langs = [6] * len(labels)

            n   = len(labels)
            rng = np.random.RandomState(seed)
            idx = rng.permutation(n)
            n_t = int(n * test_ratio)
            n_v = int(n * val_ratio)

            if split == "train":   idx = idx[:n - n_t - n_v]
            elif split == "val":   idx = idx[n - n_t - n_v:n - n_t]
            else:                  idx = idx[n - n_t:]

            all_mel.append(mel[idx])
            all_mfcc.append(mfcc[idx])
            all_labels.append(labels[idx])
            all_lang_ids.extend([langs[i] for i in idx])

            g = int((labels[idx] == 0).sum())
            f = int((labels[idx] == 1).sum())
            print(f"    [{src}] {split}: {len(idx):,} (genuine={g:,} fake={f:,})")

        if not all_mel:
            raise RuntimeError("No processed sources found. Run preprocess_multilingual.py first.")

        self.mel      = torch.tensor(np.concatenate(all_mel),   dtype=torch.float32)
        self.mfcc     = torch.tensor(np.concatenate(all_mfcc),  dtype=torch.float32)
        self.labels   = torch.tensor(np.concatenate(all_labels),dtype=torch.long)
        self.lang_ids = torch.tensor(all_lang_ids,               dtype=torch.long)

    def __len__(self): return len(self.labels)

    def __getitem__(self, i):
        mel, mfcc, label = self.mel[i], self.mfcc[i], self.labels[i]
        if self.augment and label == 0:
            mel = self._spec_augment(mel)
        return mel, mfcc, label, self.lang_ids[i]

    def _spec_augment(self, mel):
        mel = mel.clone()
        F, T = mel.shape
        f  = np.random.randint(0, 20); f0 = np.random.randint(0, max(1, F-f))
        mel[f0:f0+f, :] = 0.0
        t  = np.random.randint(0, 50); t0 = np.random.randint(0, max(1, T-t))
        mel[:, t0:t0+t] = 0.0
        return mel


def compute_eer(labels, scores):
    try:
        fpr, tpr, _ = roc_curve(labels, scores, pos_label=1)
        return float(brentq(lambda x: 1.0 - x - interp1d(fpr, tpr)(x), 0.0, 1.0)) * 100
    except Exception:
        return 50.0


def evaluate(model, loader, device, criterion):
    model.eval()
    all_labels, all_preds, all_probs = [], [], []
    lang_buckets = defaultdict(lambda: {"labels": [], "probs": []})
    total_loss = 0.0

    with torch.no_grad():
        for mel, mfcc, labels, lang_ids in loader:
            mel, mfcc, labels = mel.to(device), mfcc.to(device), labels.to(device)
            logits, probs = model(mel, mfcc)
            total_loss   += criterion(logits, labels).item()
            preds         = probs.argmax(-1)
            probs_np      = probs[:, 1].cpu().numpy()
            labels_np     = labels.cpu().numpy()

            all_labels.extend(labels_np)
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(probs_np)

            for j, lid in enumerate(lang_ids.numpy()):
                name = LANG_NAME.get(int(lid), "Other")
                lang_buckets[name]["labels"].append(int(labels_np[j]))
                lang_buckets[name]["probs"].append(float(probs_np[j]))

    la = np.array(all_labels)
    pa = np.array(all_preds)
    pr = np.array(all_probs)

    metrics = {
        "loss":     total_loss / len(loader),
        "accuracy": accuracy_score(la, pa),
        "f1":       f1_score(la, pa, zero_division=0),
        "auc":      roc_auc_score(la, pr) if len(np.unique(la)) > 1 else 0.5,
        "eer":      compute_eer(la, pr),
        "per_lang": {},
    }

    for lang, data in lang_buckets.items():
        l = np.array(data["labels"])
        p = np.array(data["probs"])
        if len(l) < 10 or len(np.unique(l)) < 2:
            continue
        metrics["per_lang"][lang] = {
            "eer":      compute_eer(l, p),
            "auc":      roc_auc_score(l, p),
            "accuracy": accuracy_score(l, (p > 0.5).astype(int)),
            "n":        len(l),
        }
    return metrics


def print_metrics(tag, m, epoch, total):
    print(f"\n  [{tag}] Epoch {epoch}/{total}")
    print(f"    Overall → Loss:{m['loss']:.4f} Acc:{m['accuracy']*100:.1f}% "
          f"F1:{m['f1']:.3f} AUC:{m['auc']:.3f} EER:{m['eer']:.2f}%")
    if m["per_lang"]:
        for lang, lm in sorted(m["per_lang"].items()):
            status = "✅" if lm["eer"] < 8 else "⚠️" if lm["eer"] < 18 else "❌"
            print(f"    {status} {lang:<10}: EER={lm['eer']:.1f}%  "
                  f"AUC={lm['auc']:.3f}  (n={lm['n']:,})")


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    proc   = Path(args.data)

    if args.datasets:
        available = [d.strip() for d in args.datasets.split(",") if d.strip()]
    else:
        available = sorted([d.name for d in proc.iterdir()
                            if d.is_dir() and (d / "labels.npy").exists()]) if proc.exists() else []

    if not available:
        print("  ✗ No processed datasets found.")
        print("    Run: python datasets/download_multilingual.py --all-auto")
        print("    Then: python datasets/preprocess_multilingual.py --all")
        return

    print(f"\n  Device: {device}")
    print(f"  Sources ({len(available)}): {available}")

    print("\n  Building datasets...")
    train_ds = MultilingualDataset(proc, available, "train", augment=True)
    val_ds   = MultilingualDataset(proc, available, "val",   augment=False)
    test_ds  = MultilingualDataset(proc, available, "test",  augment=False)

    labels_np  = train_ds.labels.numpy()
    lang_np    = train_ds.lang_ids.numpy()
    class_w    = 1.0 / (np.bincount(labels_np, minlength=2)[labels_np] + 1)
    lang_w     = 1.0 / (np.bincount(lang_np,   minlength=7)[lang_np]   + 1)
    sample_w   = torch.tensor(class_w * lang_w, dtype=torch.float32)

    train_loader = DataLoader(train_ds, args.batch_size,
                              sampler=WeightedRandomSampler(sample_w, len(sample_w)),
                              num_workers=args.workers, pin_memory=True)
    val_loader   = DataLoader(val_ds,   args.batch_size, shuffle=False,
                              num_workers=args.workers, pin_memory=True)
    test_loader  = DataLoader(test_ds,  args.batch_size, shuffle=False,
                              num_workers=args.workers, pin_memory=True)

    model     = VoiceCloneDetector().to(device)
    print(f"\n  Model parameters: {model.num_parameters:,}")

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, args.epochs, eta_min=1e-6)
    scaler    = GradScaler(enabled=(device.type == "cuda"))

    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_eer, patience_ctr = float("inf"), 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        for mel, mfcc, labels, _ in train_loader:
            mel, mfcc, labels = mel.to(device), mfcc.to(device), labels.to(device)
            optimizer.zero_grad()
            with autocast(enabled=(device.type == "cuda")):
                logits, _ = model(mel, mfcc)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer); scaler.update()
            train_loss += loss.item()

        scheduler.step()
        val_m = evaluate(model, val_loader, device, criterion)
        print_metrics("VAL", val_m, epoch, args.epochs)

        if val_m["eer"] < best_eer:
            best_eer = val_m["eer"]
            patience_ctr = 0
            torch.save({"epoch": epoch, "model": model.state_dict(),
                        "best_eer": best_eer, "val": val_m},
                       ckpt_dir / "best_model.pt")
            print(f"    ✅ Best EER: {best_eer:.2f}% — checkpoint saved")
        else:
            patience_ctr += 1
            if patience_ctr >= args.patience:
                print(f"\n  ⚡ Early stopping at epoch {epoch}")
                break

        torch.save({"epoch": epoch, "model": model.state_dict()},
                   ckpt_dir / "last_model.pt")

    print("\n  Loading best checkpoint for test evaluation...")
    ckpt = torch.load(ckpt_dir / "best_model.pt", map_location=device)
    model.load_state_dict(ckpt["model"])
    test_m = evaluate(model, test_loader, device, criterion)

    print("\n" + "=" * 60)
    print("  FINAL TEST RESULTS — PER LANGUAGE BREAKDOWN")
    print("=" * 60)
    print(f"  Overall → Acc:{test_m['accuracy']*100:.1f}%  "
          f"F1:{test_m['f1']:.3f}  AUC:{test_m['auc']:.3f}  EER:{test_m['eer']:.2f}%")
    print()
    for lang, lm in sorted(test_m.get("per_lang", {}).items()):
        status = "✅ GOOD" if lm["eer"] < 8 else "⚠️  NEEDS MORE DATA" if lm["eer"] < 18 else "❌ POOR"
        print(f"  {lang:<12}: EER={lm['eer']:.2f}%  AUC={lm['auc']:.4f}  "
              f"Acc={lm['accuracy']*100:.1f}%  [{status}]  (n={lm['n']:,})")
    print("=" * 60)

    with open(ckpt_dir / "multilingual_results.json", "w") as f:
        json.dump({"test": test_m, "best_val_eer": best_eer}, f, indent=2, default=str)
    print(f"\n  Results → {ckpt_dir}/multilingual_results.json")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data",           default="datasets/processed")
    p.add_argument("--datasets",       default=None,
                   help="Comma-separated list of dataset directory names to load in a specific order")
    p.add_argument("--epochs",         type=int,   default=60)
    p.add_argument("--batch_size",     type=int,   default=32)
    p.add_argument("--lr",             type=float, default=1e-4)
    p.add_argument("--workers",        type=int,   default=4)
    p.add_argument("--patience",       type=int,   default=10)
    p.add_argument("--checkpoint_dir", default="backend/training/checkpoints")
    args = p.parse_args()
    train(args)