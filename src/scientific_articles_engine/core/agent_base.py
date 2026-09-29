"""Abstract base class for all agents in the system.

Implements the Single Responsibility Principle (SRP) and provides a common
interface for all agents (Liskov Substitution Principle - LSP).
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from ..utils.logger import get_logger
from .exceptions import AgentExecutionError
from .protocols import LLMServiceProtocol
from .state import AgentState

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all agents.

    All agents inherit from this class and implement the execute() method.
    This ensures consistency and allows for polymorphic agent usage.

    The generic type T represents the return type of the agent's execution.

    Attributes:
        llm_service: Language model service for text generation
        config: Agent-specific configuration dictionary
        agent_name: Name of the agent (for logging and error reporting)
    """

    def __init__(
        self,
        llm_service: LLMServiceProtocol,
        config: dict[str, Any],
        agent_name: str = "BaseAgent",
    ):
        """Initialize the agent with dependencies.

        Args:
            llm_service: LLM service implementing LLMServiceProtocol
            config: Configuration dictionary for the agent
            agent_name: Name identifier for the agent
        """
        self.llm_service = llm_service
        self.config = config
        self.agent_name = agent_name
        self.logger = get_logger(agent_name)

    @abstractmethod
    async def execute(self, state: AgentState) -> T:
        """Execute the agent's main task.

        This method must be implemented by all concrete agent classes.
        It receives the current workflow state and returns its specific output type.

        Args:
            state: Current workflow state

        Returns:
            Agent-specific output (type T)

        Raises:
            AgentExecutionException: If execution fails
        """
        pass

    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get the prompt template used by this agent.

        Returns:
            Prompt template string with placeholders

        Note:
            Override this method to provide agent-specific prompts
        """
        pass

    def _handle_error(self, error: Exception) -> None:
        """Handle and wrap agent execution errors.

        Args:
            error: Original exception that occurred

        Raises:
            AgentExecutionException: Wrapped exception with agent context
        """
        raise AgentExecutionError(agent_name=self.agent_name, message=str(error)) from error

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Safely retrieve a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.agent_name}')"
