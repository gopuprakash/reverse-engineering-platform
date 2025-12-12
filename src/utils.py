import asyncio
from functools import wraps
from loguru import logger
import random

def retry_async(max_retries: int = 8, base_delay: float = 2.0, max_delay: float = 120.0):
    """
    Robust retry decorator with exponential backoff.
    Settings tuned for Gemini 429 Rate Limits.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    # If it's the last attempt, fail
                    if attempt == max_retries:
                        break
                    
                    # Detect Rate Limit errors (429 or Resource Exhausted)
                    error_msg = str(e).lower()
                    if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                        # Force a longer wait for rate limits (e.g. 30s + jitter)
                        wait_time = 30.0 + random.uniform(5, 15)
                        logger.warning(f"Rate Limit Hit! Cooling down for {wait_time:.1f}s... (Attempt {attempt}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        # Standard Backoff for other errors
                        jitter = random.uniform(0, delay * 0.1)
                        wait = min(delay + jitter, max_delay)
                        logger.warning(f"{func.__name__} failed: {e}. Retrying in {wait:.1f}s... (Attempt {attempt}/{max_retries})")
                        await asyncio.sleep(wait)
                        delay = min(delay * 2, max_delay)
            
            logger.error(f"{func.__name__} failed after {max_retries} attempts. Last error: {last_exc}")
            raise last_exc
        return wrapper
    return decorator