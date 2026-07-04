import feedparser
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time

# Free RSS feeds for Indian financial news
NEWS_FEEDS = {
    "Economic Times Markets": 
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol Markets": 
        "https://www.moneycontrol.com/rss/marketreports.xml",
    "Business Standard Markets": 
        "https://www.business-standard.com/rss/markets-106.rss",
    "LiveMint Markets": 
        "https://www.livemint.com/rss/markets",
}

COMPANY_KEYWORDS = {
    "RELIANCE":   ["Reliance", "RIL", "Mukesh Ambani", "Jio"],
    "TCS":        ["TCS", "Tata Consultancy", "IT services"],
    "HDFCBANK":   ["HDFC Bank", "HDFC", "banking"],
    "INFY":       ["Infosys", "Infy", "IT outsourcing"],
    "ICICIBANK":  ["ICICI Bank", "ICICI"],
    "BHARTIARTL": ["Airtel", "Bharti", "telecom"],
    "ITC":        ["ITC", "cigarettes", "FMCG"],
    "WIPRO":      ["Wipro"],
    "MARUTI":     ["Maruti", "Suzuki", "automobile"],
    "SUNPHARMA":  ["Sun Pharma", "Sun Pharmaceutical"],
}


def fetch_news_documents() -> list[dict]:
    """
    Fetch financial news from RSS feeds and convert
    to RAG documents.
    """
    all_docs = []
    
    for feed_name, feed_url in NEWS_FEEDS.items():
        print(f"  Fetching: {feed_name}")
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:50]:  # last 50 articles
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                published = entry.get("published", "")
                link = entry.get("link", "")
                
                # Clean HTML tags from summary
                if summary:
                    soup = BeautifulSoup(summary, "html.parser")
                    summary = soup.get_text()
                
                full_text = f"{title}. {summary}".strip()
                
                # Tag with relevant companies
                relevant_companies = []
                for ticker, keywords in COMPANY_KEYWORDS.items():
                    if any(kw.lower() in full_text.lower() 
                           for kw in keywords):
                        relevant_companies.append(ticker)
                
                doc_text = f"""
News Article: {title}

Source: {feed_name}
Published: {published}

{summary[:800]}
                """.strip()
                
                all_docs.append({
                    "text": doc_text,
                    "metadata": {
                        "type": "news",
                        "source": feed_name,
                        "title": title,
                        "published": published,
                        "companies": relevant_companies,
                        "url": link
                    }
                })
            
            time.sleep(1)  # polite rate limiting
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    print(f"\nTotal news documents: {len(all_docs)}")
    return all_docs
