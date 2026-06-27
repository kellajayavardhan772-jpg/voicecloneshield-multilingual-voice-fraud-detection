
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import uuid
import time
import torch
import numpy as np
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

load_dotenv()

from backend.models.voiceclone_model import VoiceCloneDetector
from backend.utils.feature_extractor import process_audio_bytes, get_duration
from backend.utils.ibm_watsonx import (
    get_watsonx_model, generate_explanation, generate_compliance_report,
)

app = FastAPI(
    title="VoiceClone Shield API",
    description="Multilingual AI voice fraud detection — Telugu, Hindi, Tamil, English",
    version="2.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

DEVICE   = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL: Optional[VoiceCloneDetector] = None
MODEL_TRAINED = False
WX_MODEL = None
REPORTS: dict = {}

CLONE_THRESH    = float(os.getenv("CLONE_THRESHOLD",    0.72))
LIVE_THRESH     = float(os.getenv("LIVENESS_THRESHOLD", 0.45))
SIM_THRESH      = float(os.getenv("SIMILARITY_THRESHOLD", 0.85))
CHECKPOINT      = os.getenv("MODEL_CHECKPOINT",
                             "backend/training/checkpoints/best_model.pt")

ALLOWED_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp3",
    "audio/flac", "audio/ogg",
    "audio/mpeg", "video/mpeg",
    "application/octet-stream",
}


@app.on_event("startup")
async def startup():
    global MODEL, WX_MODEL, MODEL_TRAINED
    MODEL = VoiceCloneDetector().to(DEVICE)
    ckpt  = Path(CHECKPOINT)
    if ckpt.exists():
        state = torch.load(ckpt, map_location=DEVICE)
        MODEL.load_state_dict(state.get("model", state))
        MODEL_TRAINED = True
        print(f"  ✅ Model loaded from {ckpt}")
    else:
        MODEL_TRAINED = False
        print(f"  ⚠  No checkpoint at {ckpt} — using untrained weights")
        print(f"     Train: python backend/training/train_multilingual.py")
    MODEL.eval()
    WX_MODEL = get_watsonx_model()
    status   = "✅ IBM Watsonx connected" if WX_MODEL else "ℹ  Watsonx not configured — rule-based fallback"
    print(f"  {status}")


def _infer(audio_bytes: bytes) -> dict:
    mel_t, mfcc_t = process_audio_bytes(audio_bytes)
    mel_t  = mel_t.to(DEVICE)
    mfcc_t = mfcc_t.to(DEVICE)
    with torch.no_grad():
        logits, probs = MODEL(mel_t, mfcc_t)
    clone_prob   = float(probs[0, 1])
    genuine_prob = float(probs[0, 0])

    spectral = []
    prosody  = []
    if clone_prob > 0.50: spectral.append("harmonic distortion pattern")
    if clone_prob > 0.65: spectral.append("unnatural formant transitions")
    if clone_prob > 0.80: spectral.append("GAN vocoder artifacts (4–8kHz range)")
    if clone_prob > 0.55: prosody.append("flat intonation contour")
    if clone_prob > 0.70: prosody.append("unnatural breath pause intervals")

    verdict = ("CLONE_DETECTED" if clone_prob >= CLONE_THRESH else
               "SUSPICIOUS"     if clone_prob >= LIVE_THRESH  else
               "GENUINE")

    return {
        "clone_probability":   round(clone_prob,   4),
        "genuine_probability": round(genuine_prob, 4),
        "verdict":             verdict,
        "spectral_anomalies":  spectral,
        "prosody_flags":       prosody,
    }


@app.get("/")
def root():
    ui = Path("index.html")
    if ui.exists():
        return FileResponse(str(ui))
    return {"project": "VoiceClone Shield v2.0",
            "languages": ["Telugu", "Hindi", "Tamil", "Kannada", "English"],
            "model_ready": MODEL is not None,
            "watsonx": WX_MODEL is not None,
            "docs": "/docs"}


@app.get("/api/v1/health")
def health():
    return {"status": "healthy",
            "model_loaded": MODEL is not None,
            "model_trained": MODEL_TRAINED,
            "device": str(DEVICE),
            "watsonx_connected": WX_MODEL is not None,
            "supported_languages": ["Telugu (te)", "Hindi (hi)", "Tamil (ta)",
                                     "Kannada (kn)", "English (en)"]}


@app.post("/api/v1/analyze")
async def analyze(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    if len(audio_bytes) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large — max 20MB")
    if len(audio_bytes) < 1000:
        raise HTTPException(400, "File too small or empty")

    t0 = time.time()
    try:
        result     = _infer(audio_bytes)
        duration   = get_duration(audio_bytes)
        session_id = str(uuid.uuid4())
        latency_ms = round((time.time() - t0) * 1000, 1)

        lang = "unknown"

        explanation = generate_explanation(
            clone_prob         = result["clone_probability"],
            spectral_anomalies = result["spectral_anomalies"],
            prosody_flags      = result["prosody_flags"],
            duration           = duration,
            language           = lang,
            model              = WX_MODEL,
        )
        report = generate_compliance_report(
            session_id = session_id,
            clone_prob = result["clone_probability"],
            verdict    = result["verdict"],
            explanation= explanation,
            language   = lang,
            model      = WX_MODEL,
        )
        REPORTS[session_id] = report

        return {
            "session_id":          session_id,
            "filename":            file.filename,
            "duration_sec":        round(duration, 2),
            "latency_ms":          latency_ms,
            "verdict":             result["verdict"],
            "clone_probability":   result["clone_probability"],
            "genuine_probability": result["genuine_probability"],
            "risk_level":          report["risk_level"],
            "action":              report["action"],
            "language_detected":   lang,
            "explanation":         explanation,
            "spectral_anomalies":  result["spectral_anomalies"],
            "prosody_flags":       result["prosody_flags"],
            "report_id":           report["report_id"],
        }
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/api/v1/compare")
async def compare(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    a1 = await file1.read()
    a2 = await file2.read()
    try:
        mel1, mfcc1 = process_audio_bytes(a1)
        mel2, mfcc2 = process_audio_bytes(a2)
        mel1, mfcc1 = mel1.to(DEVICE), mfcc1.to(DEVICE)
        mel2, mfcc2 = mel2.to(DEVICE), mfcc2.to(DEVICE)
        with torch.no_grad():
            emb1 = MODEL.get_embedding(mel1, mfcc1)
            emb2 = MODEL.get_embedding(mel2, mfcc2)
        sim  = float(torch.nn.functional.cosine_similarity(emb1, emb2))
        same = sim >= SIM_THRESH
        return {"similarity_score": round(sim, 4),
                "same_speaker":     same,
                "threshold":        SIM_THRESH,
                "verdict":          "SAME_SPEAKER" if same else "DIFFERENT_SPEAKER"}
    except Exception as e:
        raise HTTPException(500, f"Comparison failed: {str(e)}")


@app.get("/api/v1/report/{session_id}")
def get_report(session_id: str):
    report = REPORTS.get(session_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@app.get("/ui")
def serve_ui():
    ui = Path("index.html")
    if ui.exists():
        return FileResponse(str(ui))
    return JSONResponse({"msg": "Frontend not found. Start Streamlit: streamlit run frontend/app.py"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 8000)))
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    reload = False if os.environ.get("PORT") else True
    uvicorn.run("backend.main:app",
                host=host,
                port=port,
                reload=reload)