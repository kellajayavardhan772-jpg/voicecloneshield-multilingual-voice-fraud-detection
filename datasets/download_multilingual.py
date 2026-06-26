
import os
import sys
import argparse
import zipfile
import tarfile
import subprocess
import requests
from pathlib import Path
from tqdm import tqdm

BASE    = Path(__file__).parent
RAW     = BASE / "raw"
GENUINE = RAW / "genuine"
FAKE    = RAW / "fake"

for d in [RAW, GENUINE, FAKE]:
    d.mkdir(parents=True, exist_ok=True)

GENUINE_DATASETS = {

    "openslr_telugu": {
        "language": "Telugu",
        "description": "OpenSLR 66 — native Telugu male + female studio recordings",
        "urls": [
            "https://www.openslr.org/resources/66/te_in_female.zip",
            "https://www.openslr.org/resources/66/te_in_male.zip",
        ],
        "output": GENUINE / "telugu_openslr",
        "size_gb": 1.2,
        "speakers": 2,
        "hours": 10.0,
        "label": 0,
        "auto": True,
    },

    "openslr_hindi": {
        "language": "Hindi",
        "description": "OpenSLR 103 — native Hindi male + female speakers",
        "urls": [
            "https://www.openslr.org/resources/103/hi_in_female.zip",
            "https://www.openslr.org/resources/103/hi_in_male.zip",
        ],
        "output": GENUINE / "hindi_openslr",
        "size_gb": 0.8,
        "speakers": 2,
        "hours": 8.0,
        "label": 0,
        "auto": True,
    },

    "openslr_tamil": {
        "language": "Tamil",
        "description": "OpenSLR 65 — native Tamil male + female speakers",
        "urls": [
            "https://www.openslr.org/resources/65/ta_in_female.zip",
            "https://www.openslr.org/resources/65/ta_in_male.zip",
        ],
        "output": GENUINE / "tamil_openslr",
        "size_gb": 0.7,
        "speakers": 2,
        "hours": 6.0,
        "label": 0,
        "auto": True,
    },

    "openslr_kannada": {
        "language": "Kannada",
        "description": "OpenSLR 79 — native Kannada female speaker",
        "urls": [
            "https://www.openslr.org/resources/79/kn_in_female.zip",
        ],
        "output": GENUINE / "kannada_openslr",
        "size_gb": 0.4,
        "speakers": 1,
        "hours": 4.0,
        "label": 0,
        "auto": True,
    },

    "openslr_marathi": {
        "language": "Marathi",
        "description": "OpenSLR 64 — native Marathi speakers",
        "urls": [
            "https://www.openslr.org/resources/64/mr_in_female.zip",
        ],
        "output": GENUINE / "marathi_openslr",
        "size_gb": 0.4,
        "speakers": 1,
        "hours": 3.5,
        "label": 0,
        "auto": True,
    },

    "librispeech_clean": {
        "language": "English",
        "description": "LibriSpeech train-clean-100 — 100h English audiobook speech",
        "urls": [
            "https://www.openslr.org/resources/12/train-clean-100.tar.gz",
        ],
        "output": GENUINE / "librispeech",
        "size_gb": 6.3,
        "speakers": 251,
        "hours": 100.0,
        "label": 0,
        "auto": True,
    },


    "common_voice_telugu": {
        "language": "Telugu",
        "description": "Mozilla Common Voice Telugu — 5000+ real speakers, natural speech",
        "manual": True,
        "manual_url": "https://commonvoice.mozilla.org/en/datasets",
        "manual_steps": [
            "1. Visit https://commonvoice.mozilla.org/en/datasets",
            "2. Create FREE account (email only)",
            "3. Select language: Telugu (te) → Click Download",
            "4. Extract and place clips/ folder at:",
            "   datasets/raw/genuine/common_voice_telugu/",
        ],
        "output": GENUINE / "common_voice_telugu",
        "size_gb": 8.0,
        "speakers": 5000,
        "hours": 80.0,
        "label": 0,
        "auto": False,
    },

    "common_voice_hindi": {
        "language": "Hindi",
        "description": "Mozilla Common Voice Hindi — 8000+ real speakers",
        "manual": True,
        "manual_url": "https://commonvoice.mozilla.org/en/datasets",
        "manual_steps": [
            "1. Visit https://commonvoice.mozilla.org/en/datasets",
            "2. Create FREE account",
            "3. Select language: Hindi (hi) → Click Download",
            "4. Extract clips/ folder to datasets/raw/genuine/common_voice_hindi/",
        ],
        "output": GENUINE / "common_voice_hindi",
        "size_gb": 12.0,
        "speakers": 8000,
        "hours": 150.0,
        "label": 0,
        "auto": False,
    },

    "common_voice_tamil": {
        "language": "Tamil",
        "description": "Mozilla Common Voice Tamil — 3000+ real speakers",
        "manual": True,
        "manual_url": "https://commonvoice.mozilla.org/en/datasets",
        "manual_steps": [
            "1. Visit https://commonvoice.mozilla.org/en/datasets",
            "2. Select language: Tamil (ta) → Download",
            "3. Extract to datasets/raw/genuine/common_voice_tamil/",
        ],
        "output": GENUINE / "common_voice_tamil",
        "size_gb": 5.0,
        "speakers": 3000,
        "hours": 60.0,
        "label": 0,
        "auto": False,
    },

    "kathbath_hindi": {
        "language": "Hindi",
        "description": "AI4Bharat KathBath — 1218 real Hindi speakers, 200h (BEST Hindi dataset)",
        "hf_dataset": "ai4bharat/kathbath",
        "hf_config": "hi",
        "output": GENUINE / "kathbath_hindi",
        "size_gb": 5.0,
        "speakers": 1218,
        "hours": 200.0,
        "label": 0,
        "auto": False,
        "pip_deps": ["datasets", "soundfile"],
    },
}

