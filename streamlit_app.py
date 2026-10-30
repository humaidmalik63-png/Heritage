import os
import sys
import tempfile
import json
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional dotenv load
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
from PIL import Image

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Heritage Discovery — Visual Monument Recognition",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom Styling ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Obsidian & Bronze Cinematic Palette */
    .stApp {
        background-color: #050608;
        color: #F2F4F7;
    }
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        color: #F2F4F7;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: rgba(235, 240, 248, 0.65);
        margin-bottom: 1.5rem;
    }
    .result-card {
        background: rgba(13, 16, 23, 0.95);
        border: 1px solid rgba(232, 209, 203, 0.25);
        padding: 1.5rem;
        border-radius: 4px;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .badge-local {
        display: inline-block;
        background: rgba(143, 191, 159, 0.15);
        color: #8FBF9F;
        border: 1px solid rgba(143, 191, 159, 0.4);
        padding: 0.25rem 0.75rem;
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
        padding: 0.25rem 0.75rem;
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
        padding: 0.25rem 0.75rem;
        border-radius: 2px;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .metric-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 0.75rem 1rem;
        border-radius: 4px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #E8D1CB;
    }
    .metric-label {
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(235, 240, 248, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ── Service Loader ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Initializing OpenCLIP Embeddings and FAISS Vector Index...")
def load_heritage_service():
    from backend.heritage_service import build_service
    return build_service()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ Heritage Platform")
    st.caption("Visual recognition · Similarity search · Grounded cultural discovery")
    
    st.markdown("---")
    st.markdown("**System Architecture**")
    st.markdown("""
    - **Vision Encoder**: CLIP ViT-B/32 (512-dim)
    - **Index Engine**: FAISS IndexFlatIP (Cosine)
    - **Acceptance Threshold**: ≥ 0.8500
    - **Competitor Margin**: ≥ 0.1000
    - **Evidence Grounding**: UNESCO World Heritage & ASI
    """)

    # Optional Gemini key override
    env_gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not env_gemini_key:
        user_key = st.text_input("Gemini API Key (Optional fallback)", type="password")
        if user_key:
            os.environ["GEMINI_API_KEY"] = user_key

    st.markdown("---")
    st.caption("Grounded in visual evidence & official catalogue records · 2026")

# ── Main Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">Visual Heritage Recognition</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Identify architectural monuments from query photographs using vector similarity and grounded evidence.</div>', unsafe_allow_html=True)

# ── Service Initialisation ───────────────────────────────────────────────────
try:
    service = load_heritage_service()
    service_ready = True
except Exception as e:
    st.error(f"Failed to initialize Heritage Service: {e}")
    service_ready = False

# ── Application Tabs ──────────────────────────────────────────────────────────
tab_recognize, tab_catalogue = st.tabs(["🔍 Identification Console", "📖 Monument Catalogue"])

with tab_recognize:
    col_upload, col_result = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("#### Upload Photograph")
        uploaded_file = st.file_uploader(
            "Upload an architectural photograph to identify",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Query: {uploaded_file.name}", use_container_width=True)
            run_btn = st.button("Execute Recognition", type="primary", use_container_width=True)
        else:
            run_btn = False
            st.info("Select or drop a photograph of an architectural site to begin identification.")

    with col_result:
        st.markdown("#### Recognition Analysis")
        
        if uploaded_file is not None and run_btn and service_ready:
            # Save to temporary file for the feature extractor
            suffix = Path(uploaded_file.name).suffix or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                with st.spinner("Analyzing image features, computing vector cosine similarity, and validating thresholds..."):
                    result = service.recognize(query=tmp_path, top_k=5)
                    data = result.to_dict()

                rec_source = data.get("recognition_source", "unknown")
                meta = data.get("metadata") or {}
                evidence = data.get("evidence") or {}
                g = data.get("global_identification") or {}
                similarity = data.get("similarity", 0.0)
                margin = data.get("margin", 0.0)

                # ── 1. Local Catalogue Match ──
                if rec_source in ("local", "faiss") and data.get("confirmed"):
                    monument_name = meta.get("name") or data.get("site_id", "Identified Monument")
                    location = ", ".join(filter(None, [meta.get("city"), meta.get("state"), meta.get("country")]))
                    
                    st.markdown('<div class="badge-local">Verified Catalogue Match</div>', unsafe_allow_html=True)
                    st.subheader(monument_name)
                    if location:
                        st.caption(f"📍 {location}")

                    # Metric cards
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f'<div class="metric-box"><div class="metric-value">{similarity:.2f}</div><div class="metric-label">CLIP Similarity</div></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown(f'<div class="metric-box"><div class="metric-value">+{margin:.2f}</div><div class="metric-label">Competitor Margin</div></div>', unsafe_allow_html=True)
                    with m3:
                        st.markdown('<div class="metric-box"><div class="metric-value" style="color:#8FBF9F;">Confirmed</div><div class="metric-label">Status</div></div>', unsafe_allow_html=True)

                    st.markdown("##### Architectural Profile")
                    if meta.get("description"):
                        st.write(meta.get("description"))

                    if meta.get("period"):
                        st.markdown(f"**Historical Period:** {meta.get('period')}")

                    # Evidence and Claims
                    claims = evidence.get("claims") if isinstance(evidence, dict) else None
                    if claims:
                        st.markdown("##### Factual Evidence Claims")
                        for claim in claims:
                            st.markdown(f"- {claim}")

                    # Official Citations
                    citations = data.get("citations") or []
                    if citations:
                        st.markdown("##### Official Verification Sources")
                        for cit in citations:
                            name = cit.get("source_name") or "Catalogue Record"
                            url = cit.get("source_url")
                            if url:
                                st.markdown(f"- [{name}]({url})")
                            else:
                                st.markdown(f"- {name}")

                # ── 2. External Vision Identification ──
                elif rec_source in ("gemini", "ollama") and g.get("site_name") and not g.get("unknown"):
                    site_name = g.get("site_name", "Identified Monument")
                    location = ", ".join(filter(None, [g.get("city"), g.get("country_or_region") or g.get("country")]))
                    conf_score = g.get("confidence", 0.0)

                    st.markdown('<div class="badge-external">External Identification</div>', unsafe_allow_html=True)
                    st.subheader(site_name)
                    if location:
                        st.caption(f"📍 {location}")

                    m1, m2 = st.columns(2)
                    with m1:
                        st.markdown(f'<div class="metric-box"><div class="metric-value">{conf_score * 100:.0f}%</div><div class="metric-label">Recognition Score</div></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown('<div class="metric-box"><div class="metric-value" style="color:#E8D1CB;">External Model</div><div class="metric-label">Source</div></div>', unsafe_allow_html=True)

                    st.info("ℹ️ This identification was generated by an external vision reasoning service and has not been verified against the local catalogue.")

                    if g.get("architectural_style"):
                        st.markdown(f"**Architectural Style:** {g.get('architectural_style')}")
                    if g.get("historical_period"):
                        st.markdown(f"**Historical Period:** {g.get('historical_period')}")
                    if g.get("summary"):
                        st.write(g.get("summary"))

                    facts = g.get("interesting_facts") or []
                    if facts:
                        st.markdown("##### Heritage Context & Highlights")
                        for fact in facts:
                            st.markdown(f"- {fact}")

                # ── 3. Unconfirmed / Low Similarity ──
                else:
                    st.markdown('<div class="badge-unknown">Not Confirmed</div>', unsafe_allow_html=True)
                    st.subheader("Monument Not Identified")
                    
                    reason = data.get("reason")
                    if reason == "low_similarity" or similarity < 0.85:
                        st.warning(f"The photograph did not meet the required similarity threshold (0.8500). Highest match similarity: {similarity:.4f}.")
                    elif reason == "non_heritage":
                        st.warning("The submitted image does not appear to depict a registered architectural heritage monument.")
                    else:
                        st.warning("The visual features did not match any verified record in the catalogue, and external fallback could not confirm the site.")

            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
        elif not run_btn:
            st.markdown("""
            *Results will appear here after clicking **Execute Recognition**.*
            
            - **Local Catalogue Identification**: Evaluated against the 512-dim FAISS index with dual cosine similarity and margin verification.
            - **External Identification**: Queried when no local record meets the verified threshold.
            """)

with tab_catalogue:
    st.markdown("#### Indexed Cultural Heritage Monuments")
    
    cat_path = PROJECT_ROOT / "data" / "metadata" / "global_monument_catalogue.json"
    if cat_path.exists():
        try:
            with open(cat_path, "r", encoding="utf-8") as f:
                catalogue_data = json.load(f)
            
            search_query = st.text_input("Filter monuments by name, city, or country", "").strip().lower()
            
            filtered = [
                m for m in catalogue_data
                if not search_query or search_query in (m.get("name", "") + " " + m.get("city", "") + " " + m.get("country", "")).lower()
            ]

            st.caption(f"Showing {len(filtered)} of {len(catalogue_data)} registered catalogue monuments.")

            cols = st.columns(3)
            for idx, item in enumerate(filtered[:24]):
                col = cols[idx % 3]
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{item.get('name')}**")
                        place = ", ".join(filter(None, [item.get("city"), item.get("country")]))
                        if place:
                            st.caption(f"📍 {place}")
                        if item.get("type"):
                            st.caption(f"🏛️ {item.get('type')}")
                        if item.get("period"):
                            st.caption(f"⏳ {item.get('period')}")
                        if item.get("description"):
                            desc = item.get("description")
                            st.write(desc[:120] + "..." if len(desc) > 120 else desc)

            if len(filtered) > 24:
                st.caption(f"*Showing first 24 records. Use search above to narrow down results.*")

        except Exception as e:
            st.error(f"Error loading catalogue: {e}")
    else:
        st.warning("Catalogue data file not found.")

