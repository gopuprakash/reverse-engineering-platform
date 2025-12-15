import asyncio
from functools import wraps
from loguru import logger
import random

import re

def retry_async(max_retries: int = 5, base_delay: float = 2.0, max_delay: float = 120.0):
    """
    Robust retry decorator with exponential backoff and smart rate limit handling.
    Parses 'Please retry in Xs' messages from Gemini API.
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
                    
                    error_msg = str(e).lower()
                    
                    # 1. Check for Rate Limit (429 / Resource Exhausted)
                    if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                        wait_time = 30.0 # Default fallback
                        
                        # Try to parse exact wait time: "Please retry in 41.246s"
                        match = re.search(r"retry in\s+([\d\.]+)\s*s", error_msg)
                        if match:
                            try:
                                wait_time = float(match.group(1)) + 5.0 # Add 5s buffer
                                logger.warning(f"Rate Limit: API requested wait of {match.group(1)}s. Sleeping {wait_time:.1f}s...")
                            except ValueError:
                                pass
                        else:
                            # Fallback jitter
                            wait_time = wait_time + random.uniform(5, 15)
                            logger.warning(f"Rate Limit hit. Sleeping {wait_time:.1f}s (Attempt {attempt}/{max_retries})")
                        
                        await asyncio.sleep(wait_time)
                        
                    # 2. Standard Backoff for other errors
                    else:
                        jitter = random.uniform(0, delay * 0.1)
                        wait = min(delay + jitter, max_delay)
                        logger.warning(f"{func.__name__} failed: {e}. Retrying in {wait:.1f}s... (Attempt {attempt}/{max_retries})")
                        await asyncio.sleep(wait)
                        delay = min(delay * 2, max_delay)
            
            logger.error(f"{func.__name__} failed after {max_retries} attempts. Last error: {last_exc}")
            raise last_exc
        return wrapper
    return decorator