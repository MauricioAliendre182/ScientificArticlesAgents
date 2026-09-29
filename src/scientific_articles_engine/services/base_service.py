"""Base service class for all external service integrations."""

from abc import ABC
from typing import Any

from ..core.exceptions import ServiceError
from ..utils.logger import get_logger


# ABC is to define an abstract base class that cannot be instantiated
# directly and is meant to be subclassed by concrete service implementations.
class BaseService(ABC):
    """Abstract base class for all services.

    Provides common functionality for error handling, logging, and configuration.

    Attributes:
        service_name: Name of the service for logging and errors
        config: Service-specific configuration
        logger: Logger instance for this service
    """

    def __init__(self, service_name: str, config: dict[str, Any]):
        """Initialize the service.

        Args:
            service_name: Name identifier for the service
            config: Configuration dictionary
        """
        self.service_name = service_name
        self.config = config
        self.logger = get_logger(f"{__name__}.{service_name}")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle and wrap service errors.

        Args:
            error: Original exception
            context: Additional context about the error

        Raises:
            ServiceException: Wrapped exception with service context
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(f"Service error in {self.service_name}: {error_msg}")
        raise ServiceError(
            service_name=self.service_name, message=error_msg
        ) from error

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
        """String representation of the service."""
        return f"{self.__class__.__name__}(name='{self.service_name}')"