FAKE_DATASETS = {

    "asvspoof2019": {
        "language": "English",
        "description": "ASVspoof2019 Logical Access — 19 TTS + Voice Conversion attack types",
        "manual": True,
        "manual_url": "https://datashare.ed.ac.uk/handle/10283/3336",
        "manual_steps": [
            "1. Visit https://datashare.ed.ac.uk/handle/10283/3336",
            "2. Register for FREE academic access (takes 1-2 days)",
            "3. Download LA.zip (~8GB)",
            "4. Place at: datasets/raw/fake/asvspoof2019/",
        ],
        "output": FAKE / "asvspoof2019",
        "size_gb": 8.4,
        "samples": 108978,
        "attacks": ["A01–A19: Neural TTS, Griffin-Lim, WORLD vocoder, Voice Conversion"],
        "label": 1,
        "auto": False,
    },

    "asvspoof2021": {
        "language": "English",
        "description": "ASVspoof2021 DeepFake track — 611K modern deepfake samples",
        "urls": [
            "https://zenodo.org/record/4837263/files/ASVspoof2021_DF_eval_part00.tar.gz",
            "https://zenodo.org/record/4837263/files/ASVspoof2021_DF_eval_part01.tar.gz",
            "https://zenodo.org/record/4837263/files/ASVspoof2021_DF_eval_part02.tar.gz",
        ],
        "output": FAKE / "asvspoof2021",
        "size_gb": 110.0,
        "samples": 611829,
        "attacks": ["Neural codec", "GAN vocoder", "Flow-based TTS", "Voice conversion"],
        "label": 1,
        "auto": True,
    },

    "wavefake": {
        "language": "English",
        "description": "WaveFake — 6 GAN architectures (MelGAN, HiFi-GAN, WaveGlow, etc.)",
        "urls": [
            "https://zenodo.org/record/5645207/files/WaveFake.zip",
        ],
        "output": FAKE / "wavefake",
        "size_gb": 172.0,
        "samples": 117985,
        "attacks": ["MelGAN", "HiFi-GAN", "WaveGlow", "Parallel WaveGAN",
                    "Multi-Band MelGAN", "FullBand MelGAN"],
        "label": 1,
        "auto": True,
    },

    "mlaad": {
        "language": "Multi (Hindi, Tamil, Telugu, Kannada + 19 others)",
        "description": "MLAAD — 1M AI voices in 23 languages INCLUDING Indian languages ⭐ MOST IMPORTANT",
        "manual": True,
        "manual_url": "https://deepfake-total.com/mlaad",
        "manual_steps": [
            "1. Visit https://deepfake-total.com/mlaad",
            "2. Fill the data request form (academic/research use)",
            "3. You will receive download links by email",
            "4. Download language-specific archives:",
            "   - mlaad_hi.tar.gz  (Hindi AI voices)",
            "   - mlaad_te.tar.gz  (Telugu AI voices)",
            "   - mlaad_ta.tar.gz  (Tamil AI voices)",
            "   - mlaad_kn.tar.gz  (Kannada AI voices)",
            "5. Extract to: datasets/raw/fake/mlaad/",
            "",
            "WHY CRITICAL: This is the ONLY large dataset with AI-cloned",
            "Indian language voices. Without it, the model cannot detect",
            "Telugu/Hindi/Tamil voice cloning attacks.",
        ],
        "output": FAKE / "mlaad",
        "size_gb": 56.0,
        "samples": 1000000,
        "attacks": ["TTS in 23 languages", "Neural cloning in Indian languages"],
        "label": 1,
        "auto": False,
    },

    "fake_or_real": {
        "language": "English",
        "description": "FoR dataset — Google, Amazon, IBM Watson, Microsoft Azure TTS attacks",
        "manual": True,
        "manual_url": "https://bil.eecs.yorku.ca/datasets/",
        "manual_steps": [
            "1. Email York University BIL lab: bil@eecs.yorku.ca",
            "2. Request FoR dataset for academic research",
            "3. Extract to: datasets/raw/fake/fake_or_real/",
            "",
            "NOTE: Contains IBM Watson TTS as an attack vector —",
            "directly relevant for your IBM internship project!",
        ],
        "output": FAKE / "fake_or_real",
        "size_gb": 6.0,
        "samples": 198000,
        "attacks": ["Google TTS WaveNet", "Amazon Polly Neural",
                    "IBM Watson TTS", "Microsoft Azure Neural"],
        "label": 1,
        "auto": False,
    },
}

