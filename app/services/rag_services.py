import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DATA_DIR = "data"
CHROMA_PATH = os.path.join("data", "chroma_db")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Load once at module level — reused for every query, never reloaded
_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
_vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=_embeddings)


def get_vector_store() -> Chroma:
    return _vector_store


def ingest_documents():
    print("Loading documents from data/ directory...")

    loader = DirectoryLoader(DATA_DIR, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("No .txt files found in data/ to ingest.")
        return

    print(f"Loaded {len(documents)} document(s).")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    global _vector_store
    _vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=_embeddings,
        persist_directory=CHROMA_PATH
    )

    print(f"Ingested into Vector Database at '{CHROMA_PATH}'!")
    return _vector_store
