import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    BASE_TELEGRAM_URL: str = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "doculoom-446020")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    MODEL: str = os.getenv("GCP_PROJECT_ID", "gemini-2.0-flash-exp")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

    class Config:
        env_file = ".env"


settings = Settings()