ALL_DATASETS = {**GENUINE_DATASETS, **FAKE_DATASETS}


INDIAN_SENTENCES = {
    "telugu": [
        "నమస్కారం, నేను మీ బ్యాంక్ నుండి మాట్లాడుతున్నాను",
        "మీ ఖాతా నిర్ధారించండి లేదా బ్లాక్ అవుతుంది",
        "ప్రభుత్వ పథకం కింద మీకు డబ్బులు వస్తాయి",
        "మీ OTP నంబర్ చెప్పండి",
        "ఇది TRAI నుండి చాలా ముఖ్యమైన కాల్",
        "మీ ఆధార్ నంబర్ నిర్ధారించండి",
        "24 గంటల్లో మీ ఖాతా బ్లాక్ అవుతుంది",
        "కస్టమర్ కేర్ నంబర్ కి కాల్ చేయండి",
    ],
    "hindi": [
        "नमस्ते, मैं आपके बैंक से बोल रहा हूँ",
        "आपका खाता ब्लॉक होने वाला है कृपया OTP दें",
        "TRAI की तरफ से यह महत्वपूर्ण सूचना है",
        "सरकारी योजना के तहत आपको 50,000 रुपये मिलेंगे",
        "अपना आधार नंबर सत्यापित करें",
        "24 घंटे में कार्रवाई न होने पर नंबर बंद होगा",
        "KYC अपडेट करें वरना खाता बंद होगा",
        "यह RBI का अधिकृत कॉल है",
    ],
    "tamil": [
        "வணக்கம், நான் உங்கள் வங்கியிலிருந்து பேசுகிறேன்",
        "உங்கள் கணக்கு தடுக்கப்படும் OTP கொடுங்கள்",
        "TRAI சார்பில் இது முக்கியமான அறிவிப்பு",
        "அரசு திட்டத்தில் உங்களுக்கு பணம் வரும்",
        "உங்கள் ஆதார் எண்ணை உறுதிப்படுத்துங்கள்",
        "24 மணி நேரத்தில் உங்கள் SIM நிறுத்தப்படும்",
    ],
    "english": [
        "Hello this is an automated call from your bank",
        "Your account has been flagged for suspicious activity",
        "Please verify your OTP to prevent account suspension",
        "This is TRAI calling regarding your mobile number",
        "You have won a prize of fifty thousand rupees",
        "Your KYC is pending please update immediately",
        "This is an urgent message from the Income Tax Department",
        "Press 1 to speak with our fraud prevention team",
    ],
}


