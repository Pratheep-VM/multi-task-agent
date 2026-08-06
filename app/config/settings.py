from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str = "GROQ_API_KEY"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_TEMPERATURE: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()