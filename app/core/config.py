import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    BASE_TELEGRAM_URL: str = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "doculoom-446020")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    CLOUD_TASKS_QUEUE: str = os.getenv("CLOUD_TASKS_QUEUE", "her-queue")
    MODEL: str = os.getenv("GCP_PROJECT_ID", "gemini-2.0-flash-exp")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    VAULT_API_URL: str = os.getenv("VAULT_API_URL")
    HER_API_URL: str = os.getenv("HER_API_URL")
    MAX_MESSAGES_PER_USER: int = os.getenv("MAX_MESSAGES_PER_USER", 20)
    MEMORY_DUMP_SECONDS: int = int(os.getenv("MEMORY_DUMP_SECONDS", "240"))
    VAULT_DB_NAME: str = os.getenv("VAULT_DB_NAME", "vault")

    class Config:
        env_file = ".env"


settings = Settings()
