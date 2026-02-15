"""
THÉRÈSE v2 - Configuration

Settings with pydantic-settings for type-safe configuration.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "THÉRÈSE"
    app_version: str = "0.1.20"
    debug: bool = False
    therese_env: str = "development"  # "development" or "production" (SEC-018)

    # Server
    host: str = "127.0.0.1"
    port: int = 17293

    # Paths
    therese_data_dir: str | None = None  # Override via env var for testing
    data_dir: Path | None = None  # Will be set in model_post_init
    db_path: Path | None = None  # Will be set in model_post_init

    # LLM Configuration
    llm_provider: Literal["claude", "mistral", "ollama"] = "claude"
    anthropic_api_key: str | None = None
    mistral_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Default models
    claude_model: str = "claude-sonnet-4-20250514"
    mistral_model: str = "mistral-large-latest"
    ollama_model: str = "mistral:7b"

    # Embeddings
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    embedding_dimensions: int = 768

    # Qdrant
    qdrant_path: Path | None = None  # Will be set in model_post_init
    qdrant_collection: str = "therese_memory"

    # Performance
    max_context_tokens: int = 8000
    max_memory_results: int = 10
    chunk_size: int = 500
    chunk_overlap: int = 50

    def model_post_init(self, __context) -> None:
        """Initialize paths after settings are loaded."""
        # Set data_dir from env or default
        if self.data_dir is None:
            if self.therese_data_dir:
                self.data_dir = Path(self.therese_data_dir)
            else:
                self.data_dir = Path.home() / ".therese"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Set default paths if not provided
        if self.db_path is None:
            self.db_path = self.data_dir / "therese.db"

        if self.qdrant_path is None:
            self.qdrant_path = self.data_dir / "qdrant"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
