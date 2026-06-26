
import streamlit as st
import requests
import json
import time
import plotly.graph_objects as go

st.set_page_config(
    page_title="VoiceClone Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API = "http://localhost:8000/api/v1"


with st.sidebar:
    st.markdown("## 🛡️ VoiceClone Shield")
    st.markdown("**IBM Internship Project**")
    st.markdown("Roll: 24L31A5481 | Vignan's IIT")
    st.divider()
    st.markdown("### Supported Languages")
    for lang, flag in [("Telugu","🇮🇳"), ("Hindi","🇮🇳"),
                        ("Tamil","🇮🇳"), ("Kannada","🇮🇳"), ("English","🇬🇧")]:
        st.markdown(f"{flag} {lang}")
    st.divider()
    st.markdown("### Detection Threshold")
    threshold = st.slider("Clone threshold", 0.5, 0.95, 0.72, 0.01)
    show_tech = st.checkbox("Show technical details", True)
    st.divider()

    try:
        h = requests.get(f"{API}/health", timeout=2).json()
        if h.get("status") == "healthy":
            st.success("✅ Backend online")
            if h.get("watsonx_connected"):
                st.info("🔵 IBM Watsonx active")
        else:
            st.error("❌ Backend unhealthy")
    except Exception:
        st.error("❌ Backend offline\n\n```\nuvicorn backend.main:app\n```")

tab1, tab2, tab3 = st.tabs(["🎙️ Analyze Audio", "🔄 Compare Speakers", "📊 Model Info"])

with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Upload Voice Sample")
        st.caption("Supports Telugu, Hindi, Tamil, Kannada, English voices")
        uploaded = st.file_uploader("Drop audio file here",
                                     type=["wav","mp3","flac","ogg"],
                                     help="Max 20MB")
        if uploaded:
            st.audio(uploaded)
            st.caption(f"📎 {uploaded.name}  |  {len(uploaded.getvalue())/1024:.1f} KB")
        analyze_btn = st.button("🔍 Analyze for Voice Cloning",
                                 use_container_width=True,
                                 disabled=(uploaded is None))

    with col_right:
        st.subheader("Result")

        if uploaded and analyze_btn:
            with st.spinner("Running CNN-BiLSTM inference..."):
                msgs = ["Extracting mel-spectrogram...",
                        "Running CNN branch...",
                        "Running BiLSTM branch...",
                        "Cross-attention fusion...",
                        "Querying IBM Watsonx..."]
                placeholder = st.empty()
                for i, msg in enumerate(msgs):
                    placeholder.caption(f"⟳ {msg}")
                    time.sleep(0.4)
                placeholder.empty()

                try:
                    files = {"file": (uploaded.name, uploaded.getvalue(),
                                      f"audio/{uploaded.name.split('.')[-1]}")}
                    resp  = requests.post(f"{API}/analyze", files=files, timeout=30)

                    if resp.status_code == 200:
                        d = resp.json()
                        cp  = d["clone_probability"]
                        v   = d["verdict"]
                        cls = ("verdict-clone" if v == "CLONE_DETECTED" else
                               "verdict-sus"   if v == "SUSPICIOUS"    else "verdict-ok")
                        icon = "🚨" if v=="CLONE_DETECTED" else "⚠️" if v=="SUSPICIOUS" else "✅"
                        label= ("AI Clone Detected" if v=="CLONE_DETECTED" else
                                "Suspicious Voice"  if v=="SUSPICIOUS"    else "Genuine Voice")
                        color= ("#FF3A5C" if v=="CLONE_DETECTED" else
                                "#FFB800" if v=="SUSPICIOUS"     else "#39FF7A")


                        st.markdown("---")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Duration",  f"{d.get('duration_sec','—')}s")
                        m2.metric("Latency",   f"{d.get('latency_ms','—')}ms")
                        m3.metric("Risk",      d.get("risk_level","—"))
                        m4.metric("Report ID", d.get("report_id","—")[:10])

                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=cp * 100,
                            title={"text": "Clone Probability (%)"},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar":  {"color": color},
                                "steps": [
                                    {"range": [0, 45],  "color": "#071F12"},
                                    {"range": [45, 72], "color": "#2A1C08"},
                                    {"range": [72, 100],"color": "#2A0A0E"},
                                ],
                                "threshold": {"line": {"color":"white","width":3},
                                              "thickness":0.75, "value": threshold*100},
                            },
                        ))
                        fig.update_layout(height=260, paper_bgcolor="#05070D",
                                          font_color="#E8EDF8",
                                          margin=dict(t=40,b=10,l=20,r=20))
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("#### 🔵 IBM Watsonx Analysis")
                        st.info(d.get("explanation", "—"))

                        if show_tech:
                            with st.expander("🔬 Technical Details"):
                                sa = d.get("spectral_anomalies", [])
                                pf = d.get("prosody_flags", [])
                                if sa:
                                    st.markdown("**Spectral Anomalies:**")
                                    for a in sa: st.markdown(f"  • {a}")
                                if pf:
                                    st.markdown("**Prosody Flags:**")
                                    for f_ in pf: st.markdown(f"  • {f_}")
                                st.caption(f"Session: `{d.get('session_id','—')}`")

                        sid = d.get("session_id")
                        if sid:
                            try:
                                r2 = requests.get(f"{API}/report/{sid}")
                                if r2.ok:
                                    st.download_button(
                                        "📄 Download Compliance Report (JSON)",
                                        data=json.dumps(r2.json(), indent=2),
                                        file_name=f"VCS_{d.get('report_id','report')}.json",
                                        mime="application/json",
                                    )
                            except Exception:
                                pass
                    else:
                        st.error(f"API Error {resp.status_code}: {resp.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend not running.\n\n"
                             "Start it: `uvicorn backend.main:app --port 8000`")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("Upload audio and click analyze to begin.")

