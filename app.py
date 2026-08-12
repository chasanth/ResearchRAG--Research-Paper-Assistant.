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

# ---------- Global CSS ----------
st.markdown("""
    <style>
    html { scroll-behavior: smooth; }

    #MainMenu, footer, header {visibility: hidden;}

    .hero {
        text-align: center;
        padding: 4rem 1rem 3rem 1rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.4);
        padding: 0.35rem 1rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        font-size: 3.4rem;
        font-weight: 900;
        line-height: 1.1;
        background: linear-gradient(90deg, #818CF8, #C084FC, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #9CA3AF;
        max-width: 640px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }
    .hero-cta {
        display: inline-block;
        background: linear-gradient(90deg, #6366F1, #A855F7);
        color: white !important;
        text-decoration: none;
        font-weight: 700;
        padding: 0.85rem 2.2rem;
        border-radius: 10px;
        font-size: 1.05rem;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
        transition: transform 0.15s ease;
    }
    .hero-cta:hover { transform: translateY(-2px); }

    .feature-card {
        background: #1A1D27;
        border: 1px solid #2A2E3A;
        border-radius: 14px;
        padding: 1.6rem;
        height: 100%;
    }
    .feature-icon { font-size: 1.8rem; margin-bottom: 0.6rem; }
    .feature-title { font-weight: 700; font-size: 1.05rem; margin-bottom: 0.4rem; }
    .feature-desc { color: #9CA3AF; font-size: 0.9rem; line-height: 1.5; }

    .section-divider {
        border-top: 1px solid #2A2E3A;
        margin: 3.5rem 0 2.5rem 0;
    }
    .tool-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }
    .tool-subtitle {
        color: #9CA3AF;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Hero Section ----------
st.markdown("""
    <div class="hero">
        <div class="hero-badge">✨ AI-POWERED RESEARCH ASSISTANT</div>
        <div class="hero-title">Understand any research<br>paper in minutes</div>
        <div class="hero-subtitle">
            Upload a paper and ask questions in plain language. ResearchRAG retrieves
            the exact sections that matter and gives you grounded, source-backed answers —
            no more digging through pages manually.
        </div>
        <a href="#tool-section" class="hero-cta">Try it now ↓</a>
    </div>
""", unsafe_allow_html=True)

# ---------- Feature cards ----------
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

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ---------- Session state ----------
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Sidebar (the tool controls) ----------
with st.sidebar:
    st.markdown("### 📄 ResearchRAG")
    st.caption("AI-powered research paper assistant")
    st.divider()

    uploaded_file = st.file_uploader("Upload a research paper", type="pdf")

    if uploaded_file:
        if st.button("Process Paper", use_container_width=True):
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

            st.success(f"Processed into {st.session_state.chunk_count} chunks")

    st.divider()
    if st.session_state.vector_db:
        st.metric("Chunks indexed", st.session_state.chunk_count)
        if st.button("Clear paper", use_container_width=True):
            st.session_state.vector_db = None
            st.session_state.chunk_count = 0
            st.session_state.history = []
            st.rerun()

# ---------- Tool section ----------
st.markdown('<div id="tool-section"></div>', unsafe_allow_html=True)
st.markdown('<p class="tool-title">Ask your paper anything</p>', unsafe_allow_html=True)
st.markdown('<p class="tool-subtitle">Answers are grounded in the paper\'s actual content — every response shows its sources.</p>', unsafe_allow_html=True)

if not st.session_state.vector_db:
    st.info("👈 Upload a PDF from the sidebar to get started.")
else:
    question = st.text_input("Ask a question about the paper", placeholder="e.g. What methodology did the authors use?")

    if question:
        with st.spinner("Thinking..."):
            answer, sources = get_answer(st.session_state.vector_db, question)
            st.session_state.history.insert(0, (question, answer, sources))

    for q, a, sources in st.session_state.history:
        st.markdown(f"**Q: {q}**")
        with st.container(border=True):
            st.markdown(a)

        with st.expander("📚 Sources used"):
            for i, doc in enumerate(sources):
                page = doc.metadata.get("page", "?")
                st.markdown(f"**Chunk {i+1}** · page {page}")
                st.caption(doc.page_content[:300] + "...")
        st.divider()