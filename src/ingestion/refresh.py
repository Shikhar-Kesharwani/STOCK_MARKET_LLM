import schedule
import time
import glob
import os
from datetime import datetime
from src.ingestion.pipeline import run_ingestion_pipeline
from src.rag.embedder import build_vector_store

def daily_refresh():
    """Run every day at 6am to get fresh market data."""
    print(f"[{datetime.now()}] Starting daily refresh...")
    
    # Step 1: Fetch new data
    run_ingestion_pipeline()
    
    # Step 2: Find latest processed file
    files = sorted(glob.glob("data/processed/documents_*.json"))
    if not files:
        print("No processed files found")
        return
    
    latest = files[-1]
    
    # Step 3: Rebuild vector store with fresh data
    build_vector_store(latest)
    
    print(f"[{datetime.now()}] Daily refresh complete")


if __name__ == "__main__":
    # Run immediately on start
    daily_refresh()
    
    # Then schedule daily at 6am
    schedule.every().day.at("06:00").do(daily_refresh)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
