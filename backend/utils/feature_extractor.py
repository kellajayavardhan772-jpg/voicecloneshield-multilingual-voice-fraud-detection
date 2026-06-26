
import io
import numpy as np
import librosa
import soundfile as sf
import torch
from pathlib import Path
from typing import Tuple, Union

SR         = 16000
N_MELS     = 128
N_FFT      = 512
HOP_LEN    = 160
WIN_LEN    = 400
MAX_SEC    = 5.0
N_MFCC     = 40


def load_audio(src: Union[bytes, str, Path]) -> np.ndarray:
    if isinstance(src, (bytes, bytearray)):
        audio, rate = sf.read(io.BytesIO(src))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        audio = audio.astype(np.float32)
        if rate != SR:
            audio = librosa.resample(audio, orig_sr=rate, target_sr=SR)
    else:
        audio, _ = librosa.load(str(src), sr=SR, mono=True)
        audio = audio.astype(np.float32)
    return audio


def normalize(audio: np.ndarray) -> np.ndarray:
    peak = np.max(np.abs(audio))
    return audio / (peak + 1e-8)


def pad_clip(audio: np.ndarray) -> np.ndarray:
    target = int(SR * MAX_SEC)
    return audio[:target] if len(audio) >= target else np.pad(audio, (0, target - len(audio)))


def extract_features(audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    audio = normalize(audio)
    audio = pad_clip(audio)

    mel = librosa.feature.melspectrogram(
        y=audio, sr=SR, n_mels=N_MELS,
        n_fft=N_FFT, hop_length=HOP_LEN, win_length=WIN_LEN, fmax=8000,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    log_mel = (log_mel - log_mel.min()) / (log_mel.max() - log_mel.min() + 1e-8)

    mfcc = librosa.feature.mfcc(y=audio, sr=SR, n_mfcc=N_MFCC,
                                  n_fft=N_FFT, hop_length=HOP_LEN)
    mfcc_full = np.vstack([mfcc,
                            librosa.feature.delta(mfcc),
                            librosa.feature.delta(mfcc, order=2)])

    return log_mel.astype(np.float32), mfcc_full.astype(np.float32)


def features_to_tensors(mel: np.ndarray,
                         mfcc: np.ndarray) -> Tuple[torch.Tensor, torch.Tensor]:
    return (torch.tensor(mel,  dtype=torch.float32).unsqueeze(0),
            torch.tensor(mfcc, dtype=torch.float32).unsqueeze(0))


def process_audio_bytes(data: bytes) -> Tuple[torch.Tensor, torch.Tensor]:
    audio = load_audio(data)
    mel, mfcc = extract_features(audio)
    return features_to_tensors(mel, mfcc)


def get_duration(data: bytes) -> float:
    audio = load_audio(data)
    return len(audio) / SR