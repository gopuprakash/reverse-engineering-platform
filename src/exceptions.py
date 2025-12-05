# src/exceptions.py
class ReverseEngineeringError(Exception):
    """Base exception"""

class LLMError(ReverseEngineeringError):
    """LLM call failed"""

class ParseError(ReverseEngineeringError):
    """Failed to parse LLM output"""

class RepositoryError(ReverseEngineeringError):
    """Git/repo access issue"""

class DatabaseError(ReverseEngineeringError):
    """KB persistence issue"""