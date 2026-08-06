import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Path configuration
DATA_DIR = "data"
CHROMA_PATH = os.path.join("data", "chroma_db")

# Use a fast, free, local HuggingFace embedding model (runs on your CPU)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

def get_embedding_function():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def ingest_documents():
    """
    Reads documents from data/, splits them into chunks, and stores in ChromaDB.
    """
    print("📂 Loading documents from data/ directory...")
    
    # 1. Load all text files in data/ directory
    loader = DirectoryLoader(DATA_DIR, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("⚠️ No .txt files found in data/ to ingest.")
        return

    print(f"📄 Loaded {len(documents)} document(s).")

    # 2. Chunk documents into smaller overlapping segments
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # 500 characters per chunk
        chunk_overlap=50      # 50 characters overlap to preserve context between chunks
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Split documents into {len(chunks)} chunks.")

    # 3. Embed & Store Chunks into Vector DB (ChromaDB)
    embeddings = get_embedding_function()
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print(f"✅ Successfully ingested into Vector Database at '{CHROMA_PATH}'!")
    return vector_store

def get_vector_store():
    """
    Loads existing vector store from disk.
    """
    embeddings = get_embedding_function()
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )