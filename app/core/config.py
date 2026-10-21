import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    BRAVE_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./linkedin_gen.db"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Supabase Auth (Google sign-in). SUPABASE_URL/ANON_KEY are public values,
    # safe to hand to the frontend. Exactly one of SUPABASE_JWT_SECRET (legacy
    # HS256 projects) or SUPABASE_JWKS_URL (newer asymmetric-key projects)
    # should be set, depending on the Supabase project's signing config.
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_JWKS_URL: str = ""

    # Bcrypt hash of the shared invite passphrase. Never store the raw phrase.
    APP_PASSPHRASE_HASH: str = ""

    # Comma-separated list of origins allowed to call the API (frontend origin(s)).
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

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

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
