import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from pdf_utils import load_pdf, split_text
from vector_store import create_vector_store
from qa_chain import get_answer

load_dotenv()

st.set_page_config(
    page_title="ResearchRAG",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Logo SVG ----------
logo_svg = '<svg width="34" height="34" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#818CF8"/><stop offset="50%" stop-color="#A855F7"/><stop offset="100%" stop-color="#F472B6"/></linearGradient></defs><rect width="34" height="34" rx="9" fill="url(#logoGrad)"/><path d="M10 8.5C10 7.67 10.67 7 11.5 7H19L24 12V25.5C24 26.33 23.33 27 22.5 27H11.5C10.67 27 10 26.33 10 25.5V8.5Z" fill="white" fill-opacity="0.95"/><path d="M19 7L24 12H20C19.45 12 19 11.55 19 11V7Z" fill="white" fill-opacity="0.6"/><line x1="13" y1="16" x2="21" y2="16" stroke="#A855F7" stroke-width="1.4" stroke-linecap="round"/><line x1="13" y1="19.5" x2="21" y2="19.5" stroke="#A855F7" stroke-width="1.4" stroke-linecap="round"/><line x1="13" y1="23" x2="18" y2="23" stroke="#A855F7" stroke-width="1.4" stroke-linecap="round"/><path d="M25.5 6.5L26.3 8.2L28 9L26.3 9.8L25.5 11.5L24.7 9.8L23 9L24.7 8.2L25.5 6.5Z" fill="#FBBF24"/></svg>'

# ---------- Theme state ----------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

is_dark = st.session_state.theme == "dark"

# ---------- Color palette ----------
if is_dark:
    bg = "#0F1117"
    bg_secondary = "#1A1D27"
    card_bg = "#1A1D27"
    border = "#2A2E3A"
    text = "#E5E7EB"
    text_muted = "#9CA3AF"
    badge_bg = "rgba(99, 102, 241, 0.15)"
    badge_text = "#A5B4FC"
    badge_border = "rgba(99, 102, 241, 0.4)"
    glow1 = "rgba(99, 102, 241, 0.25)"
    glow2 = "rgba(236, 72, 153, 0.18)"
    card_shadow = "rgba(0, 0, 0, 0.4)"
else:
    bg = "#FFFFFF"
    bg_secondary = "#F8F9FC"
    card_bg = "#FFFFFF"
    border = "#E5E7EB"
    text = "#111827"
    text_muted = "#6B7280"
    badge_bg = "rgba(99, 102, 241, 0.08)"
    badge_text = "#6366F1"
    badge_border = "rgba(99, 102, 241, 0.25)"
    glow1 = "rgba(99, 102, 241, 0.12)"
    glow2 = "rgba(236, 72, 153, 0.1)"
    card_shadow = "rgba(99, 102, 241, 0.08)"

# ---------- Global CSS ----------
st.markdown(f"""
    <style>
    html {{ scroll-behavior: smooth; }}
    #MainMenu, footer {{visibility: hidden;}}
    [data-testid="stToolbar"] {{visibility: hidden;}}

    .stApp {{
        background-color: {bg};
        color: {text};
        background-image:
            radial-gradient(circle at 15% 10%, {glow1} 0%, transparent 40%),
            radial-gradient(circle at 85% 25%, {glow2} 0%, transparent 40%);
    }}

    .block-container {{
        padding-top: 2rem !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {bg_secondary} !important;
        border-right: 1px solid {border};
    }}
    section[data-testid="stSidebar"] * {{
        color: {text} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {text_muted} !important;
    }}

    .navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0.5rem;
        border-bottom: 1px solid {border};
        margin-bottom: 1rem;
    }}
    .navbar-logo {{
        font-weight: 800;
        font-size: 1.15rem;
        color: {text};
    }}
    .navbar-links a {{
        color: {text_muted};
        text-decoration: none;
        margin-left: 1.8rem;
        font-size: 0.92rem;
        font-weight: 600;
        transition: color 0.15s ease;
    }}
    .navbar-links a:hover {{ color: {badge_text}; }}

    .hero {{ text-align: center; padding: 3rem 1rem 2rem 1rem; position: relative; }}
    .hero-badge {{
        display: inline-block;
        background: {badge_bg};
        color: {badge_text};
        border: 1px solid {badge_border};
        padding: 0.4rem 1.1rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-bottom: 1.4rem;
    }}
    .hero-title {{
        font-size: 3.4rem;
        font-weight: 900;
        line-height: 1.1;
        background: linear-gradient(90deg, #818CF8, #C084FC, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.2rem;
        letter-spacing: -0.02em;
    }}
    .hero-subtitle {{
        font-size: 1.15rem;
        color: {text_muted};
        max-width: 660px;
        margin: 0 auto 1.5rem auto;
        line-height: 1.65;
    }}

    .stats-row {{
        display: flex;
        justify-content: center;
        gap: 3.5rem;
        padding: 1.5rem 0;
        margin: 0.5rem 0;
    }}
    .stat-item {{ text-align: center; }}
    .stat-number {{
        font-size: 2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .stat-label {{ color: {text_muted}; font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; }}

    .feature-card, .step-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 1.7rem;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        box-shadow: 0 4px 14px {card_shadow};
    }}
    .feature-card:hover, .step-card:hover {{
        transform: translateY(-5px);
        border-color: {badge_border};
        box-shadow: 0 14px 34px {card_shadow};
    }}
    .feature-icon {{
        font-size: 1.9rem;
        margin-bottom: 0.7rem;
        display: inline-block;
        background: {badge_bg};
        padding: 0.55rem;
        border-radius: 10px;
    }}
    .step-number {{
        font-size: 1.6rem;
        font-weight: 900;
        color: {badge_text};
        margin-bottom: 0.5rem;
    }}
    .feature-title, .step-title {{ font-weight: 700; font-size: 1.08rem; margin-bottom: 0.45rem; color: {text}; }}
    .feature-desc, .step-desc {{ color: {text_muted}; font-size: 0.9rem; line-height: 1.55; }}

    .section-divider {{ border-top: 1px solid {border}; margin: 3rem 0 2rem 0; }}
    .section-heading {{ font-size: 2rem; font-weight: 800; margin-bottom: 0.4rem; color: {text}; text-align: center; }}
    .section-subheading {{ color: {text_muted}; margin-bottom: 2rem; text-align: center; font-size: 1.02rem; }}

    .upload-card {{
        background: {card_bg};
        border: 1.5px dashed {badge_border};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }}
    .upload-card-title {{ font-weight: 700; font-size: 1.15rem; color: {text}; margin-bottom: 0.3rem; }}
    .upload-card-desc {{ color: {text_muted}; font-size: 0.92rem; margin-bottom: 1rem; }}

    .tool-title {{ font-size: 1.9rem; font-weight: 800; margin-bottom: 0.3rem; color: {text}; }}
    .tool-subtitle {{ color: {text_muted}; margin-bottom: 1.6rem; }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 12px !important;
        box-shadow: 0 4px 16px {card_shadow};
    }}

    .app-footer {{
        text-align: center;
        color: {text_muted};
        font-size: 0.85rem;
        padding: 2.5rem 0 1.5rem 0;
        border-top: 1px solid {border};
        margin-top: 3rem;
    }}

    [data-testid="stChatMessage"] {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 3px 12px {card_shadow};
    }}
    </style>
""", unsafe_allow_html=True)

# ---------- Session state ----------
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Sidebar (secondary controls) ----------
with st.sidebar:
    sidebar_logo_html = f'<div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem;">{logo_svg}<span style="font-weight:800; font-size:1.15rem; color:{text};">ResearchRAG</span></div>'
    st.markdown(sidebar_logo_html, unsafe_allow_html=True)
    st.caption("AI-powered research paper assistant")
    st.button("☀️ Light mode" if is_dark else "🌙 Dark mode", on_click=toggle_theme, use_container_width=True)
    st.divider()
    if st.session_state.vector_db:
        st.metric("Chunks indexed", st.session_state.chunk_count)
        if st.button("Clear paper", use_container_width=True):
            st.session_state.vector_db = None
            st.session_state.chunk_count = 0
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("👉 Upload your paper in the main panel to get started.")

# ---------- Navbar ----------
navbar_html = f'<div class="navbar"><div class="navbar-logo" style="display:flex; align-items:center; gap:0.6rem;">{logo_svg}<span>ResearchRAG</span></div><div class="navbar-links"><a href="#upload-section">Upload</a><a href="#how-it-works">How it works</a><a href="#tool-section">Chat</a></div></div>'
st.markdown(navbar_html, unsafe_allow_html=True)

# ---------- Hero ----------
hero_html = '<div class="hero"><div class="hero-badge">✨ AI-POWERED RESEARCH ASSISTANT</div><div class="hero-title">Understand any research<br>paper in minutes</div><div class="hero-subtitle">Upload a paper and ask questions in plain language. ResearchRAG retrieves the exact sections that matter and gives you grounded, source-backed answers — no more digging through pages manually.</div></div>'
st.markdown(hero_html, unsafe_allow_html=True)

# ---------- Stats bar ----------
stats_html = '<div class="stats-row"><div class="stat-item"><div class="stat-number">10x</div><div class="stat-label">FASTER READING</div></div><div class="stat-item"><div class="stat-number">100%</div><div class="stat-label">SOURCE-GROUNDED</div></div><div class="stat-item"><div class="stat-number">0</div><div class="stat-label">MANUAL SEARCHING</div></div></div>'
st.markdown(stats_html, unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ---------- Upload section (main, always visible) ----------
st.markdown('<div id="upload-section"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-heading">Upload Your Paper</p>', unsafe_allow_html=True)
st.markdown('<p class="section-subheading">Drop in a PDF to start asking questions</p>', unsafe_allow_html=True)

upload_col1, upload_col2, upload_col3 = st.columns([1, 2, 1])
with upload_col2:
    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        process_col1, process_col2, process_col3 = st.columns([1, 1, 1])
        with process_col2:
            if st.button("🚀 Process Paper", use_container_width=True, type="primary"):
                with st.spinner("Extracting, chunking, embedding..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    docs = load_pdf(tmp_path)
                    chunks = split_text(docs)
                    st.session_state.vector_db = create_vector_store(chunks)
                    st.session_state.chunk_count = len(chunks)
                    st.session_state.history = []
                    os.remove(tmp_path)

                st.success(f"Processed into {st.session_state.chunk_count} chunks — scroll down to chat!")

# ---------- Feature cards ----------
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
features = [
    ("💬", "Paper Q&A", "Ask natural-language questions and get answers grounded in the actual paper."),
    ("📝", "Summarisation", "Generate concise summaries of dense, technical papers instantly."),
    ("🔍", "Gap Identification", "Surface limitations and potential research directions automatically."),
    ("📊", "Dataset Analysis", "Find datasets, metrics, and experimental results without manual searching."),
]
for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
    with col:
        st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
        """, unsafe_allow_html=True)

# ---------- How it works ----------
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<div id="how-it-works"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-heading">How it works</p>', unsafe_allow_html=True)
st.markdown('<p class="section-subheading">Three simple steps, powered by Retrieval-Augmented Generation</p>', unsafe_allow_html=True)

s1, s2, s3 = st.columns(3)
steps = [
    ("1", "Upload your paper", "Drop in any research paper as a PDF — no formatting or setup needed."),
    ("2", "Ask a question", "Type what you want to know, just like you'd ask a colleague."),
    ("3", "Get grounded answers", "Receive a detailed answer with the exact source chunks it came from."),
]
for col, (num, title, desc) in zip([s1, s2, s3], steps):
    with col:
        st.markdown(f"""
            <div class="step-card">
                <div class="step-number">{num}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ---------- Chat / tool section ----------
st.markdown('<div id="tool-section"></div>', unsafe_allow_html=True)
st.markdown('<p class="tool-title">Chat with your paper</p>', unsafe_allow_html=True)
st.markdown('<p class="tool-subtitle">Answers are grounded in the paper\'s actual content — every response shows its sources.</p>', unsafe_allow_html=True)

if not st.session_state.vector_db:
    st.info("👆 Upload and process a PDF above to start chatting.")
else:
    top_col1, top_col2 = st.columns([5, 1])
    with top_col2:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    for q, a, sources in reversed(st.session_state.history):
        with st.chat_message("user", avatar="🧑"):
            st.markdown(q)
        with st.chat_message("assistant", avatar="📄"):
            st.markdown(a)
            with st.expander("📚 Sources used"):
                for i, doc in enumerate(sources):
                    page = doc.metadata.get("page", "?")
                    st.markdown(f"**Chunk {i+1}** · page {page}")
                    st.caption(doc.page_content[:300] + "...")

    question = st.chat_input("Ask a question about the paper...")

    if question:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="📄"):
            with st.spinner("Thinking..."):
                answer, sources = get_answer(st.session_state.vector_db, question)
                st.markdown(answer)
                with st.expander("📚 Sources used"):
                    for i, doc in enumerate(sources):
                        page = doc.metadata.get("page", "?")
                        st.markdown(f"**Chunk {i+1}** · page {page}")
                        st.caption(doc.page_content[:300] + "...")

        st.session_state.history.insert(0, (question, answer, sources))

# ---------- Footer ----------
st.markdown("""
    <div class="app-footer">
        Built with Streamlit, LangChain, and Groq · ResearchRAG — Capstone Project
    </div>
""", unsafe_allow_html=True)