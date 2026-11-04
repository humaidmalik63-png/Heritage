# Heritage Recognition Platform — Streamlit Cloud Deployment Guide

This guide details the procedure to deploy the **Unified Heritage Recognition Platform** (combining the local CLIP + FAISS recognition engine, Gemini 3.1 Flash-Lite fallback, Grounded RAG, and the full 7-screen interactive Web Experience) onto **Streamlit Community Cloud** ([share.streamlit.io](https://share.streamlit.io)).

---

## 🏛️ System Architecture in Streamlit

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Cloud Application                     │
│                             (streamlit_app.py)                         │
├───────────────────────────────────┬────────────────────────────────────┤
│ Tab 1: Cinematic Web Experience   │ Tab 2: Native Studio Console       │
│                                   │                                    │
│ • Custom 7-screen HTML5/CSS3/JS   │ • Native Camera input              │
│ • Bidirectional Streamlit Bridge  │ • Direct File Uploader             │
│ • Zero separate port dependency   │ • Grounded Architectural Q&A       │
│ • Zero network latency in-process │ • Model Metrics & Heritage Claims  │
├───────────────────────────────────┴────────────────────────────────────┤
│                       In-Process HeritageService                       │
│ • ViT-B/32 CLIP (OpenCLIP)                                             │
│ • Canonical 40-Vector FAISS FlatL2 Index                               │
│ • Gemini 3.1 Flash-Lite Fallback Engine (Bounded Backoff)              │
│ • Official UNESCO Architectural Evidence Citations                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 1-Click Deployment Steps

### 1. Push Latest Code to GitHub
Ensure all changes from `backend/`, `frontend/`, `data/`, `.streamlit/`, and `streamlit_app.py` are pushed to your GitHub repository:
- **Repository**: `https://github.com/humaidmalik63-png/Heritage`
- **Branch**: `main`

### 2. Sign In to Streamlit Community Cloud
1. Navigate to **[share.streamlit.io](https://share.streamlit.io)**.
2. Sign in using your GitHub account (`humaidmalik63-png`).

### 3. Create a New App
1. Click **"New app"** (or **"Create app"**).
2. Choose **"Deploy a public app from GitHub"**.
3. Configure the repository parameters:
   - **Repository**: `humaidmalik63-png/Heritage`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **App URL (optional)**: e.g. `heritage-ai.streamlit.app`

### 4. Configure Secrets (Gemini API Key)
Before clicking Deploy, click **"Advanced settings..."** at the bottom:
1. Select **Secrets**.
2. Enter your Gemini API key in TOML format:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
   *(Replace `"AIzaSy..."` with your actual Google Gemini API key).*
3. Under **Python version**, select **3.11** or **3.12**.
4. Click **Save**.

### 5. Deploy & Verify
1. Click **Deploy!**.
2. Streamlit Cloud will automatically clone the repository, install dependencies from `requirements.txt`, compile the FAISS index and CLIP embeddings, and launch the service.
3. Once loaded:
   - **Tab 1** displays the complete 7-screen Cinematic Web Experience embedded directly in the canvas.
   - **Tab 2** provides the native Streamlit Studio with live camera capture and interactive grounded Q&A.
   - **Tab 3** displays the Global Monument Catalogue with UNESCO citations.
   - **Tab 4** displays real-time health metrics and deployment diagnostics.

---

## ⚙️ Environment & Dependencies Reference

### Python Version
- Supported: Python 3.11 or 3.12

### Key Requirements in `requirements.txt`
```text
streamlit>=1.35.0
fastapi>=0.110.0
uvicorn>=0.29.0
torch
torchvision
open-clip-torch
faiss-cpu
pillow
python-dotenv
httpx
pydantic
```

### Streamlit Configuration (`.streamlit/config.toml`)
```toml
[theme]
primaryColor = "#d4af37"
backgroundColor = "#0b0c10"
secondaryBackgroundColor = "#12141a"
textColor = "#e8eaed"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10
enableStaticServing = true
```

---

## 🔒 Security & Invariants
- **API Key Confidentiality**: The API key is stored exclusively in Streamlit Secrets or local `.env`. It is never returned in client HTTP responses, logged, or exposed in the UI.
- **Local FAISS Index**: 40 canonical vectors with cosine similarity threshold $0.85$ and competitor margin $0.10$.
- **Fallback Engine**: Triggered strictly on visual ambiguity; bounded single retry with exponential jitter on HTTP 503; zero quota leakage on local rejections.

