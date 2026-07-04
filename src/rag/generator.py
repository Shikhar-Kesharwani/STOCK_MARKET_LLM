from langchain_openai import ChatOpenAI
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

GPT4O_MINI_INPUT_COST  = 0.150 / 1_000_000
GPT4O_MINI_OUTPUT_COST = 0.600 / 1_000_000

def format_context(docs: list[Document]) -> str:
    """Format retrieved documents into context string."""
    sections = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        source_label = f"[Source {i}: {meta.get('type','').upper()} — {meta.get('company', meta.get('source', 'Unknown'))}]"
        sections.append(f"{source_label}\n{doc.page_content}")
    return "\n\n".join(sections)


def generate_answer(question: str, 
                    docs: list[Document],
                    langfuse,
                    span) -> dict:
    """
    Generate a grounded answer from retrieved documents.
    Returns answer + metadata for tracing.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=400
    )
    
    context = format_context(docs)
    
    prompt = f"""{SYSTEM_PROMPT}

DATA:
{context}

QUESTION: {question}

ANSWER:"""
    
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="llm-call",
        model="gpt-4o-mini",
        input=prompt
    ) as generation:
        
        response = llm.invoke(prompt)
        
        usage = response.usage_metadata
        input_tokens  = usage.get("input_tokens", 0) if usage else 0
        output_tokens = usage.get("output_tokens", 0) if usage else 0
        
        cost_usd = (
            input_tokens  * GPT4O_MINI_INPUT_COST +
            output_tokens * GPT4O_MINI_OUTPUT_COST
        )
        
        generation.update(
            output=response.content,
            usage={
                "input":       input_tokens,
                "output":      output_tokens,
                "total":       input_tokens + output_tokens,
                "unit":        "TOKENS",
                "input_cost":  input_tokens * GPT4O_MINI_INPUT_COST,
                "output_cost": output_tokens * GPT4O_MINI_OUTPUT_COST,
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
