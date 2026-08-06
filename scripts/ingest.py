import sys
import os

# Add root project directory to Python import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.rag_services import ingest_documents

if __name__ == "__main__":
    ingest_documents()