with tab2:
    st.subheader("Speaker Identity Comparison")
    st.caption("Check if two voice samples belong to the same speaker")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Reference Voice (enrolled)**")
        f1 = st.file_uploader("Reference", type=["wav","mp3","flac","ogg"], key="f1")
        if f1: st.audio(f1)
    with c2:
        st.markdown("**Test Voice (to verify)**")
        f2 = st.file_uploader("Test voice", type=["wav","mp3","flac","ogg"], key="f2")
        if f2: st.audio(f2)

    if f1 and f2:
        if st.button("🔍 Compare Speaker Identity", use_container_width=True):
            with st.spinner("Computing speaker embeddings..."):
                try:
                    files = {"file1": (f1.name, f1.getvalue()),
                             "file2": (f2.name, f2.getvalue())}
                    r = requests.post(f"{API}/compare", files=files, timeout=30)
                    if r.ok:
                        d   = r.json()
                        sim = d["similarity_score"]
                        same= d["same_speaker"]
                        col = "#39FF7A" if same else "#FF3A5C"
                    else:
                        st.error(f"API error: {r.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab3:
    st.subheader("Model Architecture & Training")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🧠 Model Architecture")
        st.markdown("""
        The system uses a two-branch neural network architecture:
        - **CNN Branch (with SE block)**: Analyzes spatial frequency patterns from Mel-spectrogram features (128, T).
        - **BiLSTM Branch (with Attention Pooling)**: Processes temporal features from MFCC, Delta, and Delta-Delta features (120, T).
        - **Cross-Attention Fusion**: Inter-correlates spectral and temporal features to extract cohesive fraud indicators.
        - **Fully Connected Classifier**: Computes the final probability of the voice being genuine vs. an AI clone.
        """)
    with c2:
        st.markdown("### 📊 Training & Performance")
        st.markdown("""
        - **Training Datasets**: ASVspoof 2019, ASVspoof 2021, WaveFake.
        - **Metrics**:
          - Target Accuracy: > 95%
          - Target EER (Equal Error Rate): < 5%
          - Target Latency: < 300ms
        - **Explainable AI Integration**: Powered by IBM Watsonx Granite-13B model for generating compliance audits and security reports.
        """)

    st.divider()