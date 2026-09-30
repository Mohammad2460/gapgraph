from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT_DIR / "fixtures"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT_DIR / ".env", ".env"), extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-6-luna"
    openai_effort: str = "low"  # reasoning effort: none | low | medium | high — lower = faster

    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "medium"  # low | medium | high — lower = faster demo

    # Per-pillar mock switches: each pillar flips its own flag to 0 when its
    # real implementation works, without blocking anyone else.
    mock_extraction: bool = True  # Pillar A: /documents stream + /quiz
    mock_learner: bool = True  # Pillar B: /assess

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
