# src/llm/base.py
from abc import ABC, abstractmethod
from typing import Any

class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str | None = None, response_format: Any = None) -> str:
        pass