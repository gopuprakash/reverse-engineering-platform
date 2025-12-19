import tree_sitter
from tree_sitter_language_pack import get_language, get_parser
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class CodeChunk:
    code: str
    start_line: int
    end_line: int
    name: str
    type: str  # 'class', 'function', 'method'

class UniversalChunker:
    # Configuration: Which AST nodes constitute a "chunk" in each language?
    LANGUAGE_CONFIG = {
        "python": {
            "split_nodes": {"class_definition", "function_definition", "async_function_definition"},
            "context_nodes": {"import_statement", "import_from_statement"},
            "name_field": "name"
        },
        "java": {
            "split_nodes": {"class_declaration", "method_declaration", "interface_declaration", "enum_declaration"},
            "context_nodes": {"import_declaration", "package_declaration"},
            "name_field": "name"
        },
        "c_sharp": {
            "split_nodes": {"class_declaration", "method_declaration", "interface_declaration", "struct_declaration"},
            "context_nodes": {"using_directive", "namespace_declaration"},
            "name_field": "name"
        },
        "go": {
            "split_nodes": {"function_declaration", "method_declaration", "type_declaration"},
            "context_nodes": {"import_declaration", "package_clause"},
            "name_field": "name"
        },
        "javascript": {
            "split_nodes": {"class_declaration", "function_declaration", "method_definition", "arrow_function"},
            "context_nodes": {"import_statement", "export_statement", "lexical_declaration", "variable_declaration"}, # Includes const x = require(...)
            "name_field": "name"
        }
    }

    def __init__(self, source_code: str, language_id: str = "python", max_chars: int = 15000):
        self.source = source_code
        self.source_bytes = source_code.encode("utf8")  # Store bytes for safe slicing
        self.max_chars = max_chars
        self.language_id = self._normalize_lang_id(language_id)
        
        try:
            self.parser = get_parser(self.language_id)
            self.lang_def = get_language(self.language_id)
            self.config = self.LANGUAGE_CONFIG.get(self.language_id)
        except Exception as e:
            # Fallback: Try manual import for specific languages
            try:
                if self.language_id == "c_sharp":
                    import tree_sitter_c_sharp
                    # Direct approach matching recent tree-sitter:
                    lang_capsule = tree_sitter_c_sharp.language()
                    self.lang_def = tree_sitter.Language(lang_capsule)
                    self.parser = tree_sitter.Parser(self.lang_def)
                    self.config = self.LANGUAGE_CONFIG.get(self.language_id)
                elif self.language_id == "javascript":
                    try:
                        import tree_sitter_javascript
                        self.lang_def = tree_sitter_javascript.language()
                    except ImportError:
                        # Try js alias if needed, though usually it's tree_sitter_javascript
                        pass
                    
                    self.parser = tree_sitter.Parser()
                    self.parser.set_language(self.lang_def)
                    self.config = self.LANGUAGE_CONFIG.get(self.language_id)
                else:
                    raise e
            except Exception as fallback_error:
                print(f"Warning: Could not load parser for {language_id} (Fallback also failed): {fallback_error}")
                self.config = None

    def _normalize_lang_id(self, lang: str) -> str:
        # Map common names to tree-sitter identifiers
        mapping = {"cs": "c_sharp", "c#": "c_sharp", "golang": "go", "py": "python", "js": "javascript", "ts": "javascript"}
        return mapping.get(lang.lower(), lang.lower())

    def chunk(self) -> List[CodeChunk]:
        """Main entry point."""
        if not self.config:
            return self._fallback_slicing()

        tree = self.parser.parse(self.source_bytes)
        root_node = tree.root_node

        # 1. Extract Global Context (Imports/Package defs)
        context_str = self._extract_context(root_node)

        # 2. Walk the tree to find split points
        chunks = []
        self._traverse(root_node, chunks, context_str)

        if not chunks:
            return self._fallback_slicing()

        return chunks

    def _extract_context(self, root) -> str:
        """Extracts imports and package definitions."""
        context_parts = []
        for child in root.children:
            if child.type in self.config["context_nodes"]:
                # Safe byte slicing
                text = self.source_bytes[child.start_byte : child.end_byte].decode("utf8")
                context_parts.append(text)
        return "\n".join(context_parts)

    def _traverse(self, node, chunks: List[CodeChunk], context_header: str):
        """Recursively finds chunks."""
        if node.type in self.config["split_nodes"]:
            # SAFE SLICING: Do not use node.text
            node_text = self.source_bytes[node.start_byte : node.end_byte].decode("utf8")
            
            # Identify the name of the function/class
            name_node = node.child_by_field_name(self.config["name_field"])
            if name_node:
                chunk_name = self.source_bytes[name_node.start_byte : name_node.end_byte].decode("utf8")
            else:
                chunk_name = "anonymous"

            if len(node_text) < self.max_chars:
                chunks.append(CodeChunk(
                    code=f"{context_header}\n\n{node_text}",
                    start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1,
                    name=chunk_name,
                    type=node.type
                ))
                return

        for child in node.children:
            self._traverse(child, chunks, context_header)

    def _fallback_slicing(self) -> List[CodeChunk]:
        """Naive string slicer for unsupported languages."""
        chunks = []
        start = 0
        overlap = 500
        while start < len(self.source):
            end = min(start + self.max_chars, len(self.source))
            chunks.append(CodeChunk(
                code=self.source[start:end],
                start_line=1 + self.source[:start].count('\n'),
                end_line=1 + self.source[:end].count('\n'),
                name=f"part_{len(chunks)}",
                type="slice"
            ))
            start += (self.max_chars - overlap)
        return chunks