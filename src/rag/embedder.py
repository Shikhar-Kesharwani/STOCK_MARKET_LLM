import json
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "data/chroma_db"

def build_vector_store(documents_path: str):
    """
    Load raw documents, chunk them, embed them,
    and store in ChromaDB.
    """
    print("Building vector store...")
    
    # Load raw documents
    with open(documents_path) as f:
        raw_docs = json.load(f)
    
    # Convert to LangChain documents (clean metadata for ChromaDB)
    lc_docs = []
    for doc in raw_docs:
        if not doc["text"].strip():
            continue
        cleaned_meta = {k: v for k, v in doc["metadata"].items() if v is not None and (not isinstance(v, list) or len(v) > 0)}
        lc_docs.append(Document(page_content=doc["text"], metadata=cleaned_meta))
    
    print(f"Loaded {len(lc_docs)} documents")
    
    # Chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_documents(lc_docs)
    print(f"Created {len(chunks)} chunks")
    
    # Embed and store locally with HuggingFace (100% free, no API keys)
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Delete existing store if rebuilding
    import shutil
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedder,
        persist_directory=CHROMA_PATH
    )
    
    print(f"✓ Vector store built: {len(chunks)} chunks stored")
    return vectorstore


def load_vector_store():
    """Load existing vector store from disk."""
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedder
    )
