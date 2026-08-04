from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langfuse import get_client
from src.observability.tracer import ask_stock_rag_with_session, run_debate_with_session
from src.observability.evaluator import run_all_evals, log_user_feedback
from dotenv import load_dotenv

load_dotenv()

langfuse = get_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    langfuse.flush()
    print("Langfuse flushed on shutdown")

app = FastAPI(
    title="Indian Stock Intelligence RAG",
    description="Production LLM App with Full Observability",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

from fastapi.responses import FileResponse

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Serve main frontend UI directly at root URL."""
    return FileResponse("frontend/index.html")


# ── Request/Response Models ───────────────────────────────
from typing import Optional

class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    company_filter: Optional[str] = None

class FeedbackRequest(BaseModel):
    trace_id: str
    thumbs_up: bool
    comment: str = ""


# ── Endpoints ─────────────────────────────────────────────
@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {
        "status": "healthy",
        "observability": "langfuse",
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}


@app.post("/ask")
async def ask(req: QueryRequest):
    """Main RAG endpoint — fully traced and evaluated."""
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    
    if len(req.question) > 500:
        raise HTTPException(400, "Question too long (max 500 chars)")
    
    try:
        # Get answer
        result = ask_stock_rag_with_session(
            question=req.question,
            user_id=req.user_id,
            session_id=req.session_id,
            company_filter=req.company_filter
        )
        
        # Auto-evaluate
        scores = run_all_evals(
            question=req.question,
            answer=result["answer"],
            trace_id=result["trace_id"]
        )
        
        return {
            "answer":           result["answer"],
            "sources":          result["sources"],
            "companies":        result["companies"],
            "latency_seconds":  round(result["latency"], 3),
            "quality_score":    round(scores["overall"], 2),
            "trace_id":         result["trace_id"],
            "session_id":       result["session_id"],
            "cost_usd":         result["cost_usd"]
        }
    
    except Exception as e:
        raise HTTPException(500, f"RAG pipeline error: {str(e)}")
    finally:
        langfuse.flush()

@app.post("/debate")
async def debate(req: QueryRequest):
    """Multi-Agent debate endpoint."""
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    
    if len(req.question) > 500:
        raise HTTPException(400, "Question too long (max 500 chars)")
    
    try:
        # Get dual answers
        result = run_debate_with_session(
            question=req.question,
            user_id=req.user_id,
            session_id=req.session_id,
            company_filter=req.company_filter
        )
        
        # Auto-evaluate just the bull answer to have some basic eval metric, or skip.
        # For simplicity, we just return the debate.
        
        return {
            "bull_answer":      result["bull_answer"],
            "bear_answer":      result["bear_answer"],
            "sources":          result["sources"],
            "companies":        result["companies"],
            "latency_seconds":  round(result["latency"], 3),
            "trace_id":         result["trace_id"],
            "session_id":       result["session_id"],
            "cost_usd":         result["cost_usd"]
        }
    
    except Exception as e:
        raise HTTPException(500, f"Debate pipeline error: {str(e)}")
    finally:
        langfuse.flush()


@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    """Log user thumbs up/down to Langfuse."""
    try:
        log_user_feedback(req.trace_id, req.thumbs_up, req.comment)
        return {"status": "logged", "trace_id": req.trace_id}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        langfuse.flush()


@app.get("/companies")
async def get_companies():
    """Return list of supported companies."""
    return {
        "companies": [
            {"ticker": "RELIANCE", "name": "Reliance Industries"},
            {"ticker": "TCS",      "name": "Tata Consultancy Services"},
            {"ticker": "HDFCBANK", "name": "HDFC Bank"},
            {"ticker": "INFY",     "name": "Infosys"},
            {"ticker": "ICICIBANK","name": "ICICI Bank"},
            {"ticker": "BHARTIARTL","name": "Bharti Airtel"},
            {"ticker": "ITC",      "name": "ITC Limited"},
            {"ticker": "WIPRO",    "name": "Wipro"},
            {"ticker": "MARUTI",   "name": "Maruti Suzuki"},
            {"ticker": "SUNPHARMA","name": "Sun Pharmaceutical"},
        ]
    }
