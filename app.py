import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from pdf_utils import load_pdf, split_text
from vector_store import create_vector_store
from qa_chain import get_answer

load_dotenv()  # loads OPENAI_API_KEY from .env

st.set_page_config(page_title="ResearchRAG", layout="wide")
st.title("📄 ResearchRAG — Research Paper Assistant")

if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

uploaded_file = st.file_uploader("Upload a research paper (PDF)", type="pdf")

if uploaded_file:
    with st.spinner("Processing paper... extracting, chunking, embedding"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        docs = load_pdf(tmp_path)
        chunks = split_text(docs)
        st.session_state.vector_db = create_vector_store(chunks)
        os.remove(tmp_path)

    st.success(f"Paper processed into {len(chunks)} chunks. Ask away!")

if st.session_state.vector_db:
    question = st.text_input("Ask a question about the paper")

    if question:
        with st.spinner("Thinking..."):
            answer, sources = get_answer(st.session_state.vector_db, question)

        st.subheader("Answer")
        st.write(answer)

        with st.expander("📚 Sources used"):
            for i, doc in enumerate(sources):
                page = doc.metadata.get("page", "?")
                st.markdown(f"**Chunk {i+1}** (page {page})")
                st.caption(doc.page_content[:300] + "...")