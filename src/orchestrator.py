# src/orchestrator.py
import asyncio
import yaml
from loguru import logger
from src.config import settings
from src.repo_manager import RepoManager
from src.mcp_server import RepoMCPServer
from src.knowledge_base import KnowledgeBaseManager
from src.models import CodebaseMetadata

async def run_analysis():
    logger.add("logs/analysis_{time:YYYYMMDD}.log", rotation="7 days")

    # 1. Load Config
    try:
        with open("config/codebases.yaml") as f:
            config = yaml.safe_load(f)
    except:
        logger.error("config/codebases.yaml not found! Creating example...")
        example = {"codebases": [{"id": "my-project", "name": "My Project", "source": "projects/my-app", "language": "python"}]}
        import json
        with open("config/codebases.yaml", "w") as f:
            yaml.dump(example, f)
        logger.info("Created example config/codebases.yaml — please edit it!")
        return

    # 2. Initialize Managers
    repo_manager = RepoManager()
    mcp = RepoMCPServer(repo_manager)
    kb = KnowledgeBaseManager()

    # 3. Discovery Phase
    all_files = []
    for cb in config["codebases"]:
        meta = CodebaseMetadata(**cb)
        path = repo_manager.ensure_local_repo(meta.source)
        files = list(repo_manager.list_source_files(path))
        logger.info(f"Found {len(files)} files in {meta.name}")
        all_files.extend([(f, meta.language) for f in files])

    if not all_files:
        logger.warning("No files found to analyze. Check your config paths.")
        return

    # --- Fix D: Generate Global Context (File Tree) ---
    # We create a simple list of files to help the LLM understand the project structure
    # This helps it know that 'from src.utils import x' refers to a valid file.
    file_structure = "Project File Structure:\n" + "\n".join([f"- {f}" for f, _ in all_files])

    # --- Fix E: Concurrency Control ---
    # We use a semaphore to limit the number of parallel LLM calls based on config
    sem = asyncio.Semaphore(settings.max_concurrent_jobs)

    async def analyze_file_bounded(file_path, lang):
        async with sem:
            # We pass the global context here
            return await mcp.extract_business_rules_from_file(
                file_path, 
                lang, 
                context=file_structure
            )

    # 4. Execution Phase
    logger.info(f"Starting analysis of {len(all_files)} files with concurrency limit: {settings.max_concurrent_jobs}...")
    
    tasks = [analyze_file_bounded(f, lang) for f, lang in all_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 5. Storage Phase
    valid_results_count = 0
    for r in results:
        if isinstance(r, dict) and r.get("status") == "success":
            await kb.store_findings(r)
            valid_results_count += 1
        elif isinstance(r, Exception):
            logger.error(f"Task failed with exception: {r}")

    kb.get_summary()
    logger.success(f"ANALYSIS COMPLETE! Processed {valid_results_count}/{len(all_files)} files successfully.")