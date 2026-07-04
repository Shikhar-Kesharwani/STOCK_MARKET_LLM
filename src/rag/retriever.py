from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

def get_retriever(k: int = 6):
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        persist_directory="data/chroma_db",
        embedding_function=embedder
    )
    return vectorstore.as_retriever(
        search_type="mmr",          # Maximum Marginal Relevance
        search_kwargs={             # avoids returning duplicate chunks
            "k": k,
            "fetch_k": 20
        }
    )


def retrieve(question: str, 
             company_filter: str = None) -> list[Document]:
    """
    Retrieve relevant documents for a question.
    Optionally filter by company ticker.
    """
    retriever = get_retriever()
    
    if company_filter:
        # Filter to specific company
        vectorstore = retriever.vectorstore
        docs = vectorstore.similarity_search(
            question,
            k=6,
            filter={"ticker": company_filter}
        )
    else:
        docs = retriever.invoke(question)
    
    return docs
