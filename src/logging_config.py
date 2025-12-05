# src/logging_config.py
import logging
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Pretty console for local dev
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# JSON logs for production (e.g. GCP, Datadog, Splunk)
logger.add(
    "logs/reverse_engineer_{time:YYYYMMDD}.jsonl",
    rotation="7 days",
    retention="30 days",
    compression="zip",
    serialize=True,
    level="DEBUG",
)