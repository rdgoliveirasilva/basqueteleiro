"""Configuração centralizada — lê variáveis do .env.

Usa pydantic-settings, que lê automaticamente o arquivo .env na raiz do projeto.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # procura na raiz e no backend/
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Aplicação ---
    app_env: str = "dev"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5500"

    # --- HTTP ---
    user_agent: str = "basqueteleiro/0.1"
    http_timeout: float = 15.0
    http_retries: int = 3

    # --- Surto Olímpico (Supabase) ---
    surto_supabase_url: str = ""
    surto_supabase_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()