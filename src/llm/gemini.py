# src/llm/gemini.py
import os
import asyncio
import google.generativeai as genai
from loguru import logger
from src.config import settings

class GeminiClient:
    def __init__(self):
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set! Get it from: https://aistudio.google.com/app/apikey")

            genai.configure(api_key=api_key)

            # CRITICAL: JSON mode + low temp MUST be set at model creation
            self.model = genai.GenerativeModel(
                model_name=settings.model_name,  # respects config (gemini-3-pro-preview!)
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.temperature,  # 0.1 from config
                    max_output_tokens=settings.max_tokens,
                    response_mime_type="application/json",  # ← THIS IS REQUIRED!
                )
            )
            logger.info(f"Gemini initialized: {settings.model_name} | JSON mode: ON | Temp: {settings.temperature}")
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")
            raise

    async def complete(self, prompt: str, system: str | None = None, response_format=None) -> str:
        try:
            content = [prompt]
            if system:
                content.insert(0, system)

            # No need to pass generation_config again — it's baked into the model!
            response = await asyncio.to_thread(
                self.model.generate_content,
                content
            )
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            raise