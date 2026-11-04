"""
Visual Heritage Recognition and Grounded Cultural Discovery Platform
Integrated Streamlit Application & Cloud Deployment Entrypoint
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import socket
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

# ── Ensure Project Root & Environment ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load project-root .env reliably
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(override=False)
except ImportError:
    pass

import streamlit as st
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Heritage Discovery — Visual Monument Recognition",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Cinematic Styling ──────────────────────────────────────────────────
st.markdown("""
<style>
    /* Obsidian & Bronze Cinematic Palette */
    .stApp {
        background-color: #050608;
        color: #F2F4F7;
    }
    .main-header {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #F2F4F7;
        margin-bottom: 0.2rem;
        letter-spacing: -0.01em;
    }
    .sub-header {
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 0.95rem;
        color: rgba(235, 240, 248, 0.7);
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(13, 16, 23, 0.9);
        border: 1px solid rgba(232, 209, 203, 0.15);
        border-radius: 4px;
        padding: 1rem;
        text-align: center;
    }
    .metric-card-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #E8D1CB;
        font-family: 'Playfair Display', Georgia, serif;
    }
    .metric-card-lbl {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(235, 240, 248, 0.55);
        margin-top: 0.25rem;
    }
    .badge-local {
        display: inline-block;
        background: rgba(143, 191, 159, 0.15);
        color: #8FBF9F;
        border: 1px solid rgba(143, 191, 159, 0.4);
        padding: 0.3rem 0.8rem;
        border-radius: 2px;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .badge-external {
        display: inline-block;
        background: rgba(232, 209, 203, 0.15);
        color: #E8D1CB;
        border: 1px solid rgba(232, 209, 203, 0.4);
        padding: 0.3rem 0.8rem;
        border-radius: 2px;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .badge-unavailable {
        display: inline-block;
        background: rgba(239, 107, 107, 0.15);
        color: #EF6B6B;
        border: 1px solid rgba(239, 107, 107, 0.4);
        padding: 0.3rem 0.8rem;
        border-radius: 2px;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .badge-unknown {
        display: inline-block;
        background: rgba(229, 155, 140, 0.15);
        color: #E59B8C;
        border: 1px solid rgba(229, 155, 140, 0.4);
        padding: 0.3rem 0.8rem;
        border-radius: 2px;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    iframe {
        border-radius: 4px;
        border: 1px solid rgba(232, 209, 203, 0.12);
    }
</style>
""", unsafe_allow_html=True)

# ── Background Local FastAPI Server Daemon ────────────────────────────────────
@st.cache_resource
def ensure_local_backend():
    """Ensure local FastAPI backend is active on port 8000 when running in an environment with socket support."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        res = sock.connect_ex(("127.0.0.1", 8000))
        sock.close()
        if res == 0:
            return True  # Already running

        # Start uvicorn in a daemon thread
        import uvicorn
        from backend.api import app

        def run_uvicorn():
            try:
                config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="warning")
                server = uvicorn.Server(config)
                server.run()
            except Exception as e:
                logger.debug("Uvicorn background daemon exit: %s", e)

        thread = threading.Thread(target=run_uvicorn, daemon=True)
        thread.start()
        return True
    except Exception as exc:
        logger.debug("Background backend daemon not available: %s", exc)
        return False

# Attempt background backend startup
backend_active = ensure_local_backend()

# ── Cached Service Loader ─────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Initializing OpenCLIP Embeddings and FAISS Vector Index...")
def load_heritage_service():
    """Build and cache the core in-process HeritageService."""
    from backend.heritage_service import build_service

    # Sync Gemini API key from Streamlit secrets if provided
    try:
        if "GEMINI_API_KEY" in st.secrets and not os.getenv("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return build_service()

# ── Streamlit Custom Component Declaration ────────────────────────────────────
FRONTEND_DIR = PROJECT_ROOT / "frontend"
try:
    heritage_frontend = components.declare_component("heritage_discovery", path=str(FRONTEND_DIR))
except Exception as exc:
    logger.warning("Could not declare custom frontend component: %s", exc)
    heritage_frontend = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ Heritage Platform")
    st.caption("Visual Recognition · Vector Retrieval · Grounded Discovery")
    st.markdown("---")

    # API Configuration
    st.markdown("**External Vision Fallback**")
    configured_key = os.getenv("GEMINI_API_KEY", "")
    if configured_key:
        st.success("✓ Gemini API Key Configured", icon="🔑")
    else:
        user_key = st.text_input("Gemini API Key (Optional)", type="password", help="Enter a Gemini API key for fallback recognition of uncatalogued global monuments.")
        if user_key:
            os.environ["GEMINI_API_KEY"] = user_key
            st.rerun()

    st.markdown("---")
    st.markdown("**Core Architecture Invariants**")
    st.markdown(r"""
    - **Vision Encoder**: `clip-ViT-B-32` (512-dim)
    - **Vector Index**: FAISS IndexFlatIP (Cosine)
    - **Index Size**: 40 canonical vectors
    - **Similarity Threshold**: $\ge 0.8500$
    - **Competitor Margin**: $\ge 0.1000$
    - **Fallback Model**: `gemini-3.1-flash-lite`
    - **Fallback Thinking**: `MINIMAL`
    - **Evidence Base**: UNESCO & Archaeological Survey of India
    """)

    st.markdown("---")
    st.caption("Visual Heritage Recognition & Grounded Cultural Discovery Platform · 2026")

# ── Main Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">Visual Heritage Recognition Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Identify cultural monuments from query photographs using local vector embeddings, open-set boundaries, and grounded architectural evidence.</div>', unsafe_allow_html=True)

# Initialize in-process service
try:
    service = load_heritage_service()
    service_ready = True
    # Ensure Gemini client always holds active API key from secrets/environment
    active_key = os.getenv("GEMINI_API_KEY")
    if not active_key:
        try:
            active_key = st.secrets.get("GEMINI_API_KEY")
            if active_key:
                os.environ["GEMINI_API_KEY"] = active_key
        except Exception:
            pass
    if active_key and getattr(service, "gemini_client", None):
        service.gemini_client.api_key = active_key
except Exception as e:
    st.error(f"Heritage Service failed to initialize: {e}")
    service_ready = False

# ── Tabs Navigation ───────────────────────────────────────────────────────────
tab_integrated_app, tab_studio_console, tab_catalogue, tab_system_info = st.tabs([
    "🏛️ Cinematic Web Experience (Full Frontend)",
    "📸 Streamlit Studio Console",
    "📖 Global Monument Catalogue",
    "⚙️ System Status & Deployment",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: INTEGRATED CURRENT FRONTEND
# ══════════════════════════════════════════════════════════════════════════════
with tab_integrated_app:
    st.markdown("##### Complete 7-Screen Cinematic Heritage Discovery Application")
    st.caption("Includes the full interactive experience: Hero Slideshow with playback controls, Live Camera Capture, Visual Recognition Console, Grounded UNESCO Evidence Q&A, and Interactive Gallery.")

    if heritage_frontend is not None:
        # Check if previous execution produced a result to send to frontend
        component_result = st.session_state.get("component_rec_result")
        
        # Render the custom component with bidirectional messaging
        comp_output = heritage_frontend(
            recognition_result=component_result,
            service_health={
                "status": "ok",
                "service_ready": True,
                "index_size": 40,
                "similarity_threshold": 0.85,
                "competitor_margin": 0.10,
                "catalogue_size": 6,
            },
            key="heritage_frontend_component",
            default=None
        )

        # Handle requests from the embedded frontend component
        if comp_output and isinstance(comp_output, dict) and comp_output.get("action") == "recognize":
            b64_image = comp_output.get("image_base64", "")
            q = comp_output.get("question", "")
            req_id = comp_output.get("req_id") or str(comp_output.get("timestamp"))

            if b64_image and req_id != st.session_state.get("last_processed_req_id"):
                st.session_state["last_processed_req_id"] = req_id
                st.session_state["component_rec_result"] = None
                with st.spinner("Processing recognition request directly in-process..."):
                    tmp_file_path = None
                    try:
                        raw = b64_image
                        suffix = ".jpg"
                        if raw.startswith("data:"):
                            header, _, raw = raw.partition(",")
                            if "png" in header:
                                suffix = ".png"
                            elif "webp" in header:
                                suffix = ".webp"
                        img_bytes = base64.b64decode(raw)
                        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
                            tf.write(img_bytes)
                            tmp_file_path = tf.name

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        res = loop.run_until_complete(service.recognize_async(tmp_file_path, question=q, top_k=5))
                        res_dict = res.to_dict()
                        res_dict["req_id"] = req_id
                        st.session_state["component_rec_result"] = res_dict
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Recognition error: {exc}")
                        st.session_state["component_rec_result"] = {
                            "confirmed": False,
                            "recognition_status": "recognition_error",
                            "recognition_source": "error",
                            "reason": str(exc),
                            "similarity": 0.0,
                            "margin": 0.0,
                            "metadata": {},
                            "evidence": {},
                            "citations": [],
                            "req_id": req_id,
                        }
                        st.rerun()
                    finally:
                        if tmp_file_path and os.path.exists(tmp_file_path):
                            try:
                                os.unlink(tmp_file_path)
                            except Exception:
                                pass
    else:
        # Fallback to direct iframe if component declaration failed
        st.components.v1.iframe("http://127.0.0.1:8000/frontend/index.html", height=920, scrolling=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: STREAMLIT STUDIO CONSOLE (NATIVE UI)
# ══════════════════════════════════════════════════════════════════════════════
with tab_studio_console:
    st.markdown("##### Native Streamlit Recognition Console")
    st.caption("Upload or snap a monument photograph to evaluate local FAISS vector similarity, open-set rejection boundaries, and Gemini Vision fallback.")

    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        input_mode = st.radio(
            "Input Mode",
            ["📁 Upload Photograph", "📷 Live Camera Capture"],
            horizontal=True,
            label_visibility="collapsed",
        )

        query_image: Optional[Image.Image] = None
        query_filename = "photo.jpg"

        if input_mode == "📁 Upload Photograph":
            uploaded = st.file_uploader(
                "Choose an architectural photograph",
                type=["jpg", "jpeg", "png", "webp"],
                help="Accepts high-resolution JPG, PNG, and WebP images up to 10MB.",
            )
            if uploaded is not None:
                query_image = Image.open(uploaded)
                query_filename = uploaded.name
        else:
            camera_photo = st.camera_input("Capture architectural subject with camera")
            if camera_photo is not None:
                query_image = Image.open(camera_photo)
                query_filename = "camera_capture.jpg"

        if query_image is not None:
            st.image(query_image, caption=f"Query Subject: {query_filename}", use_container_width=True)
            user_question = st.text_input(
                "Optional Cultural Discovery Question",
                placeholder="e.g. When was this monument built and what is its architectural style?",
            )
            execute_btn = st.button("🔍 Execute Monument Recognition", type="primary", use_container_width=True)
        else:
            execute_btn = False
            st.info("Upload a photograph or capture an image with your camera to begin identification.")

    with col_output:
        st.markdown("##### Recognition & Grounded Findings")

        if query_image is not None and execute_btn and service_ready:
            tmp_query_path = None
            with st.spinner("Evaluating local CLIP embeddings, FAISS distance, and open-set boundaries..."):
                try:
                    suffix = ".png" if query_image.format == "PNG" else ".jpg"
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
                        if query_image.mode not in ("RGB", "L"):
                            clean_img = query_image.convert("RGB")
                        else:
                            clean_img = query_image
                        clean_img.save(tf.name, format="PNG" if suffix == ".png" else "JPEG", quality=90)
                        tmp_query_path = tf.name

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    rec_result = loop.run_until_complete(
                        service.recognize_async(tmp_query_path, question=user_question, top_k=5)
                    )
                    data = rec_result.to_dict()
                except Exception as exc:
                    st.error(f"Recognition pipeline error: {exc}")
                    data = None
                finally:
                    if tmp_query_path and os.path.exists(tmp_query_path):
                        try:
                            os.unlink(tmp_query_path)
                        except Exception:
                            pass

            if data:
                status = data.get("recognition_status")
                source = data.get("recognition_source")
                confirmed = data.get("confirmed", False)
                sim = data.get("similarity", 0.0) or 0.0
                margin = data.get("margin", 0.0) or 0.0
                meta = data.get("metadata") or {}
                evidence = data.get("evidence") or {}
                g = data.get("global_identification") or {}

                # ── 1. Verified Local Catalogue Match ──
                if status == "local_confirmed" or (confirmed and source in ("local", "faiss")):
                    st.markdown('<div class="badge-local">✓ Verified Catalogue Match</div>', unsafe_allow_html=True)
                    st.subheader(meta.get("name") or data.get("site_id", "").replace("_", " ").title())
                    
                    loc_parts = filter(None, [meta.get("location"), meta.get("state"), meta.get("country")])
                    loc_str = ", ".join(loc_parts)
                    if loc_str:
                        st.caption(f"📍 {loc_str}")

                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f'<div class="metric-card"><div class="metric-card-val">{sim:.4f}</div><div class="metric-card-lbl">CLIP Cosine Sim</div></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown(f'<div class="metric-card"><div class="metric-card-val">+{margin:.4f}</div><div class="metric-card-lbl">Margin vs Top-2</div></div>', unsafe_allow_html=True)
                    with m3:
                        st.markdown('<div class="metric-card"><div class="metric-card-val" style="color:#8FBF9F;">Confirmed</div><div class="metric-card-lbl">Catalogue Status</div></div>', unsafe_allow_html=True)

                    if meta.get("description"):
                        st.markdown("**Architectural Summary**")
                        st.write(meta.get("description"))

                    if meta.get("historical_period"):
                        st.markdown(f"**Historical Period:** {meta.get('historical_period')}")

                    claims = evidence.get("claims") or []
                    if claims:
                        st.markdown("**Verified Architectural Claims (UNESCO)**")
                        for claim in claims[:4]:
                            st.markdown(f"- {claim}")

                    citations = data.get("citations") or []
                    if citations:
                        st.markdown("**Official Citations**")
                        for cit in citations:
                            name = cit.get("source_name") or "Catalogue Record"
                            url = cit.get("source_url")
                            if url:
                                st.markdown(f"- [{name}]({url})")
                            else:
                                st.markdown(f"- {name}")

                    if data.get("answer"):
                        st.markdown("---")
                        st.markdown("**Grounded Answer to Your Question**")
                        st.info(data.get("answer"))

                # ── 2. External Gemini Fallback Match ──
                elif status == "external_match" or (source == "gemini" and g.get("site_name")):
                    st.markdown('<div class="badge-external">External Vision Match (Gemini)</div>', unsafe_allow_html=True)
                    st.subheader(g.get("site_name"))

                    g_loc = ", ".join(filter(None, [g.get("city"), g.get("country_or_region") or g.get("country")]))
                    if g_loc:
                        st.caption(f"📍 {g_loc}")

                    g_conf = g.get("confidence") or 0.0
                    m1, m2 = st.columns(2)
                    with m1:
                        st.markdown(f'<div class="metric-card"><div class="metric-card-val">{g_conf * 100:.0f}%</div><div class="metric-card-lbl">Model Confidence</div></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown(f'<div class="metric-card"><div class="metric-card-val">{g.get("evidence_tier", "substantial").title()}</div><div class="metric-card-lbl">Evidence Tier</div></div>', unsafe_allow_html=True)

                    st.info("ℹ️ External identification generated by Google Gemini Vision fallback (uncatalogued site).")

                    if g.get("visual_evidence"):
                        st.markdown("**Visible Architectural Evidence**")
                        st.write(g.get("visual_evidence"))

                    if g.get("architectural_style"):
                        st.markdown(f"**Architectural Style:** {g.get('architectural_style')}")
                    if g.get("historical_period"):
                        st.markdown(f"**Historical Period:** {g.get('historical_period')}")

                # ── 3. External Service Temporarily Unavailable (HTTP 503) ──
                elif status == "external_service_unavailable":
                    st.markdown('<div class="badge-unavailable">Service Temporarily Unavailable</div>', unsafe_allow_html=True)
                    st.subheader("EXTERNAL IDENTIFICATION TEMPORARILY UNAVAILABLE")
                    st.warning("The external recognition service is temporarily unavailable. Your photograph has been preserved. Please try again shortly.")
                    st.caption(f"Local Similarity: {sim:.4f} (Threshold: 0.8500). Status: 503 Service Unavailable after bounded backoff.")

                # ── 4. Missing API Key ──
                elif status == "external_auth_error":
                    st.markdown('<div class="badge-unavailable">API Key Required</div>', unsafe_allow_html=True)
                    st.subheader("External Fallback Authentication Required")
                    st.warning("Local recognition correctly identified that this image is not in the 6 indexed catalogue sites. To identify global monuments (like the Colosseum or Hawa Mahal), please ensure your GEMINI_API_KEY is configured in Streamlit Secrets.")
                    st.caption(f"Local Similarity: {sim:.4f} (Threshold: 0.8500). Reason: {data.get('reason')}")

                # ── 5. Genuine Inconclusive / Safe Rejection ──
                else:
                    st.markdown('<div class="badge-unknown">Identification Declined</div>', unsafe_allow_html=True)
                    st.subheader("Inconclusive Visual Match")
                    st.warning("The submitted photograph does not contain sufficient distinctive architectural evidence to reliably confirm a specific cultural monument.")
                    m1, m2 = st.columns(2)
                    with m1:
                        st.markdown(f'<div class="metric-card"><div class="metric-card-val">{sim:.4f}</div><div class="metric-card-lbl">Highest Local Match</div></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown('<div class="metric-card"><div class="metric-card-val">Insufficient</div><div class="metric-card-lbl">Evidence Tier</div></div>', unsafe_allow_html=True)
                    if data.get("reason"):
                        st.caption(f"Reason: {data.get('reason')}")

        elif not execute_btn:
            st.markdown(r"""
            *Upload or snap a photograph and click **Execute Monument Recognition** to begin analysis.*
            
            - **Local Match**: Validated when CLIP cosine similarity $\ge 0.85$ and competitor margin $\ge 0.10$.
            - **External Fallback**: Invoked for uncatalogued monuments with strict evidence validation.
            """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: GLOBAL MONUMENT CATALOGUE
# ══════════════════════════════════════════════════════════════════════════════
with tab_catalogue:
    st.markdown("##### Registered Cultural Heritage Monuments")
    
    cat_file = PROJECT_ROOT / "data" / "evidence" / "heritage_metadata.json"
    if cat_file.exists():
        try:
            with open(cat_file, "r", encoding="utf-8") as f:
                cat_data = json.load(f)

            monuments_list = list(cat_data.items()) if isinstance(cat_data, dict) else []
            search_txt = st.text_input("Filter monuments by name, city, state, or period", "").strip().lower()

            filtered_monuments = []
            for m_id, m_info in monuments_list:
                searchable = f"{m_info.get('name', '')} {m_info.get('location', '')} {m_info.get('state', '')} {m_info.get('country', '')} {m_info.get('historical_period', '')}".lower()
                if not search_txt or search_txt in searchable:
                    filtered_monuments.append((m_id, m_info))

            st.caption(f"Showing {len(filtered_monuments)} of {len(monuments_list)} registered canonical monuments.")

            cols = st.columns(2)
            for i, (m_id, m_info) in enumerate(filtered_monuments):
                c = cols[i % 2]
                with c:
                    with st.container(border=True):
                        st.markdown(f"### {m_info.get('name')}")
                        loc = ", ".join(filter(None, [m_info.get("location"), m_info.get("state"), m_info.get("country")]))
                        if loc:
                            st.caption(f"📍 {loc}")
                        if m_info.get("historical_period"):
                            st.caption(f"⏳ **Era:** {m_info.get('historical_period')}")
                        if m_info.get("category"):
                            st.caption(f"🏛️ **Type:** {m_info.get('category')}")
                        if m_info.get("description"):
                            st.write(m_info.get("description"))
        except Exception as e:
            st.error(f"Error loading catalogue metadata: {e}")
    else:
        st.warning("Heritage metadata file not found.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: SYSTEM STATUS & STREAMLIT CLOUD DEPLOYMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_system_info:
    st.markdown("##### System Status & Architecture")
    
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown('<div class="metric-card"><div class="metric-card-val">40</div><div class="metric-card-lbl">FAISS Vectors</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="metric-card"><div class="metric-card-val">0.85</div><div class="metric-card-lbl">Similarity Threshold</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown('<div class="metric-card"><div class="metric-card-val">0.10</div><div class="metric-card-lbl">Competitor Margin</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown('<div class="metric-card"><div class="metric-card-val">3.1 Flash</div><div class="metric-card-lbl">Gemini Model</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### Streamlit Community Cloud 1-Click Deployment Guide")
    st.markdown("""
    To deploy this repository to **Streamlit Community Cloud** (free hosting):

    1. **Log in to Streamlit Community Cloud**:
       Navigate to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.

    2. **Create New App**:
       - Click **Create app** -> **Deploy an existing app from GitHub**.
       - **Repository**: `humaidmalik63-png/Heritage`
       - **Branch**: `main`
       - **Main file path**: `streamlit_app.py`
       - **App URL**: `heritage-discovery` (or your chosen subdomain)

    3. **Configure Secrets**:
       In **Advanced settings** -> **Secrets**, paste your Google Gemini API key:
       ```toml
       GEMINI_API_KEY = "your-actual-gemini-api-key-here"
       ```

    4. **Click Deploy**:
       Streamlit will automatically install dependencies from `requirements.txt`, initialize the FAISS vector index and CLIP embeddings, and launch the integrated platform!
    """)
