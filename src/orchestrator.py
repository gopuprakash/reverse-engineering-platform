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

    repo_manager = RepoManager()
    mcp = RepoMCPServer(repo_manager)
    kb = KnowledgeBaseManager()

    all_files = []
    for cb in config["codebases"]:
        meta = CodebaseMetadata(**cb)
        path = repo_manager.ensure_local_repo(meta.source)
        files = list(repo_manager.list_source_files(path))
        logger.info(f"Found {len(files)} files in {meta.name}")
        all_files.extend([(f, meta.language) for f in files])

    async def analyze_file(file_path, lang):
        return await mcp.extract_business_rules_from_file(file_path, lang)

    tasks = [analyze_file(f, lang) for f, lang in all_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, dict) and r.get("status") == "success":
            await kb.store_findings(r)

    kb.get_summary()
    logger.success("ANALYSIS COMPLETE!")
