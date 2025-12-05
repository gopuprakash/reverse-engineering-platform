from src.config import settings
from src.llm.gemini import GeminiClient
from loguru import logger
import os

def get_llm_client():
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("Please set GOOGLE_API_KEY (get it from https://aistudio.google.com/app/apikey)")
    logger.info("Gemini 2.5 Pro initialized successfully")
    return GeminiClient()
