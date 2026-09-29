"""Core abstractions and protocols for the Scientific Articles Engine."""

from .agent_base import BaseAgent
from .exceptions import (
    AgentExecutionError,
    EngineError,
    ServiceError,
    ValidationError,
)
from .protocols import LLMServiceProtocol, PaperSearchServiceProtocol
from .state import AgentState

__all__ = [
    "BaseAgent",
    "EngineError",
    "AgentExecutionError",
    "ServiceError",
    "ValidationError",
    "LLMServiceProtocol",
    "PaperSearchServiceProtocol",
    "AgentState",
]
