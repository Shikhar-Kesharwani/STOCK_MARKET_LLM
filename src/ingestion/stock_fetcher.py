import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

COMPANIES = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "HDFCBANK": "HDFC Bank",
    "INFY": "Infosys",
    "ICICIBANK": "ICICI Bank",
    "BHARTIARTL": "Bharti Airtel",
    "ITC": "ITC Limited",
    "WIPRO": "Wipro",
    "MARUTI": "Maruti Suzuki",
    "SUNPHARMA": "Sun Pharmaceutical",
}

def fetch_stock_data(ticker: str, company_name: str, 
                     years: int = 3) -> list[dict]:
    """
    Fetch historical price data and convert to
    text documents for RAG ingestion.
    """
    symbol = f"{ticker}.NS"  # NSE suffix for yfinance
    stock = yf.Ticker(symbol)
    
    end = datetime.now()
    start = end - timedelta(days=365 * years)
    
    # Historical price data
    hist = stock.history(start=start, end=end)
    
    # Company info
    info = stock.info
    
    documents = []
    
    # 1. Monthly summary documents
    hist_monthly = hist.resample("ME").agg({
        "Open":   "first",
        "Close":  "last",
        "High":   "max",
        "Low":    "min",
        "Volume": "sum"
    })
    
    for date, row in hist_monthly.iterrows():
        month_str = date.strftime("%B %Y")
        pct_change = ((row["Close"] - row["Open"]) / row["Open"]) * 100
        direction = "gained" if pct_change > 0 else "lost"
        
        doc_text = f"""
{company_name} ({ticker}) Stock Performance — {month_str}

The stock {direction} {abs(pct_change):.1f}% during {month_str}.
Opening price: ₹{row['Open']:.2f}
Closing price: ₹{row['Close']:.2f}
Monthly high: ₹{row['High']:.2f}
Monthly low: ₹{row['Low']:.2f}
Total volume traded: {row['Volume']:,.0f} shares

Sector: {info.get('sector', 'N/A')}
Industry: {info.get('industry', 'N/A')}
Market Cap: ₹{info.get('marketCap', 0)/1e9:.1f}B
        """.strip()
        
        documents.append({
            "text": doc_text,
            "metadata": {
                "company": company_name,
                "ticker": ticker,
                "date": date.strftime("%Y-%m"),
                "type": "price_summary",
                "pct_change": round(pct_change, 2)
            }
        })
    
    # 2. Company overview document
    overview = f"""
{company_name} ({ticker}) — Company Overview

Sector: {info.get('sector', 'N/A')}
Industry: {info.get('industry', 'N/A')}
Market Cap: ₹{info.get('marketCap', 0)/1e9:.1f} Billion
52-Week High: ₹{info.get('fiftyTwoWeekHigh', 'N/A')}
52-Week Low: ₹{info.get('fiftyTwoWeekLow', 'N/A')}
P/E Ratio: {info.get('trailingPE', 'N/A')}
EPS: {info.get('trailingEps', 'N/A')}
Dividend Yield: {info.get('dividendYield', 'N/A')}
Beta: {info.get('beta', 'N/A')}
Description: {str(info.get('longBusinessSummary', 'N/A'))[:500]}
    """.strip()
    
    documents.append({
        "text": overview,
        "metadata": {
            "company": company_name,
            "ticker": ticker,
            "type": "company_overview",
            "date": datetime.now().strftime("%Y-%m")
        }
    })
    
    print(f"  ✓ {company_name}: {len(documents)} documents")
    return documents


def fetch_all_companies() -> list[dict]:
    """Fetch data for all companies."""
    all_docs = []
    for ticker, name in COMPANIES.items():
        try:
            docs = fetch_stock_data(ticker, name)
            all_docs.extend(docs)
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")
    
    print(f"\nTotal documents: {len(all_docs)}")
    return all_docs
