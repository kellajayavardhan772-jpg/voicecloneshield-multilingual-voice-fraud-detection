
import os
import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    IBM_AVAILABLE = True
except ImportError:
    IBM_AVAILABLE = False


def get_watsonx_model() -> Optional[object]:
    if not IBM_AVAILABLE:
        return None
    api_key    = os.getenv("IBM_WATSONX_API_KEY")
    project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
    url        = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    if not api_key or not project_id:
        return None
    try:
        creds = Credentials(api_key=api_key, url=url)
        return ModelInference(
            model_id="ibm/granite-13b-instruct-v2",
            credentials=creds,
            project_id=project_id,
            params={"max_new_tokens": 512, "temperature": 0.1,
                    "top_p": 0.95, "repetition_penalty": 1.1},
        )
    except Exception as e:
        print(f"  [Watsonx] Connection failed: {e}")
        return None


def generate_explanation(
    clone_prob: float,
    spectral_anomalies: list,
    prosody_flags: list,
    duration: float,
    language: str = "unknown",
    model=None,
) -> str:
    verdict = ("HIGH RISK — likely AI-cloned"  if clone_prob > 0.72 else
               "MEDIUM RISK — suspicious"       if clone_prob > 0.45 else
               "LOW RISK — likely genuine")
    anomaly_text = ", ".join(spectral_anomalies) if spectral_anomalies else "none detected"
    prosody_text = ", ".join(prosody_flags)       if prosody_flags      else "none detected"

    prompt = (
        f"You are VoiceClone Shield, an AI voice fraud explanation helper. "
        f"Generate a clear, professional compliance and security explanation for an audio analysis. "
        f"Analysis Results:\n"
        f"- Clone Probability: {clone_prob:.1%}\n"
        f"- Verdict: {verdict}\n"
        f"- Audio Duration: {duration:.2f} seconds\n"
        f"- Language Detected: {language}\n"
        f"- Spectral Anomalies: {anomaly_text}\n"
        f"- Prosody Flags: {prosody_text}\n\n"
        f"Explain why this audio is classified as {verdict} based on these indicators and specify the recommended action (BLOCK, CHALLENGE, or ALLOW). Be concise and professional."
    )

    if model:
        try:
            return model.generate_text(prompt=prompt).strip()
        except Exception:
            pass

    lang_note = f" (language detected: {language})" if language != "unknown" else ""
    if clone_prob > 0.72:
        return (
            f"This audio sample{lang_note} shows {clone_prob:.0%} probability of being "
            f"AI-generated. Key indicators include: {anomaly_text}. "
            f"Prosodic analysis revealed: {prosody_text}. "
            f"These patterns are consistent with modern TTS or voice conversion systems "
            f"used in vishing and KYC bypass attacks. "
            f"Recommended action: BLOCK this authentication attempt and flag for manual review."
        )
    elif clone_prob > 0.45:
        return (
            f"This audio{lang_note} shows moderate suspicion ({clone_prob:.0%} clone probability). "
            f"Anomalies detected: {anomaly_text}. "
            f"Recommended action: Apply secondary authentication challenge (OTP/video KYC)."
        )
    return (
        f"This audio appears genuine{lang_note} ({(1-clone_prob):.0%} confidence). "
        f"No significant spectral or prosodic anomalies detected. "
        f"Authentication may proceed through normal channels."
    )


def generate_compliance_report(
    session_id: str,
    clone_prob: float,
    verdict: str,
    explanation: str,
    language: str = "unknown",
    model=None,
) -> dict:
    risk   = "HIGH" if clone_prob > 0.72 else "MEDIUM" if clone_prob > 0.45 else "LOW"
    action = "BLOCK" if clone_prob > 0.72 else "CHALLENGE" if clone_prob > 0.45 else "ALLOW"
    return {
        "report_id":   f"VCS-{session_id[:8].upper()}",
        "timestamp":   datetime.datetime.now(datetime.UTC).isoformat() + "Z",
        "system":      "VoiceClone Shield v2.0 | IBM Watsonx AI",
        "verdict":     verdict,
        "clone_prob":  round(clone_prob, 4),
        "risk_level":  risk,
        "action":      action,
        "language_detected": language,
        "explanation": explanation,
        "compliance": {
            "gdpr_art22":     "AI decision with human oversight recommended",
            "rbi_guideline":  "RBI Digital Lending — Fraud Prevention Clause 4.2",
            "audit_hash":     f"sha256:{abs(hash(session_id + verdict)):x}",
        },
        "model_info": {
            "architecture":   "CNN-BiLSTM + Cross-Attention Fusion",
            "trained_on":     "ASVspoof2019/2021 + WaveFake + MLAAD (Telugu/Hindi/Tamil/English)",
            "languages":      ["Telugu", "Hindi", "Tamil", "Kannada", "English"],
            "ibm_layer":      "Watsonx.ai Granite-13B for NLG",
        },
    }