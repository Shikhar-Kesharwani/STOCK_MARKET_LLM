import time
import os
import uuid
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv
from src.rag.retriever import retrieve
from src.rag.generator import generate_answer, format_context

load_dotenv()
langfuse = get_client()


def ask_stock_rag_with_session(
    question: str,
    user_id: str = "anonymous",
    session_id: str = None,
    company_filter: str = None
) -> dict:
    """
    Full RAG pipeline using modern Langfuse SDK.
    Supports sessions, tags, and environments.
    """
    start = time.time()
    
    if not session_id:
        session_id = str(uuid.uuid4())
        
    tags = ["stock-intelligence", "rag"]
    if company_filter:
        tags.append(f"company:{company_filter}")
        
    if any(word in question.lower() for word in ["fall", "drop", "crash", "down"]):
        tags.append("query-type:bearish")
    elif any(word in question.lower() for word in ["rise", "gain", "up", "bull"]):
        tags.append("query-type:bullish")
    else:
        tags.append("query-type:general")
    
    environment = os.getenv("LANGFUSE_ENVIRONMENT", "development")
    
    with langfuse.start_as_current_observation(
        as_type="span",
        name="stock-query",
        session_id=session_id,
        user_id=user_id,
        tags=tags,
        metadata={"environment": environment, "company_filter": company_filter}
    ) as span:
        
        # Step 1: Retrieve
        with langfuse.start_as_current_observation(
            as_type="span",
            name="stock-retrieval"
        ) as retrieval_span:
            docs = retrieve(question, company_filter)
            retrieval_span.update(output=f"Retrieved {len(docs)} docs")
        
        # Step 2: Generate
        result = generate_answer(question, docs, langfuse, span)
        
        latency = time.time() - start
        
        span.update(
            input={"question": question},
            output={"answer": result["answer"]}
        )
        
        trace_id = span.trace_id
        
        return {
            "question": question,
            "answer": result["answer"],
            "sources": [d.metadata for d in docs],
            "latency": latency,
            "companies": result["companies_referenced"],
            "trace_id": trace_id,
            "session_id": session_id,
            "cost_usd": result.get("cost_usd", 0)
        }
