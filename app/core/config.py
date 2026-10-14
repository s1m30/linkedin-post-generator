import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    BRAVE_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./linkedin_gen.db"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Locate the .env file in the backend root directory (two levels up from core/config.py)
    model_config = ConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
