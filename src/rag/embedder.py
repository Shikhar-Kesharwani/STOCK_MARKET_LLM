import json
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
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
    
    # Convert to LangChain documents
    lc_docs = [
        Document(
            page_content=doc["text"],
            metadata=doc["metadata"]
        )
        for doc in raw_docs
        if doc["text"].strip()  # skip empty documents
    ]
    
    print(f"Loaded {len(lc_docs)} documents")
    
    # Chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_documents(lc_docs)
    print(f"Created {len(chunks)} chunks")
    
    # Embed and store
    embedder = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=os.environ.get("GEMINI_API_KEY"))
    
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
    embedder = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=os.environ.get("GEMINI_API_KEY"))
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedder
    )
