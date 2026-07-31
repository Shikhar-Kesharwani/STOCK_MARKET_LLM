from src.ingestion.stock_fetcher import fetch_all_companies
from src.ingestion.news_fetcher import fetch_news_documents
import json
import os
from datetime import datetime

def run_ingestion_pipeline():
    """
    Master ETL pipeline.
    Run this once to build the knowledge base.
    Run again weekly to refresh with new data.
    """
    print("="*60)
    print("INDIAN STOCK INTELLIGENCE — INGESTION PIPELINE")
    print("="*60)
    
    all_documents = []
    
    # Step 1: Stock price data
    print("\n[1/2] Fetching stock price and company data...")
    stock_docs = fetch_all_companies()
    all_documents.extend(stock_docs)
    
    # Step 2: News data
    print("\n[2/2] Fetching financial news...")
    news_docs = fetch_news_documents()
    all_documents.extend(news_docs)
    
    # Step 3: Save raw documents
    os.makedirs("data/processed", exist_ok=True)
    output_path = f"data/processed/documents_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    master_path = "data/processed/all_processed_docs.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, indent=2, default=str)

    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, indent=2, default=str)
    
    print(f"\n[OK] Saved {len(all_documents)} documents to {output_path} & {master_path}")
    print(f"  Stock docs: {len(stock_docs)}")
    print(f"  News docs:  {len(news_docs)}")
    
    return master_path


if __name__ == "__main__":
    run_ingestion_pipeline()
