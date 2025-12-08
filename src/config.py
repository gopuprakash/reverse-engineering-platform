# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from typing import Literal

class Settings(BaseSettings):
    # Paths
    repo_root: Path = Path("/srv/repos")
    codebase_config: Path = Path("config/codebases.yaml")
    prompts_dir: Path = Path("config/prompts")

    # LLM
    llm_provider: Literal["gemini", "anthropic", "openai", "ollama"] = "gemini"
    model_name: str = "gemini-2.5-pro" 
    temperature: float = 0.1
    max_tokens: int = 8192
    
    # API Keys & Gemini Specifics
    # FIX: Renamed to match the standard GOOGLE_API_KEY variable
    google_api_key: str = Field(validation_alias="GOOGLE_API_KEY")
    gemini_project_id: str | None = None
    gemini_location: str = "us-central1"

    # Database
    kb_db_name: str = "reverse_engineering_kb"
    kb_db_user: str = "postgres"
    kb_db_host: str = "localhost"
    kb_db_port: int = 5432

    # Project Configuration
    project_id: str = "default-project"
    project_name: str = "Default Analysis Project"

    # Processing
    max_concurrent_jobs: int = 6
    file_extensions: tuple[str, ...] = (".py", ".cs", ".js", ".ts", ".java")
    exclude_dirs: set[str] = {
        ".git", "venv", ".venv", "node_modules", "__pycache__",
        "dist", "build", "env", ".env", "bin", "obj"
    }

    # FIX: Adjusted configuration to ensure .env is read correctly
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" 
    )

settings = Settings()