def generate_coqui_fakes():
    try:
        from TTS.api import TTS
    except ImportError:
        print("  Installing Coqui TTS (this may take a few minutes)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "TTS"], check=True)
        from TTS.api import TTS

    out_dir = FAKE / "coqui_multilingual"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n  Loading XTTS-v2 (~2GB download on first run)...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    ref_map = {
        "te": GENUINE / "telugu_openslr",
        "hi": GENUINE / "hindi_openslr",
        "ta": GENUINE / "tamil_openslr",
        "en": GENUINE / "librispeech",
    }
    lang_code_map = {"telugu": "te", "hindi": "hi", "tamil": "ta", "english": "en"}
    count = 0

    for lang_name, sentences in INDIAN_SENTENCES.items():
        lang_code = lang_code_map[lang_name]
        lang_dir  = out_dir / lang_name
        lang_dir.mkdir(exist_ok=True)

        ref_dir  = ref_map.get(lang_code)
        ref_file = None
        if ref_dir and ref_dir.exists():
            wavs = list(ref_dir.rglob("*.wav")) + list(ref_dir.rglob("*.flac"))
            if wavs:
                ref_file = str(wavs[0])

        if not ref_file:
            print(f"  ⚠  No reference voice for {lang_name}. Download openslr_{lang_name} first.")
            continue

        print(f"\n  Generating {lang_name} AI clone voices...")
        for i, text in enumerate(sentences):
            out_path = lang_dir / f"coqui_{lang_name}_{i:04d}.wav"
            if out_path.exists():
                print(f"  ✓ [{lang_name}] {i+1}/{len(sentences)} — already exists")
                continue
            try:
                tts.tts_to_file(
                    text=text,
                    speaker_wav=ref_file,
                    language=lang_code,
                    file_path=str(out_path),
                )
                count += 1
                print(f"  ✓ [{lang_name}] {i+1}/{len(sentences)}: {out_path.name}")
            except Exception as e:
                print(f"  ✗ [{lang_name}] {i+1}: {e}")

    print(f"\n  ✅ Coqui: Generated {count} fake samples → {out_dir}")


def generate_google_tts_fakes():
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return

    try:
        from google.cloud import texttospeech
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install",
                        "google-cloud-texttospeech"], check=True)
        from google.cloud import texttospeech

    client  = texttospeech.TextToSpeechClient()
    out_dir = FAKE / "google_tts_indian"
    out_dir.mkdir(parents=True, exist_ok=True)

    voice_configs = {
        "telugu": [
            ("te-IN", "te-IN-Standard-A", "FEMALE"),
            ("te-IN", "te-IN-Standard-B", "MALE"),
        ],
        "hindi": [
            ("hi-IN", "hi-IN-Neural2-A", "FEMALE"),
            ("hi-IN", "hi-IN-Neural2-B", "MALE"),
            ("hi-IN", "hi-IN-Wavenet-A", "FEMALE"),
            ("hi-IN", "hi-IN-Wavenet-B", "MALE"),
        ],
        "tamil": [
            ("ta-IN", "ta-IN-Standard-A", "FEMALE"),
            ("ta-IN", "ta-IN-Standard-B", "MALE"),
        ],
        "english": [
            ("en-IN", "en-IN-Neural2-A", "FEMALE"),
            ("en-IN", "en-IN-Neural2-B", "MALE"),
        ],
    }

    count = 0
    for lang_name, voices in voice_configs.items():
        sentences = INDIAN_SENTENCES.get(lang_name, [])
        lang_dir  = out_dir / lang_name
        lang_dir.mkdir(exist_ok=True)

        for lang_code, voice_name, gender in voices:
            voice_dir = lang_dir / voice_name.replace("-", "_")
            voice_dir.mkdir(exist_ok=True)

            for i, text in enumerate(sentences):
                out_path = voice_dir / f"google_{i:04d}.wav"
                if out_path.exists():
                    continue
                try:
                    synthesis_input = texttospeech.SynthesisInput(text=text)
                    voice = texttospeech.VoiceSelectionParams(
                        language_code=lang_code, name=voice_name)
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                        sample_rate_hertz=16000,
                    )
                    response = client.synthesize_speech(
                        input=synthesis_input, voice=voice, audio_config=audio_config
                    )
                    with open(out_path, "wb") as f:
                        f.write(response.audio_content)
                    count += 1
                    print(f"  ✓ [{voice_name}] {text[:45]}...")
                except Exception as e:
                    print(f"  ✗ {voice_name}: {e}")

    print(f"\n  ✅ Google TTS: Generated {count} fake samples → {out_dir}")


