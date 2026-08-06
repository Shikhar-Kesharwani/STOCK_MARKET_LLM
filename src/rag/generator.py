from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert Indian stock market analyst.
You have access to historical price data, company financials,
and recent news for NSE-listed companies.

Rules you must follow:
1. Answer using ONLY the data provided below
2. Always mention specific numbers: prices in ₹, percentages, dates
3. Always cite which company and time period you are referring to
4. If data is insufficient say: "I don't have enough data on this"
5. Never speculate or make predictions — only report what the data shows
6. Keep answers concise and factual — 3-5 sentences maximum"""

BULL_PROMPT = """You are an aggressive Bullish investor. 
Using the provided data, argue WHY this stock is a strong BUY.
Highlight all positive news, growth metrics, and upside potential.
Ignore bearish signals or spin them positively.
Follow the same rules as above."""

BEAR_PROMPT = """You are a ruthless Bearish short-seller.
Using the provided data, argue WHY this stock is a terrible investment.
Highlight all risks, negative news, and downside potential.
Ignore bullish signals or downplay them.
Follow the same rules as above."""

# Using free tier Gemini API
GEMINI_INPUT_COST  = 0.0
GEMINI_OUTPUT_COST = 0.0

def format_context(docs: list[Document]) -> str:
    """Format retrieved documents into context string."""
    sections = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        source_label = f"[Source {i}: {meta.get('type','').upper()} — {meta.get('company', meta.get('source', 'Unknown'))}]"
        sections.append(f"{source_label}\n{doc.page_content}")
    return "\n\n".join(sections)


SESSION_STORE = {}

def generate_answer(question: str, 
                    docs: list[Document],
                    langfuse,
                    span,
                    session_id: str = None) -> dict:
    """
    Generate a grounded answer from retrieved documents.
    Returns answer + metadata for tracing.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        max_tokens=400,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    context = format_context(docs)
    
    # Retrieve chat history for this session
    history = SESSION_STORE.get(session_id, [])
    history_text = ""
    if history:
        history_text = "PREVIOUS CONVERSATION HISTORY:\n"
        for turn in history[-3:]: # last 3 turns
            history_text += f"User: {turn['user']}\nAI: {turn['ai']}\n\n"
    
    prompt = f"""{SYSTEM_PROMPT}

DATA:
{context}

{history_text}
QUESTION: {question}

ANSWER:"""
    
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="llm-call",
        model="gemini-1.5-flash",
        input=prompt
    ) as generation:
        
        response = llm.invoke(prompt)
        
        usage = response.usage_metadata
        input_tokens  = usage.get("input_tokens", 0) if usage else 0
        output_tokens = usage.get("output_tokens", 0) if usage else 0
        
        cost_usd = (
            input_tokens  * GEMINI_INPUT_COST +
            output_tokens * GEMINI_OUTPUT_COST
        )
        
        generation.update(
            output=response.content,
            usage={
                "input":       input_tokens,
                "output":      output_tokens,
                "total":       input_tokens + output_tokens,
                "unit":        "TOKENS",
                "input_cost":  input_tokens * GEMINI_INPUT_COST,
                "output_cost": output_tokens * GEMINI_OUTPUT_COST,
                "total_cost":  cost_usd
            }
        )
        
        return {
            "answer": response.content,
            "prompt": prompt,
            "num_sources": len(docs),
            "source_types": list(set(
                d.metadata.get("type", "unknown") for d in docs
            )),
            "companies_referenced": list(set(
                d.metadata.get("ticker", "") for d in docs
                if d.metadata.get("ticker")
            )),
            "cost_usd": cost_usd
        }

def generate_debate(question: str, 
                    docs: list[Document],
                    langfuse,
                    span,
                    session_id: str = None) -> dict:
    """
    Generate two grounded answers (Bull vs Bear) from retrieved documents.
    Runs sequentially for simplicity, returning both.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        max_tokens=300,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    context = format_context(docs)
    
    history = SESSION_STORE.get(session_id, [])
    history_text = ""
    if history:
        history_text = "PREVIOUS CONVERSATION HISTORY:\n"
        for turn in history[-2:]:
            history_text += f"User: {turn['user']}\nAI: {turn['ai']}\n\n"
            
    base_prompt_template = f"""DATA:
{context}

{history_text}
QUESTION: {question}

ANSWER:"""

    bull_prompt = f"{SYSTEM_PROMPT}\n\n{BULL_PROMPT}\n\n{base_prompt_template}"
    bear_prompt = f"{SYSTEM_PROMPT}\n\n{BEAR_PROMPT}\n\n{base_prompt_template}"
    
    total_cost_usd = 0.0
    
    # 1. Bull Call
    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-call-bull", model="gemini-1.5-flash", input=bull_prompt
    ) as bull_gen:
        bull_res = llm.invoke(bull_prompt)
        u1 = bull_res.usage_metadata
        i1 = u1.get("input_tokens", 0) if u1 else 0
        o1 = u1.get("output_tokens", 0) if u1 else 0
        c1 = i1 * GEMINI_INPUT_COST + o1 * GEMINI_OUTPUT_COST
        total_cost_usd += c1
        bull_gen.update(output=bull_res.content, usage={"input": i1, "output": o1, "total": i1+o1, "unit": "TOKENS", "total_cost": c1})
        
    # 2. Bear Call
    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-call-bear", model="gemini-1.5-flash", input=bear_prompt
    ) as bear_gen:
        bear_res = llm.invoke(bear_prompt)
        u2 = bear_res.usage_metadata
        i2 = u2.get("input_tokens", 0) if u2 else 0
        o2 = u2.get("output_tokens", 0) if u2 else 0
        c2 = i2 * GEMINI_INPUT_COST + o2 * GEMINI_OUTPUT_COST
        total_cost_usd += c2
        bear_gen.update(output=bear_res.content, usage={"input": i2, "output": o2, "total": i2+o2, "unit": "TOKENS", "total_cost": c2})
        
    return {
        "bull_answer": bull_res.content,
        "bear_answer": bear_res.content,
        "num_sources": len(docs),
        "source_types": list(set(d.metadata.get("type", "unknown") for d in docs)),
        "companies_referenced": list(set(d.metadata.get("ticker", "") for d in docs if d.metadata.get("ticker"))),
        "cost_usd": total_cost_usd
    }
