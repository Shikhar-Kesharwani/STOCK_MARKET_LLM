import os
import pickle
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from src.rag.embedder import load_vector_store
from dotenv import load_dotenv

load_dotenv()

# Global BM25 index cache
_BM25_INDEX = None
_CHUNKS = None

def get_vector_store():
    return load_vector_store()

def _load_bm25():
    global _BM25_INDEX, _CHUNKS
    if _BM25_INDEX is None:
        try:
            with open("data/chunks.pkl", "rb") as f:
                _CHUNKS = pickle.load(f)
            # Simple tokenization for BM25
            tokenized_corpus = [doc.page_content.lower().split(" ") for doc in _CHUNKS]
            _BM25_INDEX = BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"Failed to load BM25 index: {e}")
            _CHUNKS = []
            _BM25_INDEX = None

def get_bm25_results(query: str, n: int = 10, company_filter: str = None) -> list[Document]:
    _load_bm25()
    if not _BM25_INDEX or not _CHUNKS:
        return []
    
    tokenized_query = query.lower().split(" ")
    doc_scores = _BM25_INDEX.get_scores(tokenized_query)
    
    # Sort docs by score
    scored_docs = sorted(zip(_CHUNKS, doc_scores), key=lambda x: x[1], reverse=True)
    
    if company_filter:
        scored_docs = [sd for sd in scored_docs if sd[0].metadata.get("companies") and company_filter in sd[0].metadata["companies"]]
    
    return [sd[0] for sd in scored_docs[:n]]


def retrieve(question: str, 
             company_filter: str = None,
             k: int = 6) -> list[Document]:
    """
    Hybrid Retrieval (Vector + Keyword via Reciprocal Rank Fusion)
    """
    # 1. Vector Search
    vectorstore = get_vector_store()
    if company_filter:
        # We assume 'companies' is a list in metadata and chroma supports $contains. 
        # But wait, in Chroma, lists are supported differently in old versions. 
        # Actually in build_vector_store we might not have a clean 'companies' as a string. 
        # Let's fallback to searching all and filtering manually to be safe for vector search too, or assume it works.
        pass
        # To be completely safe against ChromaDB list metadata filter issues:
        vector_docs = vectorstore.similarity_search(question, k=20)
        vector_docs = [d for d in vector_docs if d.metadata.get("companies") and company_filter in d.metadata["companies"]][:10]
    else:
        vector_docs = vectorstore.similarity_search(question, k=10)
        
    # 2. Keyword Search
    bm25_docs = get_bm25_results(question, n=10, company_filter=company_filter)
    
    # 3. Reciprocal Rank Fusion (RRF)
    # RRF Score = 1 / (rank + k) where k is usually 60
    RRF_K = 60
    
    doc_scores = {}
    doc_map = {}
    
    # Add vector scores
    for rank, doc in enumerate(vector_docs):
        key = doc.page_content[:200]
        doc_map[key] = doc
        doc_scores[key] = 1.0 / (rank + RRF_K)
        
    # Add BM25 scores
    for rank, doc in enumerate(bm25_docs):
        key = doc.page_content[:200]
        doc_map[key] = doc
        doc_scores[key] = doc_scores.get(key, 0.0) + (1.0 / (rank + RRF_K))
        
    # Sort by RRF score
    sorted_keys = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
    
    # Return top K
    final_docs = [doc_map[key] for key in sorted_keys[:k]]
    
    return final_docs
