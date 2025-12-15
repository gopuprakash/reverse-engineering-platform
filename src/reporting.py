import os
import datetime
from loguru import logger
from src.db.repository import BusinessRuleRepository, GraphRepository
from src.mcp_server import RepoMCPServer

class ReportGenerator:
    def __init__(self, db_session, mcp_server: RepoMCPServer):
        self.db = db_session
        self.mcp_server = mcp_server
        self.rule_repo = BusinessRuleRepository(db_session)
        self.graph_repo = GraphRepository(db_session)

    def estimate_tokens(self, context_data: dict) -> float:
        import json
        dump = json.dumps(context_data)
        return len(dump) / 4.0

    async def prepare_report_context(self, run_id: str, project_name: str, file_paths: list[str]) -> dict:
        """
        Gathers data and prepares context dict.
        """
        # 1. Gather Data (Scoped to this run/files)
        rules = self.rule_repo.get_all_rules(run_id)
        summaries = self.graph_repo.get_summaries_for_files(file_paths)
        dependencies = self.graph_repo.get_dependencies_for_files(file_paths)

        # 2. Prepare Context
        return {
            "project_name": project_name,
            "date": datetime.date.today().isoformat(),
            "business_rules": [{"file_path": r.file_path, "title": r.title, "description": r.description} for r in rules],
            "code_summaries": [{"file_path": s.file_path, "summary": s.summary} for s in summaries],
            "dependencies": [{"source_file": d.source_file, "target_file": d.target_file, "relation_type": d.relation_type} for d in dependencies]
        }

    async def generate_report_safe(self, run_id: str, project_name: str, file_paths: list[str] = None) -> str:
        """
        Centralized method to generate a report with full safety checks:
        - Auto-discovers files if not provided
        - Prepares context
        - Estimates tokens and throttles if needed
        - Generates and saves report
        """
        # 1. Resolve Files
        if not file_paths:
            logger.info("No file list provided. Looking up files from run history...")
            file_paths = self.rule_repo.get_file_paths_for_run(run_id)
            if not file_paths:
                logger.warning(f"No files found for Run ID {run_id}. Report might be empty.")

        # 2. Prepare Context
        context = await self.prepare_report_context(run_id, project_name, file_paths)

        # 3. Token Estimation & Safe Throttling
        est_tokens = self.estimate_tokens(context)
        logger.info(f"Estimated Request Size: {est_tokens:,.0f} tokens")
        
        # Throttling Logic (Quota: 2M/min)
        if est_tokens > 200000: # Threshold: 200k tokens
            # Calculate wait time: (Tokens / 1.5M) * 60s
            # We use 1.5M as a conservative denominator to be safe
            wait_time = max((est_tokens / 1_500_000) * 60, 60)
            logger.warning(f"Large payload detected ({est_tokens:,.0f} tokens). Cooling down for {wait_time:.1f}s...")
            import asyncio
            await asyncio.sleep(wait_time)

        # 4. Generate & Save
        return await self.generate_and_save_report(context, run_id, project_name)

    async def generate_and_save_report(self, context_data: dict, run_id: str, project_name: str):
        # 5. Generate
        content = await self.mcp_server.generate_project_summary(context_data)
        
        # 6. Save
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Add timestamp to avoid overwriting: YYYY-MM-DD_HH-MM
        # Note: Windows does not allow colons in filenames
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{output_dir}/{project_name.replace(' ', '_')}_{run_id}_{timestamp}_Summary.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.success(f"Report generated: {filename}")
        return filename
