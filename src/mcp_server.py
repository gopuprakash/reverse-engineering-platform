# src/mcp_server.py
import json
import math
from src.llm.factory import get_llm_client
from src.repo_manager import RepoManager
from src.prompts import render_prompt
from src.exceptions import ParseError, LLMError
from src.utils import retry_async
from loguru import logger
from src.chunking import UniversalChunker

class RepoMCPServer:
    def __init__(self, repo_manager: RepoManager):
        self.repo_manager = repo_manager
        self.llm = get_llm_client()

    @retry_async(max_retries=3)
    async def extract_business_rules_from_file(self, file_path: str, language: str = "python", context: str = "") -> dict:
        """
        Analyzes a file for business rules.
        Uses sliding window chunking for large files and injects global context.
        """
        try:
            full_code = self.repo_manager.read_file(file_path)
            
            # Initialize Universal Chunker
            chunker = UniversalChunker(full_code, language_id=language)
            chunks = chunker.chunk()
            
            logger.info(f"Splitting {file_path} into {len(chunks)} chunks using {chunker.language_id} parser")

            all_rules = []
            
            for i, code_chunk in enumerate(chunks):
                # --- Fix D: Inject Global Context (project_structure) ---
                prompt = render_prompt(
                    "extract_business_rules", 
                    language=language, 
                    code=code_chunk, 
                    project_structure=context
                )

                raw = await self.llm.complete(
                    prompt=prompt,
                    system="You are an expert reverse engineer. Return ONLY valid JSON matching the schema.",
                    response_format="json"
                )
                
                # Parse results for this chunk
                try:
                    data = self._safe_parse_json(raw, f"{file_path} [chunk {i+1}]")
                    
                    # Handle list vs dict output normalization
                    chunk_rules = []
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                chunk_rules.extend(item.get("business_rules", []))
                    elif isinstance(data, dict):
                        chunk_rules = data.get("business_rules", [])
                    
                    all_rules.extend(chunk_rules)
                    
                except Exception as e:
                    logger.error(f"Error parsing chunk {i+1} of {file_path}: {e}")
                    # We continue to the next chunk rather than failing the whole file

            logger.info(f"Successfully extracted {len(all_rules)} rules total from {file_path}")
            
            findings = {"business_rules": all_rules}

            return {
                "file_path": file_path,
                "analysis_type": "business_logic",
                "findings": findings,
                "status": "success"
            }

        except LLMError:
            logger.error(f"LLM failed for {file_path}")
            return {"file_path": file_path, "status": "llm_error", "error": "LLM call failed"}
        except Exception as e:
            logger.exception(f"Unexpected error analyzing {file_path}: {e}")
            return {"file_path": file_path, "status": "error", "error": str(e)}

    def _safe_parse_json(self, text: str, context: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed for {context}: {e}\nRaw output:\n{text[:1000]}")
            return {"raw_output": text, "parse_error": str(e), "business_rules": []}