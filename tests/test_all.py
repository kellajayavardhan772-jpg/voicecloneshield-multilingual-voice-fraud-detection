
import sys
import numpy as np
# pyrefly: ignore [missing-import]
import pytest
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.voiceclone_model import VoiceCloneDetector, MelCNNBranch, MFCCBiLSTMBranch
from backend.utils.feature_extractor import (
    normalize, pad_clip, extract_features, features_to_tensors, SR, MAX_SEC,
)
from backend.utils.ibm_watsonx import generate_explanation, generate_compliance_report


class TestVoiceCloneDetector:

    def setup_method(self):
        self.model = VoiceCloneDetector()
        self.model.eval()
        self.mel  = torch.randn(4, 128, 500)
        self.mfcc = torch.randn(4, 120, 500)

    def test_output_shape(self):
        logits, probs = self.model(self.mel, self.mfcc)
        assert logits.shape == (4, 2)
        assert probs.shape  == (4, 2)

    def test_probabilities_sum_to_one(self):
        _, probs = self.model(self.mel, self.mfcc)
        assert torch.allclose(probs.sum(dim=-1), torch.ones(4), atol=1e-5)

    def test_probabilities_in_range(self):
        _, probs = self.model(self.mel, self.mfcc)
        assert (probs >= 0).all() and (probs <= 1).all()

    def test_embedding_shape(self):
        emb = self.model.get_embedding(self.mel, self.mfcc)
        assert emb.shape == (4, 512)

    def test_num_parameters_positive(self):
        assert self.model.num_parameters > 0

    def test_gradient_flow(self):
        self.model.train()
        logits, _ = self.model(self.mel, self.mfcc)
        logits.sum().backward()
        for name, p in self.model.named_parameters():
            if p.requires_grad:
                assert p.grad is not None, f"No gradient: {name}"

    def test_single_sample(self):
        mel1  = torch.randn(1, 128, 500)
        mfcc1 = torch.randn(1, 120, 500)
        _, probs = self.model(mel1, mfcc1)
        assert 0.0 <= float(probs[0, 1].detach()) <= 1.0

    def test_different_time_lengths(self):
        for T in [200, 500, 800]:
            mel  = torch.randn(2, 128, T)
            mfcc = torch.randn(2, 120, T)
            _, probs = self.model(mel, mfcc)
            assert probs.shape == (2, 2)


class TestMelCNNBranch:
    def test_output_shape(self):
        branch = MelCNNBranch()
        out = branch(torch.randn(4, 128, 500))
        assert out.shape == (4, 256)


class TestMFCCBiLSTMBranch:
    def test_output_shape(self):
        branch = MFCCBiLSTMBranch()
        out = branch(torch.randn(4, 120, 500))
        assert out.shape == (4, 256)


class TestFeatureExtractor:

    def test_normalize_peak_is_one(self):
        audio = np.array([0.3, -0.8, 0.5, -0.2], dtype=np.float32)
        assert abs(np.max(np.abs(normalize(audio))) - 1.0) < 1e-5

    def test_normalize_silence_no_nan(self):
        assert not np.any(np.isnan(normalize(np.zeros(100, dtype=np.float32))))

    def test_pad_short_audio(self):
        audio = np.zeros(SR, dtype=np.float32)
        assert len(pad_clip(audio)) == int(SR * MAX_SEC)

    def test_clip_long_audio(self):
        audio = np.zeros(SR * 10, dtype=np.float32)
        assert len(pad_clip(audio)) == int(SR * MAX_SEC)

    def test_mel_shape(self):
        audio = np.random.randn(SR * 3).astype(np.float32)
        mel, _ = extract_features(audio)
        assert mel.shape[0] == 128

    def test_mfcc_shape(self):
        audio = np.random.randn(SR * 3).astype(np.float32)
        _, mfcc = extract_features(audio)
        assert mfcc.shape[0] == 120

    def test_mel_in_0_1(self):
        audio = np.random.randn(SR * 3).astype(np.float32)
        mel, _ = extract_features(audio)
        assert mel.min() >= -1e-5 and mel.max() <= 1.0 + 1e-5

    def test_time_dims_match(self):
        audio = np.random.randn(SR * 3).astype(np.float32)
        mel, mfcc = extract_features(audio)
        assert mel.shape[1] == mfcc.shape[1]

    def test_tensors_shape(self):
        audio = np.random.randn(SR * 3).astype(np.float32)
        mel, mfcc = extract_features(audio)
        mt, mc = features_to_tensors(mel, mfcc)
        assert mt.shape[0] == 1
        assert mc.shape[0] == 1
        assert isinstance(mt, torch.Tensor)


class TestIBMWatsonx:

    def test_explanation_high_risk(self):
        exp = generate_explanation(0.91, ["GAN artifacts"], ["flat intonation"], 3.5,
                                   language="te", model=None)
        assert isinstance(exp, str) and len(exp) > 20

    def test_explanation_genuine(self):
        exp = generate_explanation(0.08, [], [], 4.0, language="hi", model=None)
        assert "genuine" in exp.lower() or "authentic" in exp.lower() or "normal" in exp.lower()

    def test_explanation_medium_risk(self):
        exp = generate_explanation(0.55, ["harmonic distortion"], [], 2.8,
                                   language="ta", model=None)
        assert isinstance(exp, str) and len(exp) > 10

    def test_compliance_report_keys(self):
        report = generate_compliance_report(
            "test-session-abc123", 0.88, "CLONE_DETECTED",
            "Test explanation", "te", None,
        )
        for key in ["report_id", "timestamp", "verdict", "risk_level",
                    "action", "compliance", "model_info"]:
            assert key in report, f"Missing: {key}"

    def test_report_high_risk_action(self):
        r = generate_compliance_report("s1", 0.90, "CLONE_DETECTED", "exp", "hi", None)
        assert r["risk_level"] == "HIGH"
        assert r["action"]     == "BLOCK"

    def test_report_low_risk_action(self):
        r = generate_compliance_report("s2", 0.10, "GENUINE", "exp", "en", None)
        assert r["risk_level"] == "LOW"
        assert r["action"]     == "ALLOW"

    def test_report_language_recorded(self):
        r = generate_compliance_report("s3", 0.50, "SUSPICIOUS", "exp", "ta", None)
        assert r["language_detected"] == "ta"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])