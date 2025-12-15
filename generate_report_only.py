import asyncio
import sys
import argparse
from loguru import logger

from src.db.config import SessionLocal
from src.db.models import AnalysisRun, Project
from src.reporting import ReportGenerator
from src.mcp_server import RepoMCPServer
from src.llm.factory import get_llm_client

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Project Summary Report for a specific Run ID")
    parser.add_argument("--run-id", required=True, help="The UUID of the analysis run")
    return parser.parse_args()

async def main():
    args = parse_args()
    run_id = args.run_id
    
    logger.info(f"Starting Standalone Report Generator for Run ID: {run_id}")
    
    db = SessionLocal()
    try:
        # 1. Validate Run ID
        run_record = db.query(AnalysisRun).filter(AnalysisRun.run_id == run_id).first()
        if not run_record:
            logger.error(f"Run ID {run_id} not found in database!")
            return

        # 2. Get Project Name
        project = db.query(Project).filter(Project.id == run_record.project_id).first()
        project_name = project.name if project else "Unknown Project"
        logger.info(f"Project: {project_name}")

        # 3. Initialize Components
        llm_client = get_llm_client()
        mcp_server = RepoMCPServer(llm_client)
        report_gen = ReportGenerator(db, mcp_server)

        # 4. Generate Report (Centralized Logic)
        # We don't pass file_paths here, letting the safe method discover them from the DB
        report_path = await report_gen.generate_report_safe(run_id, project_name)
        
        if report_path:
            logger.success(f"SUCCESS: Report saved to {report_path}")
        else:
            logger.warning("Report generation completed but no path returned (check logs).")

    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