def generate_elevenlabs_fakes():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return

    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "elevenlabs"], check=True)
        from elevenlabs.client import ElevenLabs

    client  = ElevenLabs(api_key=api_key)
    out_dir = FAKE / "elevenlabs_multilingual"
    out_dir.mkdir(parents=True, exist_ok=True)
    count   = 0

    for lang_name, sentences in INDIAN_SENTENCES.items():
        lang_dir = out_dir / lang_name
        lang_dir.mkdir(exist_ok=True)
        for i, text in enumerate(sentences[:5]):
            out_path = lang_dir / f"el_{lang_name}_{i:04d}.mp3"
            if out_path.exists():
                continue
            try:
                audio_gen = client.generate(
                    text=text,
                    voice="Rachel",
                    model="eleven_multilingual_v2",
                )
                with open(out_path, "wb") as f:
                    for chunk in audio_gen:
                        f.write(chunk)
                count += 1
                print(f"  ✓ [ElevenLabs/{lang_name}] {text[:45]}...")
            except Exception as e:
                print(f"  ✗ {e}")

    print(f"\n  ✅ ElevenLabs: Generated {count} fake samples → {out_dir}")



def _download_file(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  ✓ Already downloaded: {dest.name}")
        return True
    print(f"  ↓ {dest.name}")
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True,
                                          desc=dest.name[:35], leave=False) as bar:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                bar.update(len(chunk))
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print(f"     Direct URL: {url}")
        return False


def _extract(archive: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    print(f"  ⇢ Extracting {archive.name}...")
    try:
        if archive.suffix == ".zip":
            with zipfile.ZipFile(archive) as z:
                z.extractall(dest)
        elif archive.name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive) as t:
                t.extractall(dest)
        print(f"  ✓ Extracted → {dest}")
    except Exception as e:
        print(f"  ✗ Extract failed: {e}")


def _download_hf(name: str, info: dict):
    out = info["output"]
    out.mkdir(parents=True, exist_ok=True)
    for dep in info.get("pip_deps", []):
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

    print(f"  Loading HuggingFace: {info['hf_dataset']}...")
    try:
        from datasets import load_dataset
        import soundfile as sf
        import numpy as np
        ds = load_dataset(info["hf_dataset"], info.get("hf_config"), trust_remote_code=True)
        split = ds.get("train", ds[list(ds.keys())[0]])
        print(f"  Saving {len(split)} audio files to WAV...")
        for i, sample in enumerate(tqdm(split, desc=name)):
            p = out / f"{name}_{i:06d}.wav"
            if p.exists():
                continue
            try:
                audio = sample["audio"]
                sf.write(str(p), np.array(audio["array"]), audio["sampling_rate"])
            except Exception:
                pass
        print(f"  ✅ {name} → {out}")
    except Exception as e:
        print(f"  ✗ HuggingFace download error: {e}")


def download_dataset(name: str):
    info = ALL_DATASETS.get(name)
    if not info:
        print(f"  ✗ Unknown dataset: '{name}'. Run --list to see options.")
        return

    print(f"\n{'─'*58}")
    print(f"  Dataset  : {name}")
    print(f"  Language : {info.get('language','—')}")
    print(f"  Size     : ~{info.get('size_gb','?')} GB")
    print(f"  Desc     : {info['description']}")
    print(f"{'─'*58}")

    if info.get("manual"):
        print(f"\n  ⚠  MANUAL DOWNLOAD REQUIRED")
        print(f"     URL: {info['manual_url']}\n")
        for step in info.get("manual_steps", []):
            print(f"     {step}")
        return

    if info.get("hf_dataset"):
        _download_hf(name, info)
        return

    output = info["output"]
    output.mkdir(parents=True, exist_ok=True)
    for url in info.get("urls", []):
        fname   = url.split("/")[-1]
        archive = output / fname
        if _download_file(url, archive):
            _extract(archive, output)


