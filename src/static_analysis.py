import re
import ast
from dataclasses import dataclass, field
from typing import List, Set, Optional
from loguru import logger
from src.repo_manager import RepoManager

@dataclass
class FileMetadata:
    """Holds the extracted structure of a file."""
    file_path: str
    language: str
    imports: Set[str] = field(default_factory=set)
    definitions: List[str] = field(default_factory=list)
    summary_content: str = ""

class StaticAnalyzer:
    def __init__(self, repo_manager: RepoManager):
        self.repo_manager = repo_manager

    def scan_file(self, file_path: str, language: str) -> FileMetadata:
        """
        Main entry point. Reads file and delegates to language-specific parsers.
        """
        meta = FileMetadata(file_path=file_path, language=language)
        
        try:
            code = self.repo_manager.read_file(file_path)
            
            # 1. Extract Imports & Definitions
            if language == "python":
                self._analyze_python(code, meta)
            else:
                self._analyze_generic(code, meta)

            # 2. Generate the "Summary" (Context Header)
            # This is what gets injected into the LLM for other files
            meta.summary_content = self._generate_summary_text(meta)
            
        except Exception as e:
            logger.warning(f"Static analysis failed for {file_path}: {e}")
            meta.summary_content = f"Error analyzing {file_path}"
            
        return meta

    def _analyze_python(self, code: str, meta: FileMetadata):
        """Uses Python's built-in AST for perfect accuracy."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # A. Extract Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        meta.imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        meta.imports.add(node.module)

                # B. Extract Definitions (Classes & Functions)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Get just the signature line (approximate)
                    sig = f"def {node.name}(...)"
                    # Try to get docstring
                    doc = ast.get_docstring(node)
                    if doc:
                        sig += f": {doc.splitlines()[0]}"
                    meta.definitions.append(sig)
                    
                elif isinstance(node, ast.ClassDef):
                    sig = f"class {node.name}"
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    if bases:
                        sig += f"({', '.join(bases)})"
                    meta.definitions.append(sig)
                    
        except SyntaxError:
            # Fallback to regex if AST fails (e.g. template files)
            self._analyze_generic(code, meta)

    def _analyze_generic(self, code: str, meta: FileMetadata):
        """
        Regex-based fallback for JS, Java, C#, etc.
        Not perfect, but sufficient for a 'Global Context' graph.
        """
        # 1. Regex for Imports
        # Matches: import X; from X import Y; using X; package X;
        import_patterns = [
            r'^\s*import\s+["\']?([\w\-\./]+)["\']?',          # JS/Python/Go
            r'^\s*from\s+([\w\.]+)\s+import',                   # Python
            r'^\s*using\s+([\w\.]+);',                          # C#
            r'^\s*package\s+([\w\.]+);',                        # Java
        ]
        
        for line in code.splitlines():
            # Check Imports
            for pattern in import_patterns:
                match = re.search(pattern, line)
                if match:
                    meta.imports.add(match.group(1))
            
            # Check Definitions (Naive)
            # Matches: class X, function X, def X, public void X
            if re.search(r'^\s*(class|def|function|public|private)\s+([A-Za-z0-9_]+)', line):
                if len(line.strip()) < 100: # heuristic to avoid noise
                    meta.definitions.append(line.strip().rstrip("{:").strip())

    def _generate_summary_text(self, meta: FileMetadata) -> str:
        """Creates the text block injected into the LLM context."""
        lines = [f"File: {meta.file_path}"]
        
        if meta.definitions:
            lines.append("Definitions:")
            # Limit to top 20 definitions to save tokens
            for d in meta.definitions[:20]:
                lines.append(f"  - {d}")
            if len(meta.definitions) > 20:
                lines.append("  - ... (more)")
                
        return "\n".join(lines)