
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class SqueezeExcitation(nn.Module):
    def __init__(self, channels: int, reduction: int = 8):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc   = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        b, c, _, _ = x.shape
        y = self.pool(x).view(b, c)
        return x * self.fc(y).view(b, c, 1, 1)


class MelCNNBranch(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.MaxPool2d(2), nn.Dropout2d(0.1),

            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.MaxPool2d(2), nn.Dropout2d(0.1),

            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.se   = SqueezeExcitation(128, 8)
        self.pool = nn.AdaptiveAvgPool2d((4, 4))
        self.fc   = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 512), nn.ReLU(inplace=True), nn.Dropout(0.3),
            nn.Linear(512, 256),
        )

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.layers(x)
        x = self.se(x)
        x = self.pool(x)
        return self.fc(x)


class MFCCBiLSTMBranch(nn.Module):
    def __init__(self, input_size=120, hidden=128, layers=3):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, layers,
                            batch_first=True, bidirectional=True, dropout=0.3)
        self.attn_fc = nn.Linear(hidden * 2, 1)
        self.fc      = nn.Sequential(
            nn.Linear(hidden * 2, 256), nn.ReLU(inplace=True), nn.Dropout(0.3),
        )

    def forward(self, x):
        x   = x.permute(0, 2, 1)
        out, _ = self.lstm(x)
        attn   = F.softmax(self.attn_fc(out), dim=1)
        ctx    = (out * attn).sum(dim=1)
        return self.fc(ctx)


class FusionClassifier(nn.Module):
    def __init__(self, embed_dim=256, num_classes=2):
        super().__init__()
        self.cross_attn = nn.MultiheadAttention(embed_dim, num_heads=4,
                                                batch_first=True, dropout=0.1)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim * 2, 512), nn.GELU(), nn.Dropout(0.4),
            nn.Linear(512, 128),           nn.GELU(), nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, mel_emb, mfcc_emb):
        q = mel_emb.unsqueeze(1)
        k = mfcc_emb.unsqueeze(1)
        attended, _ = self.cross_attn(q, k, k)
        attended     = attended.squeeze(1)
        mel_emb      = self.norm1(mel_emb + attended)
        mfcc_emb     = self.norm2(mfcc_emb)
        fused        = torch.cat([mel_emb, mfcc_emb], dim=-1)
        logits       = self.classifier(fused)
        return logits, F.softmax(logits, dim=-1)


class VoiceCloneDetector(nn.Module):
    def __init__(self):
        super().__init__()
        self.mel_branch  = MelCNNBranch()
        self.mfcc_branch = MFCCBiLSTMBranch()
        self.fusion      = FusionClassifier()

    def forward(self, mel, mfcc) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.fusion(self.mel_branch(mel), self.mfcc_branch(mfcc))

    def get_embedding(self, mel, mfcc) -> torch.Tensor:
        return torch.cat([self.mel_branch(mel), self.mfcc_branch(mfcc)], dim=-1)

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == "__main__":
    model = VoiceCloneDetector()
    mel   = torch.randn(4, 128, 500)
    mfcc  = torch.randn(4, 120, 500)
    logits, probs = model(mel, mfcc)
    print(f"Parameters  : {model.num_parameters:,}")
    print(f"Logits shape: {logits.shape}")
    print(f"Clone probs : {probs[:, 1].tolist()}")
    print("✅ Model OK")