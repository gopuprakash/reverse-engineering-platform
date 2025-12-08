from loguru import logger
from src.db.config import SessionLocal
from src.db.repository import BusinessRuleRepository

class KnowledgeBaseManager:
    def __init__(self):
        self.session = SessionLocal()
        self.repo = BusinessRuleRepository(self.session)

    # UPDATED SIGNATURE: Added run_id parameter
    async def store_findings(self, result: dict, run_id: str):
        """
        Parses the result from the Orchestrator/LLM and saves it to DB
        linked to the specific run_id.
        """
        file_path = result.get("file_path")
        findings = result.get("findings", {})
        rules = findings.get("business_rules", [])
        
        if not rules:
            return

        try:
            # Inject file_path into each rule before saving
            for r in rules:
                r["file_path"] = file_path
            
            # DIRECT SAVE: No more querying for the "latest" run
            self.repo.bulk_insert_rules(rules, run_id)
            logger.info(f"Saved {len(rules)} rules for {file_path}")

        except Exception as e:
            logger.error(f"Failed to save rules for {file_path}: {e}")

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()