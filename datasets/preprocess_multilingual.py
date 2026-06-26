
import os
import argparse
import random
import numpy as np
import pandas as pd
import librosa
import soundfile as sf
from pathlib import Path
from tqdm import tqdm
from typing import Optional, Tuple, List

TARGET_SR   = 16000
N_MELS      = 128
N_FFT       = 512
HOP_LEN     = 160
WIN_LEN     = 400
MAX_SEC     = 5.0
N_MFCC      = 40

BASE = Path(__file__).parent
RAW  = BASE / "raw"
PROC = BASE / "processed"
PROC.mkdir(parents=True, exist_ok=True)

def detect_lang(path: Path) -> str:
    p = str(path).lower()
    if any(x in p for x in ["telugu", "te_in", "/te/", "_te_"]):   return "te"
    if any(x in p for x in ["hindi",  "hi_in", "/hi/", "_hi_"]):   return "hi"
    if any(x in p for x in ["tamil",  "ta_in", "/ta/", "_ta_"]):   return "ta"
    if any(x in p for x in ["kannada","kn_in", "/kn/", "_kn_"]):   return "kn"
    if any(x in p for x in ["marathi","mr_in", "/mr/", "_mr_"]):   return "mr"
    if any(x in p for x in ["english","libri", "/en/", "libri"]):  return "en"
    return "unknown"

def load_audio(path: Path) -> Optional[np.ndarray]:
    try:
        audio, _ = librosa.load(str(path), sr=TARGET_SR, mono=True, duration=10.0)
        return audio.astype(np.float32)
    except Exception as e:
        return None

def normalize(audio: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(audio))
    return audio / (peak + 1e-8)

def pad_clip(audio: np.ndarray) -> np.ndarray:
    target = int(TARGET_SR * MAX_SEC)
    if len(audio) >= target:
        return audio[:target]
    return np.pad(audio, (0, target - len(audio)))

def augment_genuine(audio: np.ndarray) -> List[Tuple[np.ndarray, str]]:
    aug = [(audio.copy(), "clean")]

    phone = librosa.resample(audio, orig_sr=TARGET_SR, target_sr=8000)
    phone = librosa.resample(phone, orig_sr=8000,      target_sr=TARGET_SR)
    aug.append((phone, "phone_8khz"))

    noise_level = random.uniform(0.003, 0.018)
    noisy = audio + (np.random.randn(len(audio)).astype(np.float32) * noise_level)
    aug.append((np.clip(noisy, -1, 1), "bg_noise"))

    delay = int(TARGET_SR * 0.025)
    reverb = np.zeros_like(audio)
    reverb[delay:] += audio[:-delay] * 0.28
    aug.append((np.clip(audio + reverb, -1, 1), "reverb"))

    for speed in [0.95, 1.05]:
        sped = librosa.effects.time_stretch(audio, rate=speed)
        aug.append((sped, f"speed_{speed}"))

    pitched = librosa.effects.pitch_shift(audio, sr=TARGET_SR,
                                          n_steps=random.choice([-1, 1]))
    aug.append((pitched, "pitch_shift"))

    return aug


def augment_fake(audio: np.ndarray) -> List[Tuple[np.ndarray, str]]:
    aug = [(audio.copy(), "clean")]

    phone = librosa.resample(audio, orig_sr=TARGET_SR, target_sr=8000)
    phone = librosa.resample(phone, orig_sr=8000,      target_sr=TARGET_SR)
    aug.append((phone, "phone_compressed"))

    noisy = audio + (np.random.randn(len(audio)).astype(np.float32) * 0.006)
    aug.append((np.clip(noisy, -1, 1), "noise_masked"))

    return aug


