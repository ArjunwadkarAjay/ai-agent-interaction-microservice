from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    MODEL_NAME: str = "gpt-3.5-turbo"
    SUMMARY_THRESHOLD: int = 15
    CHROMA_DB_HOST: str = "chromadb"
    CHROMA_DB_PORT: int = 8000
    UPLOAD_DIR: str = "uploads" # We will ignore this for file persistence

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
