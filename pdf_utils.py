from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf(file_path):
    """Extract text from a PDF, page by page."""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents

def split_text(documents, chunk_size=1000, chunk_overlap=200):
    """Split extracted text into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    return chunks

