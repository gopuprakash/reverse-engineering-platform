from pathlib import Path
from typing import Iterable
import git
import hashlib

from loguru import logger

class RepoManager:
    def __init__(self, config=None):
        self.root = Path("C:/reverse-engineer/projects").resolve()

    def ensure_local_repo(self, path_or_url: str) -> str:
        # Check if it's a local path first
        path = Path(path_or_url)
        if path.exists():
            return str(path.resolve())
            
        # If not local, assume it's a git URL
        # Check for common git URL patterns
        is_git_url = (
            path_or_url.startswith(("http://", "https://", "git://", "ssh://", "git@"))
            or path_or_url.endswith(".git")
        )
        if is_git_url:
            # Create a unique folder name based on the URL hash to avoid collisions
            repo_hash = hashlib.md5(path_or_url.encode()).hexdigest()[:8]
            repo_name = path_or_url.split("/")[-1].replace(".git", "")
            target_dir = self.root / f"{repo_name}_{repo_hash}"
            
            if target_dir.exists():
                logger.info(f"Repository already exists at {target_dir}")
                return str(target_dir)
                
            logger.info(f"Cloning {path_or_url} to {target_dir}...")
            try:
                git.Repo.clone_from(path_or_url, target_dir)
                return str(target_dir)
            except Exception as e:
                logger.error(f"Failed to clone repository: {e}")
                raise
        
        raise ValueError(f"Invalid path or URL: {path_or_url}")

    def list_source_files(self, root_path: str, extensions=(".py", ".go", ".cs", ".js", ".ts", ".java")) -> Iterable[str]:
        root = Path(root_path)
        if not root.exists():
            return []
        exclude = {"node_modules", "dist", "build", "__pycache__", ".git", "venv", ".venv"}
        for file in root.rglob("*"):
            if file.suffix.lower() in extensions and not any(ex in file.parts for ex in exclude):
                yield str(file)

    def read_file(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
