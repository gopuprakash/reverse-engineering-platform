# src/mcp_server.py
import json
from src.llm.factory import get_llm_client
from src.repo_manager import RepoManager
from src.prompts import render_prompt
from src.exceptions import ParseError, LLMError
from src.utils import retry_async
from loguru import logger

class RepoMCPServer:
    def __init__(self, repo_manager: RepoManager):
        self.repo_manager = repo_manager
        self.llm = get_llm_client()

    @retry_async(max_retries=3)
    async def extract_business_rules_from_file(self, file_path: str, language: str = "python") -> dict:
        try:
            code = self.repo_manager.read_file(file_path)
            if len(code) > 25000:
                code = code[:25000] + "\n\n... [truncated]"
                logger.debug(f"Truncated {file_path} to 25k chars")

            prompt = render_prompt("extract_business_rules", language=language, code=code)

            raw = await self.llm.complete(
                prompt=prompt,
                system="You are an expert reverse engineer. Return ONLY valid JSON matching the schema.",
                response_format="json"
            )

            #findings = self._safe_parse_json(raw, file_path)
            #logger.info(f"Successfully extracted rules from {file_path} ({len(findings.get('business_rules', []))} rules)")
            #
            
            try:
                data = self._safe_parse_json(raw, file_path)
                
                # Handle both cases: list of objects OR single object
                if isinstance(data, list):
                    all_rules = []
                    for item in data:
                        if isinstance(item, dict):
                            all_rules.extend(item.get("business_rules", []))
                else:
                    all_rules = data.get("business_rules", []) if isinstance(data, dict) else []
                
                rule_count = len(all_rules)
                logger.info(f"Successfully extracted {rule_count} rules from {file_path}")
                
                # Wrap back into expected format for downstream
                findings = {"business_rules": all_rules}
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse failed for {file_path}: {e}")
                findings = {"business_rules": [], "raw_output": raw}
            except Exception as e:
                logger.error(f"Unexpected parsing error for {file_path}: {e}")
                findings = {"business_rules": []}
            
            #


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