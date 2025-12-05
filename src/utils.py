# src/utils.py
import asyncio
from functools import wraps
from loguru import logger
import random

def retry_async(max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
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
                    if attempt == max_retries:
                        break
                    jitter = random.uniform(0, delay * 0.1)
                    wait = min(delay + jitter, max_delay)
                    logger.warning(f"{func.__name__} failed (attempt {attempt}): {e}. Retrying in {wait:.1f}s...")
                    await asyncio.sleep(wait)
                    delay = min(delay * 2, max_delay)
            logger.error(f"{func.__name__} failed after {max_retries} attempts: {last_exc}")
            raise last_exc
        return wrapper
    return decorator