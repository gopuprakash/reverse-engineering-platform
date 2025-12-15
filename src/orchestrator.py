import asyncio
import yaml
import uuid
from typing import List, Tuple
from loguru import logger

# Config & Core Modules
from src.config import settings
from src.repo_manager import RepoManager
from src.mcp_server import RepoMCPServer
from src.knowledge_base import KnowledgeBaseManager
from src.models import CodebaseMetadata
from src.exceptions import RepositoryError, LLMError

# Database Layer
from src.db.config import SessionLocal
from src.db.repository import GraphRepository
from src.db.models import Project, AnalysisRun

# Static Analysis (The Indexer)
# Note: Ensure src/static_analysis.py exists with a StaticAnalyzer class
from src.static_analysis import StaticAnalyzer 
from src.reporting import ReportGenerator 

async def run_analysis():
    """
    Main entry point for the Reverse Engineering Platform.
    
    Phases:
    1. Discovery: Locate repositories and register projects in DB.
    2. Indexing: Parse code to build the Dependency Graph (Nodes/Edges).
    3. Analysis: Use LLM + Graph Context to extract business rules.
    """
    
    # 0. System Initialization
    logger.add("logs/orchestrator_{time:YYYYMMDD}.log", rotation="50 MB", retention="10 days")
    logger.info("Initializing Orchestrator...")
    
    db_session = SessionLocal()
    
    try:
        # Load Configuration
        try:
            with open("config/codebases.yaml") as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.critical("Configuration file 'config/codebases.yaml' not found.")
            return

        # Initialize Managers
        repo_manager = RepoManager()
        mcp_server = RepoMCPServer(repo_manager)
        kb_manager = KnowledgeBaseManager() # Manages Business Rules storage
        graph_repo = GraphRepository(db_session) # Manages Dependency Graph
        # We need rule_repo directly in orchestrator to update status
        from src.db.repository import BusinessRuleRepository
        rule_repo = BusinessRuleRepository(db_session)
        
        static_analyzer = StaticAnalyzer(repo_manager) # Parses imports/signatures
        report_generator = ReportGenerator(db_session, mcp_server) # Phase 4

        # ---------------------------------------------------------
        # PHASE 1: DISCOVERY & REGISTRATION
        # ---------------------------------------------------------
        logger.info("--- PHASE 1: DISCOVERY & REGISTRATION ---")
        
        # Structure: (project_id, file_path, language, run_id)
        active_files: List[Tuple[str, str, str, str]] = []
        active_runs: List[Tuple[str, str]] = [] # (project_name, run_id)
        
        for cb_config in config_data.get("codebases", []):
            try:
                metadata = CodebaseMetadata(**cb_config)
                
                # A. Ensure Project Exists in DB
                project = db_session.query(Project).filter(Project.id == metadata.id).first()
                if not project:
                    logger.info(f"Registering new project: {metadata.name}")
                    project = Project(id=metadata.id, name=metadata.name)
                    db_session.add(project)
                    db_session.commit()
                
                # B. Clone/Locate Repo
                local_path = repo_manager.ensure_local_repo(metadata.source)
                
                # C. Register Analysis Run
                run_id = uuid.uuid4()
                run_record = AnalysisRun(run_id=run_id, project_id=metadata.id, status="INDEXING")
                db_session.add(run_record)
                db_session.commit()
                logger.info(f"Started Run {run_id} for {metadata.name}")
                active_runs.append((metadata.name, str(run_id)))

                # D. List Files
                files = list(repo_manager.list_source_files(local_path))
                logger.info(f"Found {len(files)} source files in {metadata.id}")
                
                for f in files:
                    active_files.append((metadata.id, f, metadata.language, str(run_id)))
                    
            except Exception as e:
                logger.error(f"Failed to initialize codebase {cb_config.get('name', 'Unknown')}: {e}")
                continue

        if not active_files:
            logger.warning("No files found to process. Exiting.")
            return

        # ---------------------------------------------------------
        # PHASE 2: INDEXING (BUILD THE GRAPH)
        # ---------------------------------------------------------
        logger.info(f"--- PHASE 2: INDEXING ({len(active_files)} files) ---")
        
        indexing_success_count = 0
        
        for proj_id, file_path, lang, _ in active_files: # Ignore run_id for indexing
            try:
                # 1. Static Analysis (Fast, CPU-bound)
                file_meta = static_analyzer.scan_file(file_path, lang)
                
                # 2. Store Summary (Node)
                graph_repo.save_summary(
                    file_path=file_path,
                    summary=file_meta.summary_content,
                    # Optional: Compute embedding here if static analyzer supports it
                    embedding=None 
                )
                
                # 3. Store Dependencies (Edges)
                for imported_module in file_meta.imports:
                    # Note: You might need a resolver logic here to map 'module' -> 'file_path'
                    # For now, we store the raw import string or a resolved path if available
                    graph_repo.add_dependency(
                        source=file_path,
                        target=imported_module, # e.g., "src.utils"
                        type="import"
                    )
                
                indexing_success_count += 1
                
            except Exception as e:
                logger.warning(f"Indexing failed for {file_path}: {e}")
        
        logger.success(f"Indexing complete. Graph populated with {indexing_success_count} nodes.")

        # Update run status
        # Note: In a real multi-project run, we'd update each run_id. 
        # For simplicity, based on current active_runs list.
        for _, rid in active_runs:
            rule_repo.update_run_status(rid, "ANALYZING")

        # ---------------------------------------------------------
        # PHASE 3: ANALYSIS (LLM + GRAPH RAG)
        # ---------------------------------------------------------
        logger.info("--- PHASE 3: SEMANTIC ANALYSIS ---")
        
        # Concurrency Control
        sem = asyncio.Semaphore(settings.max_concurrent_jobs)

        async def process_file_bounded(pid: str, fpath: str, lng: str, rid: str):
            async with sem:
                try:
                    # 1. GRAPH LOOKUP: Get Context specifically for this file
                    # This replaces the old "all files list"
                    smart_context = graph_repo.get_smart_context(fpath)
                    
                    # 2. LLM CALL: Extract Rules
                    result = await mcp_server.extract_business_rules_from_file(
                        file_path=fpath, 
                        language=lng, 
                        context=smart_context
                    )
                    
                    # 3. STORAGE: Save Rules
                    if result.get("status") == "success":
                        await kb_manager.store_findings(result, rid)
                        return True
                    else:
                        logger.warning(f"LLM extraction failed for {fpath}: {result.get('error')}")
                        return False

                except Exception as e:
                    logger.error(f"Critical failure processing {fpath}: {e}")
                    return False

        # Execute Parallel Tasks
        tasks = [process_file_bounded(pid, f, l, rid) for pid, f, l, rid in active_files]
        
        # Show progress bar if tqdm is desired, otherwise await gather
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.success(f"Analysis Complete. Processed {success_count}/{len(active_files)} files successfully.")

        # ---------------------------------------------------------
        # PHASE 4: REPORTING
        # ---------------------------------------------------------
        for _, rid in active_runs:
            rule_repo.update_run_status(rid, "REPORTING")

        logger.info("--- PHASE 4: REPORT GENERATION ---")
        
        for proj_name, rid in active_runs:
            try:
                # Filter files for this specific run
                run_files = [f for _, f, _, r in active_files if str(r) == rid]
                if not run_files:
                    logger.warning(f"No active files found for run {rid}, report may be incomplete.")
                
                # Centralized, safe report generation
                await report_generator.generate_report_safe(rid, proj_name, run_files)
                
                # Mark as completed
                rule_repo.update_run_status(rid, "COMPLETED")
                
            except Exception as e:
                logger.error(f"Failed to generate report for {proj_name}: {e}")
                rule_repo.update_run_status(rid, "FAILED")

    except Exception as e:
        logger.critical(f"Orchestrator crashed: {e}")
        raise
    finally:
        db_session.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_analysis())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")