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

    async def generate_report(self, run_id: str, project_name: str, file_paths: list[str]):
        """
        Aggregates data for a specific run and generates a markdown report.
        """
        logger.info(f"Generating report for {project_name} (Run: {run_id})")

        # 1. Gather Data (Scoped to this run/files)
        rules = self.rule_repo.get_all_rules(run_id)
        if not rules:
            logger.warning("No business rules found for this run. Report may be empty.")

        summaries = self.graph_repo.get_summaries_for_files(file_paths)
        dependencies = self.graph_repo.get_dependencies_for_files(file_paths)

        # 2. Prepare Context for LLM
        context_data = {
            "project_name": project_name,
            "date": datetime.date.today().isoformat(),
            "business_rules": [
                {"file_path": r.file_path, "title": r.title, "description": r.description} 
                for r in rules
            ],
            "code_summaries": [
                {"file_path": s.file_path, "summary": s.summary}
                for s in summaries
            ],
            "dependencies": [
                {"source_file": d.source_file, "target_file": d.target_file, "relation_type": d.relation_type}
                for d in dependencies
            ]
        }

        # 3. Generate Content via LLM
        logger.info("Sending aggregated context to LLM for report generation...")
        report_content = await self.mcp_server.generate_project_summary(context_data)

        # 4. Save to File
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        # Fix: Include Run ID in filename
        filename = f"{output_dir}/{project_name.replace(' ', '_')}_{run_id}_Summary.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.success(f"Report generated: {filename}")
        return filename
