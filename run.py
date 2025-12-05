# run.py
import asyncio
from src.logging_config import logger
from src.orchestrator import run_analysis

if __name__ == "__main__":
    try:
        asyncio.run(run_analysis())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.critical(f"Platform crashed: {e}")
        raise