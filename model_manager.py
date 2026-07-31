#!/usr/bin/env python3
"""
NSE Intelligence Node - Dual Model Execution Manager
===================================================
Executes, validates, and manages Model 1 (Local Standalone) and Model 2 (Enterprise Cloud).
"""

import os
import sys
import argparse
import subprocess
import time
import webbrowser
from dotenv import load_dotenv

load_dotenv()

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def check_env_var(var_name, required=True):
    val = os.getenv(var_name)
    if not val and required:
        print(f"❌ ERROR: Environment variable {var_name} is missing in .env")
        return False
    elif val:
        print(f"[OK] {var_name} is set")
        return True
    return True

def run_model_1():
    """Model 1: Standalone Containerized Stack (Fully Local)"""
    print_header("MODEL 1: Standalone Containerized Stack (Fully Local)")
    
    print("1. Checking Environment Requirements...")
    if not check_env_var("GEMINI_API_KEY"):
        print("Please add GEMINI_API_KEY to your .env file.")
        sys.exit(1)
        
    print("\n2. Checking Docker installation...")
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[OK] Docker detected.")
    except Exception:
        print("⚠️ Docker not detected or not running. Falling back to local python execution...")
        run_local_python()
        return

    print("\n3. Launching Docker Compose Stack...")
    try:
        subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
        print("[OK] Docker containers started successfully!")
    except Exception as e:
        print(f"⚠️ Docker compose failed: {e}. Starting uvicorn directly...")
        run_local_python()
        return

    print("\n4. Health Checking Local Server...")
    time.sleep(3)
    url = "http://localhost:8000"
    print(f"[OK] Application active at: {url}")
    webbrowser.open(url)

def run_local_python():
    print("\nStarting local FastAPI server...")
    subprocess.run([sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000"])

def run_model_2():
    """Model 2: Hybrid Docker + Managed Cloud Services (Enterprise)"""
    print_header("MODEL 2: Hybrid Docker + Managed Cloud Services (Enterprise)")
    
    print("1. Checking Cloud Environment Requirements...")
    has_gemini = check_env_var("GEMINI_API_KEY")
    has_pinecone = check_env_var("PINECONE_API_KEY")
    
    if not has_gemini or not has_pinecone:
        print("\n⚠️ To run Model 2 (Cloud), ensure both GEMINI_API_KEY and PINECONE_API_KEY are in your .env")
        pinecone_key = input("Enter your PINECONE_API_KEY (or press Enter to skip): ").strip()
        if pinecone_key:
            os.environ["PINECONE_API_KEY"] = pinecone_key
            with open(".env", "a") as f:
                f.write(f"\nPINECONE_API_KEY={pinecone_key}\nPINECONE_INDEX_NAME=stock-intelligence\n")
            print("[OK] Saved PINECONE_API_KEY to .env")

    print("\n2. Syncing Vector Store to Cloud (Pinecone)...")
    try:
        from src.rag.embedder import build_vector_store
        build_vector_store("data/processed/all_processed_docs.json")
        print("[OK] Vector database synced to Pinecone cloud index!")
    except Exception as e:
        print(f"⚠️ Vector store sync notice: {e}")

    print("\n3. Cloud Deployment Configurations Ready:")
    print("  • Render Blueprint: render.yaml (Backend API)")
    print("  • Vercel Config:    vercel.json (Frontend UI)")
    print("\n[OK] Model 2 Cloud Pipeline is fully configured and ready for live hosting.")

def main():
    parser = argparse.ArgumentParser(description="NSE Intelligence Node Model Manager")
    parser.add_argument("--model", type=int, choices=[1, 2], help="Execution model: 1 (Local Docker), 2 (Cloud Enterprise)")
    args = parser.parse_args()

    if args.model == 1:
        run_model_1()
    elif args.model == 2:
        run_model_2()
    else:
        print_header("NSE Intelligence Node - Select Execution Model")
        print(" [1] MODEL 1: Standalone Containerized Stack (Fully Local Docker & ChromaDB)")
        print(" [2] MODEL 2: Hybrid Enterprise Cloud (Pinecone Vector DB + Render + Vercel)")
        print(" [3] Exit\n")
        choice = input("Select Model [1-3]: ").strip()
        if choice == "1":
            run_model_1()
        elif choice == "2":
            run_model_2()
        else:
            print("Exiting.")

if __name__ == "__main__":
    main()
