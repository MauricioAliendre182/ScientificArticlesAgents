"""Custom exceptions for the Scientific Articles Engine."""


class EngineException(Exception):
    """Base exception for all engine-related errors."""

    pass


class AgentExecutionException(EngineException):
    """Raised when an agent fails to execute its task."""

    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}' execution failed: {message}")


class ServiceException(EngineException):
    """Raised when a service encounters an error."""

    def __init__(self, service_name: str, message: str):
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' error: {message}")


class ValidationException(EngineException):
    """Raised when data validation fails."""

    pass


class ConfigurationException(EngineException):
    """Raised when configuration is invalid or missing."""

    pass


class MaxRevisionsExceededException(EngineException):
    """Raised when maximum revision attempts are exceeded."""

    def __init__(self, max_revisions: int):
        self.max_revisions = max_revisions
        super().__init__(f"Maximum revisions ({max_revisions}) exceeded")
