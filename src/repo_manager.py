import os
from pathlib import Path
from typing import Iterable
import git

class RepoManager:
    def __init__(self, config=None):
        self.root = Path("C:/reverse-engineer/projects").resolve()

    def ensure_local_repo(self, path_or_url: str) -> str:
        path = Path(path_or_url)
        if path.exists():
            return str(path.resolve())
        # For now, just return the path — we'll add git clone later
        return path_or_url

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
