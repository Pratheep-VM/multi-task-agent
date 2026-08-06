from langchain_openai import ChatOpenAI
from app.config.settings import settings

def get_llm(
    model_name: str | None = None, 
    temperature: float | None = None,
    streaming: bool = True
) -> ChatOpenAI:
    model = model_name or settings.DEFAULT_MODEL
    temp = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE

    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing in your .env file.")

    return ChatOpenAI(
        model=model,
        temperature=temp,
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_BASE_URL,
        streaming=streaming
    )