import html

from mudraid import Agent
from langchain_core.tools import tool
from app.services.rag_services import get_vector_store
from dotenv import load_dotenv
load_dotenv()

research_client = Agent(prefix="RESEARCH")


@tool
def search_knowledge_base(query: str) -> str:
    """Searches Pradeep's confidential project documents, launch dates, codenames, and private files."""
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search(query, k=2)
        if not results:
            return "No matching information found in the private knowledge base."
        context = "\n---\n".join([doc.page_content for doc in results])
        return f"Retrieved Private Context:\n{html.escape(context)}"
    except Exception as e:
        return f"Error reading knowledge base: {str(e)}"
