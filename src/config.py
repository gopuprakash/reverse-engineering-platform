# src/config.py
from pydantic_settings import BaseSettings
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
    
    # Gemini-specific
    gemini_project_id: str | None = None  # Optional: for Vertex AI
    gemini_location: str = "us-central1"   # Only needed for Vertex AI

    # Database
    kb_db_name: str = "reverse_engineering_kb"
    kb_db_user: str = "postgres"
    kb_db_password: str = ""
    kb_db_host: str = "localhost"
    kb_db_port: int = 5432

    # Processing
    max_concurrent_jobs: int = 6
    file_extensions: tuple[str, ...] = (".py", ".cs", ".js", ".ts", ".java")
    exclude_dirs: set[str] = {
        ".git", "venv", ".venv", "node_modules", "__pycache__",
        "dist", "build", "env", ".env", "bin", "obj"
    }

    model_config = {"env_prefix": "RE_", "case_sensitive": False}

settings = Settings()