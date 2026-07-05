import json
from langfuse import get_client
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()
langfuse = get_client()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=os.environ.get("GEMINI_API_KEY"))

INDIAN_COMPANIES = [
    "reliance", "tcs", "hdfc", "infosys", "icici",
    "airtel", "itc", "wipro", "maruti", "sun pharma"
]

INDIAN_CURRENCY = ["₹", "rupee", "lakh", "crore"]


def eval_llm_judge(question: str,
                   answer: str,
                   trace_id: str) -> float:
    """LLM evaluates answer quality 0-1."""
    prompt = f"""You are evaluating an Indian stock market AI answer.

QUESTION: {question}
ANSWER: {answer}

Score on these criteria:
1. Contains specific numbers (prices, %, dates)?
2. Directly answers the question?
3. Mentions specific company names?
4. Avoids hallucination or speculation?
5. Uses Indian context (₹, NSE, BSE, Indian companies)?

Respond ONLY with JSON:
{{"score": 0.0-1.0, "reason": "one sentence"}}"""

    try:
        response = llm.invoke(prompt)
        # Handle markdown json wrapping sometimes added by Gemini
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        score = float(result["score"])
        reason = result.get("reason", "")
    except Exception as e:
        score = 0.5
        reason = f"Parse error: {e}"

    langfuse.create_score(
        trace_id=trace_id,
        name="llm-judge-quality",
        value=score,
        comment=reason
    )
    return score


def eval_has_numbers(answer: str, trace_id: str) -> float:
    """Rule: does answer contain specific numbers?"""
    has_rupee   = "₹" in answer or "rupee" in answer.lower()
    has_percent = "%" in answer
    has_number  = any(c.isdigit() for c in answer)
    
    score = (has_rupee + has_percent + has_number) / 3
    
    langfuse.create_score(
        trace_id=trace_id,
        name="has-specific-numbers",
        value=score
    )
    return score


def eval_mentions_company(answer: str, trace_id: str) -> float:
    """Rule: does answer mention a known Indian company?"""
    answer_lower = answer.lower()
    found = any(c in answer_lower for c in INDIAN_COMPANIES)
    score = 1.0 if found else 0.0
    
    langfuse.create_score(
        trace_id=trace_id,
        name="mentions-company",
        value=score
    )
    return score


def eval_not_vague(answer: str, trace_id: str) -> float:
    """Rule: answer is not a vague refusal."""
    vague_phrases = [
        "i don't know", "i cannot", "no information",
        "not available", "cannot determine"
    ]
    is_vague = any(p in answer.lower() for p in vague_phrases)
    score = 0.0 if is_vague else 1.0
    
    langfuse.create_score(
        trace_id=trace_id,
        name="not-vague",
        value=score
    )
    return score


def run_all_evals(question: str,
                  answer: str,
                  trace_id: str) -> dict:
    """Run all evaluators and return combined report."""
    scores = {
        "llm_judge":      eval_llm_judge(question, answer, trace_id),
        "has_numbers":    eval_has_numbers(answer, trace_id),
        "mentions_company": eval_mentions_company(answer, trace_id),
        "not_vague":      eval_not_vague(answer, trace_id)
    }
    scores["overall"] = sum(scores.values()) / len(scores)
    return scores


def log_user_feedback(trace_id: str,
                      thumbs_up: bool,
                      comment: str = ""):
    langfuse.create_score(
        trace_id=trace_id,
        name="user-feedback",
        value=1.0 if thumbs_up else 0.0,
        comment=comment
    )