def extract_features(audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    audio = normalize(audio)
    audio = pad_clip(audio)

    mel = librosa.feature.melspectrogram(
        y=audio, sr=TARGET_SR, n_mels=N_MELS,
        n_fft=N_FFT, hop_length=HOP_LEN, win_length=WIN_LEN, fmax=8000,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    log_mel = (log_mel - log_mel.min()) / (log_mel.max() - log_mel.min() + 1e-8)

    mfcc = librosa.feature.mfcc(y=audio, sr=TARGET_SR, n_mfcc=N_MFCC,
                                  n_fft=N_FFT, hop_length=HOP_LEN)
    mfcc_full = np.vstack([mfcc,
                            librosa.feature.delta(mfcc),
                            librosa.feature.delta(mfcc, order=2)])

    return log_mel.astype(np.float32), mfcc_full.astype(np.float32)


def collect_audio_files(src_dir: Path, label: int,
                         max_files: int = 20000) -> List[Tuple[Path, int]]:
    exts = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}
    files = []
    for ext in exts:
        files.extend(src_dir.rglob(f"*{ext}"))
    random.shuffle(files)
    return [(f, label) for f in files[:max_files]]


def collect_common_voice(cv_dir: Path, label: int = 0,
                          max_files: int = 20000) -> List[Tuple[Path, int]]:
    tsv = cv_dir / "validated.tsv"
    clips = cv_dir / "clips"
    if tsv.exists() and clips.exists():
        df = pd.read_csv(tsv, sep="\t", nrows=max_files)
        files = []
        for _, row in df.iterrows():
            p = clips / row["path"]
            if p.exists():
                files.append((p, label))
        print(f"    Common Voice: {len(files)} validated clips")
        return files
    return collect_audio_files(cv_dir, label, max_files)


def collect_asvspoof(spoof_dir: Path) -> List[Tuple[Path, int]]:
    samples = []
    for split in ["train", "dev", "eval"]:
        proto = spoof_dir / f"ASVspoof2019_LA_{split}" / "CM_protocol" / \
                f"ASVspoof2019.LA.cm.{split}.trl.txt"
        audio_dir = spoof_dir / f"ASVspoof2019_LA_{split}" / "flac"
        if not proto.exists():
            continue
        with open(proto) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                fid, lbl = parts[1], parts[4]
                label = 0 if lbl == "bonafide" else 1
                path = audio_dir / f"{fid}.flac"
                if path.exists():
                    samples.append((path, label))
    print(f"    ASVspoof2019: {len(samples)} samples")
    return samples


SOURCE_MAP = {
    "openslr_telugu":      (RAW/"genuine/telugu_openslr",      0, "te",  collect_audio_files,   True),
    "openslr_hindi":       (RAW/"genuine/hindi_openslr",       0, "hi",  collect_audio_files,   True),
    "openslr_tamil":       (RAW/"genuine/tamil_openslr",       0, "ta",  collect_audio_files,   True),
    "openslr_kannada":     (RAW/"genuine/kannada_openslr",     0, "kn",  collect_audio_files,   True),
    "openslr_marathi":     (RAW/"genuine/marathi_openslr",     0, "mr",  collect_audio_files,   True),
    "librispeech":         (RAW/"genuine/librispeech",         0, "en",  collect_audio_files,   True),
    "common_voice_telugu": (RAW/"genuine/common_voice_telugu", 0, "te",  collect_common_voice,  True),
    "common_voice_hindi":  (RAW/"genuine/common_voice_hindi",  0, "hi",  collect_common_voice,  True),
    "common_voice_tamil":  (RAW/"genuine/common_voice_tamil",  0, "ta",  collect_common_voice,  True),
    "kathbath_hindi":      (RAW/"genuine/kathbath_hindi",      0, "hi",  collect_audio_files,   True),
    "asvspoof2019":        (RAW/"fake/asvspoof2019",           1, "en",  collect_asvspoof,      False),
    "asvspoof2021":        (RAW/"fake/asvspoof2021",           1, "en",  collect_audio_files,   False),
    "wavefake":            (RAW/"fake/wavefake",               1, "en",  collect_audio_files,   False),
    "mlaad":               (RAW/"fake/mlaad",                  1, "multi",collect_audio_files,  False),
    "fake_or_real":        (RAW/"fake/fake_or_real",           1, "en",  collect_audio_files,   False),
    "coqui_multilingual":  (RAW/"fake/coqui_multilingual",     1, "multi",collect_audio_files,  False),
    "google_tts_indian":   (RAW/"fake/google_tts_indian",      1, "multi",collect_audio_files,  False),
    "elevenlabs_multilingual":(RAW/"fake/elevenlabs_multilingual",1,"multi",collect_audio_files,False),
}


def preprocess_source(name: str, augment: bool = True, max_files: int = 20000):
    if name not in SOURCE_MAP:
        print(f"  ✗ Unknown source: {name}")
        return

    src_dir, default_label, lang, collector, is_genuine = SOURCE_MAP[name]

    if not src_dir.exists() or not any(src_dir.rglob("*.wav")) and \
       not any(src_dir.rglob("*.flac")) and not any(src_dir.rglob("*.mp3")):
        print(f"  ✗ Not downloaded: {src_dir}")
        print(f"     Run: python download_multilingual.py --dataset {name}")
        return

    out_dir = PROC / name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Processing [{name}]  lang={lang}  label={default_label}")

    if collector == collect_asvspoof:
        samples = collect_asvspoof(src_dir)
    elif collector == collect_common_voice:
        samples = collect_common_voice(src_dir, default_label, max_files)
    else:
        samples = collect_audio_files(src_dir, default_label, max_files)

    if not samples:
        print(f"  ✗ No audio files found in {src_dir}")
        return

    aug_fn   = augment_genuine if is_genuine else augment_fake
    mels, mfccs, labels, metas = [], [], [], []

    for filepath, label in tqdm(samples, desc=name[:25]):
        audio = load_audio(filepath)
        if audio is None or len(audio) < TARGET_SR * 0.5:
            continue

        file_lang = detect_lang(filepath) if lang == "multi" else lang
        versions  = aug_fn(audio) if augment else [(audio, "clean")]

        for aug_audio, aug_name in versions:
            try:
                mel, mfcc = extract_features(aug_audio)
                mels.append(mel)
                mfccs.append(mfcc)
                labels.append(label)
                metas.append({
                    "file":        filepath.name,
                    "label":       label,
                    "language":    file_lang,
                    "source":      name,
                    "augmentation":aug_name,
                })
            except Exception:
                pass

    if not mels:
        print(f"  ✗ No valid features extracted")
        return

    mel_arr   = np.array(mels,   dtype=np.float32)
    mfcc_arr  = np.array(mfccs,  dtype=np.float32)
    label_arr = np.array(labels, dtype=np.int64)

    np.save(out_dir / "mel.npy",    mel_arr)
    np.save(out_dir / "mfcc.npy",   mfcc_arr)
    np.save(out_dir / "labels.npy", label_arr)
    pd.DataFrame(metas).to_csv(out_dir / "metadata.csv", index=False)

    g = int((label_arr == 0).sum())
    f = int((label_arr == 1).sum())
    print(f"\n  ✅ {name}")
    print(f"     Total: {len(label_arr):,}  |  Genuine: {g:,}  |  Fake: {f:,}")
    print(f"     Mel:  {mel_arr.shape}  |  MFCC: {mfcc_arr.shape}")
    print(f"     Saved: {out_dir}")


def show_stats():
    print("\n  Processed Dataset Statistics")
    print("=" * 70)
    print(f"  {'Source':<30} {'Total':>8} {'Genuine':>8} {'Fake':>8} {'Lang':<8}")
    print(f"  {'─'*30} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    total_s = total_g = total_f = 0
    for name in SOURCE_MAP:
        lf = PROC / name / "labels.npy"
        mf = PROC / name / "metadata.csv"
        if lf.exists():
            labels = np.load(lf)
            g  = int((labels == 0).sum())
            f  = int((labels == 1).sum())
            t  = len(labels)
            lang = "?"
            if mf.exists():
                df = pd.read_csv(mf, nrows=1)
                lang = df["language"].iloc[0] if "language" in df.columns else "?"
            print(f"  {name:<30} {t:>8,} {g:>8,} {f:>8,} {lang:<8}")
            total_s += t; total_g += g; total_f += f
        else:
            print(f"  {name:<30} {'— not processed —':>27}")
    print(f"  {'─'*70}")
    print(f"  {'TOTAL':<30} {total_s:>8,} {total_g:>8,} {total_f:>8,}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Multilingual Preprocessor")
    p.add_argument("--source",      type=str,  help="Process one source")
    p.add_argument("--all",         action="store_true")
    p.add_argument("--no-augment",  action="store_true")
    p.add_argument("--max-files",   type=int, default=20000)
    p.add_argument("--stats",       action="store_true")
    args = p.parse_args()

    augment = not args.no_augment

    if args.stats:
        show_stats()
    elif args.source:
        preprocess_source(args.source, augment, args.max_files)
    elif args.all:
        available = [n for n in SOURCE_MAP
                     if (SOURCE_MAP[n][0]).exists()]
        if not available:
            print("  No datasets downloaded yet. Run download_multilingual.py first.")
        for n in available:
            preprocess_source(n, augment, args.max_files)
    else:
        show_stats()