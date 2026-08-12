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

# ---------- Custom CSS for extra polish ----------
st.markdown("""
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        color: #9CA3AF;
        font-size: 1.05rem;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }
    .answer-box {
        background-color: #1A1D27;
        border: 1px solid #2A2E3A;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Sidebar ----------
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

# ---------- Main area ----------
st.markdown('<p class="main-title">Research Paper Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload a paper and ask questions in plain language — answers are grounded in the paper\'s actual content.</p>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="answer-box">{a}</div>', unsafe_allow_html=True)

        with st.expander("📚 Sources used"):
            for i, doc in enumerate(sources):
                page = doc.metadata.get("page", "?")
                st.markdown(f"**Chunk {i+1}** · page {page}")
                st.caption(doc.page_content[:300] + "...")
        st.divider()