# 🛡️ VoiceClone Shield v2.0
### Multilingual AI Voice Fraud Detector — Telugu · Hindi · Tamil · English
**IBM Internship Project | Vignan's Institute of IT | Roll: 24L31A5481**

---

## ❌ Why v1.0 Was Inaccurate (and what we fixed)

| Problem | Old Dataset | New Dataset |
|---|---|---|
| Languages | English only | Telugu, Hindi, Tamil, Kannada, English |
| Genuine voices | Lab English speech | 5000+ real Indian speakers (Common Voice) |
| AI attack types | 2019 TTS only | ElevenLabs, XTTS-v2, Google Neural2, MLAAD |
| Indian AI fakes | None | MLAAD (1M samples in Indian languages) |
| Audio quality | Studio only | Phone-quality (8kHz), noisy, compressed |
| Result on Telugu | ~40% EER (random) | Target <5% EER |

---

## 🗂️ Project Structure

```
VoiceCloneShield_v2/
│
├── datasets/
│   ├── download_multilingual.py    ← Download all datasets (auto + manual guide)
│   ├── preprocess_multilingual.py  ← Audio → mel + MFCC tensors (all languages)
│   └── raw/
│       ├── genuine/                ← Real human voices (Telugu/Hindi/Tamil/English)
│       └── fake/                   ← AI-cloned voices (ASVspoof/WaveFake/MLAAD)
│
├── backend/
│   ├── main.py                     ← FastAPI server (analyze, compare, report)
│   ├── models/
│   │   └── voiceclone_model.py     ← CNN-BiLSTM + Cross-Attention model
│   ├── training/
│   │   └── train_multilingual.py   ← Language-aware training with per-lang EER
│   └── utils/
│       ├── feature_extractor.py    ← Audio → features at inference
│       └── ibm_watsonx.py          ← Watsonx Granite-13B integration
│
├── frontend/
│   └── app.py                      ← Streamlit dashboard (multilingual UI)
│
├── tests/
│   └── test_all.py                 ← 20 pytest unit tests
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Add your IBM Watsonx API key to .env
```

### 3. Download datasets
```bash
# List everything available
python datasets/download_multilingual.py --list

# Auto-download (OpenSLR Telugu/Hindi/Tamil + WaveFake + ASVspoof2021)
python datasets/download_multilingual.py --all-auto

# Self-generate Indian language AI fakes (FREE — uses Coqui XTTS-v2 locally)
python datasets/download_multilingual.py --self-collect-fakes --use-coqui

# Print manual download guide (Common Voice, MLAAD, etc.)
python datasets/download_multilingual.py --manual-guide
```

### 4. Preprocess
```bash
# Process all downloaded sources
python datasets/preprocess_multilingual.py --all

# Check what's been processed
python datasets/preprocess_multilingual.py --stats
```

### 5. Train
```bash
python backend/training/train_multilingual.py \
    --data datasets/processed \
    --epochs 60 \
    --batch_size 32

# Monitor with TensorBoard
tensorboard --logdir backend/training/checkpoints/tensorboard_logs
```

### 6. Run backend
```bash
uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 7. Run frontend
```bash
streamlit run frontend/app.py
# Dashboard: http://localhost:8501
```

### 8. Run tests
```bash
pytest tests/ -v
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check + language support |
| `POST` | `/api/v1/analyze` | Upload audio → fraud verdict |
| `POST` | `/api/v1/compare` | Compare two voices |
| `GET` | `/api/v1/report/{id}` | Get compliance report |
| `GET` | `/docs` | Swagger UI |

---

## 🎯 Supported Languages

| Language | Genuine Dataset | AI Fake Dataset |
|---|---|---|
| **Telugu** | OpenSLR 66 + Common Voice | MLAAD + Coqui XTTS-v2 |
| **Hindi** | KathBath (1218 speakers) + Common Voice | MLAAD + Google Neural2 |
| **Tamil** | OpenSLR 65 + Common Voice | MLAAD + Coqui XTTS-v2 |
| **Kannada** | OpenSLR 79 | MLAAD |
| **English** | LibriSpeech + VoxCeleb | ASVspoof + WaveFake |

---

## 🧠 Model Architecture

```
Raw Audio (WAV/MP3/FLAC/OGG) — any language
    ↓
Feature Extraction
    ├── Mel-spectrogram (128 bins)
    └── MFCC + Δ + ΔΔ     (120 dims)
    ↓                ↓
CNN Branch     BiLSTM Branch
(spectral      (temporal prosody
 texture)       patterns)
    ↓                ↓
   256-dim       256-dim
  embedding     embedding
         ↓    ↓
   Cross-Attention Fusion
         ↓
   FC Classifier (2 classes)
         ↓
  [Genuine | Clone]  + IBM Watsonx explanation
```

---

## 📊 Expected Results After Multilingual Training

| Language | Old EER | New EER | Improvement |
|---|---|---|---|
| Telugu | ~40% (random) | <5% | **8× better** |
| Hindi | ~35% | <4% | **9× better** |
| Tamil | ~45% | <6% | **7× better** |
| English | ~8% | <3% | **2.5× better** |

---

## 🔵 IBM Alignment

| IBM Product | How Used |
|---|---|
| **Watsonx.ai (Granite-13B)** | Fraud narrative generation + risk analysis |
| **Watsonx Trust & Transparency** | Audit trail per decision |
| **IBM Watson STT** | Audio transcript enrichment |
| **IBM Cloud Object Storage** | Dataset + checkpoint storage |
| **IBM Security QRadar** | Enterprise SIEM integration |

---

## 👤 Author
**Kella Jayavardhan** | Roll: 24L31A5481
Vignan's Institute of Information Technology, Visakhapatnam
Department of AI & Data Science | IBM Internship 2024