def list_datasets():
    print("\n  VoiceClone Shield — Multilingual Dataset Registry")
    print("=" * 70)
    print(f"\n  GENUINE (Real Human Voices)  — label = 0")
    print(f"  {'Name':<30} {'Language':<20} {'Hours':>6}  {'Auto'}")
    print(f"  {'─'*30} {'─'*20} {'─'*6}  {'─'*5}")
    for n, i in GENUINE_DATASETS.items():
        auto = "✓ Auto" if i.get("auto") else "Manual"
        print(f"  {n:<30} {i.get('language',''):<20} {i.get('hours',0):>6.0f}h  {auto}")

    print(f"\n  FAKE (AI-Generated Voices)  — label = 1")
    print(f"  {'Name':<30} {'Language':<20} {'Samples':>8}  {'Auto'}")
    print(f"  {'─'*30} {'─'*20} {'─'*8}  {'─'*5}")
    for n, i in FAKE_DATASETS.items():
        auto = "✓ Auto" if i.get("auto") else "Manual"
        samp = f"{i.get('samples',0):,}" if i.get("samples") else "—"
        print(f"  {n:<30} {i.get('language',''):<20} {samp:>8}  {auto}")



def manual_guide():
    print("\n  MANUAL DOWNLOAD GUIDE — datasets requiring registration")
    print("=" * 60)
    for name, info in ALL_DATASETS.items():
        if info.get("manual"):
            print(f"\n  [{name}]  {info['description']}")
            print(f"  URL: {info['manual_url']}")
            for step in info.get("manual_steps", []):
                print(f"    {step}")


def verify():
    print("\n  Dataset Status Check")
    print("=" * 50)
    all_info = {**GENUINE_DATASETS, **FAKE_DATASETS}
    for name, info in all_info.items():
        out = info["output"]
        if out.exists() and any(out.rglob("*.wav")):
            n = len(list(out.rglob("*.wav"))) + len(list(out.rglob("*.flac"))) + len(list(out.rglob("*.mp3")))
            print(f"  ✅ {name:<35} {n:>6} files")
        else:
            print(f"  ❌ {name:<35} missing")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VoiceClone Shield — Multilingual Dataset Downloader")
    p.add_argument("--list",                action="store_true",  help="List all available datasets")
    p.add_argument("--verify",              action="store_true",  help="Check which datasets are downloaded")
    p.add_argument("--manual-guide",        action="store_true",  help="Print manual download instructions")
    p.add_argument("--dataset",             type=str,             help="Download one specific dataset")
    p.add_argument("--all-auto",            action="store_true",  help="Download all auto-downloadable datasets")
    p.add_argument("--self-collect-fakes",  action="store_true",  help="Generate fake voices using free APIs")
    p.add_argument("--use-coqui",           action="store_true",  help="Use Coqui XTTS-v2 (FREE, local)")
    p.add_argument("--use-google",          action="store_true",  help="Use Google Cloud TTS")
    p.add_argument("--use-elevenlabs",      action="store_true",  help="Use ElevenLabs API")
    args = p.parse_args()

    if args.list:
        list_datasets()
    elif args.verify:
        verify()
    elif args.manual_guide:
        manual_guide()
    elif args.dataset:
        download_dataset(args.dataset)
    elif args.all_auto:
        auto_datasets = [n for n, i in ALL_DATASETS.items()
                         if i.get("auto") and not i.get("manual") and not i.get("hf_dataset")]
        print(f"  Auto-downloading {len(auto_datasets)} datasets...")
        for name in auto_datasets:
            download_dataset(name)
    elif args.self_collect_fakes:
        if args.use_google:
            generate_google_tts_fakes()
        elif args.use_elevenlabs:
            generate_elevenlabs_fakes()
        else:
            generate_coqui_fakes()
    else:
        list_datasets()