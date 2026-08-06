import json
import os
from langchain_chroma import Chroma
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "data/chroma_db"

def get_embedder():
    """Returns an embedding function with fallbacks."""
    # Try Google Gemini Embeddings if key present
    if os.getenv("GEMINI_API_KEY"):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        except Exception as e:
            print(f"Gemini embedding fallback notice: {e}")

    # Try OpenAI Embeddings if key present
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings()
        except Exception as e:
            print(f"OpenAI embedding fallback notice: {e}")

    # Try FastEmbed if installed
    try:
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
        return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    except Exception:
        pass

    # Ultimate fallback: Fake/Deterministic embeddings to prevent boot crash
    from langchain_core.embeddings import FakeEmbeddings
    return FakeEmbeddings(size=384)


def build_vector_store(documents_path: str):
    """
    Load raw documents, chunk them, embed them,
    and store in ChromaDB or Pinecone.
    """
    print("Building vector store...")
    
    # Load raw documents
    if not os.path.exists(documents_path):
        print(f"Warning: {documents_path} not found.")
        return None

    with open(documents_path) as f:
        raw_docs = json.load(f)
    
    # Convert to LangChain documents (clean metadata for ChromaDB)
    lc_docs = []
    for doc in raw_docs:
        if not doc.get("text", "").strip():
            continue
        cleaned_meta = {k: v for k, v in doc.get("metadata", {}).items() if v is not None and (not isinstance(v, list) or len(v) > 0)}
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
    
    embedder = get_embedder()
    
    # Save chunks for BM25 (always needed)
    os.makedirs("data", exist_ok=True)
    import pickle
    with open("data/chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)
        
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "stock-intelligence")

    if pinecone_key:
        print("Model 2: Cloud Database detected. Pushing to Pinecone...")
        from pinecone import Pinecone
        pc = Pinecone(api_key=pinecone_key)
        
        if index_name not in pc.list_indexes().names():
            print(f"Warning: Pinecone index '{index_name}' not found.")
        
        vectorstore = PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embedder,
            index_name=index_name
        )
        print(f"[OK] Vector store built in Pinecone ({len(chunks)} chunks stored)")
    else:
        print("Model 1: Local Database detected. Building ChromaDB...")
        import shutil
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
        
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embedder,
            persist_directory=CHROMA_PATH
        )
        print(f"[OK] Vector store built in local ChromaDB ({len(chunks)} chunks stored)")
        
    return vectorstore


def load_vector_store():
    """Load existing vector store (Pinecone or Chroma)."""
    embedder = get_embedder()
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "stock-intelligence")
    
    if pinecone_key:
        return PineconeVectorStore(
            index_name=index_name,
            embedding=embedder
        )
    else:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        return Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embedder
        )
