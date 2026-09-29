"""Service protocols for Interface Segregation Principle (ISP).

These protocols define contracts that services must implement, allowing for
dependency inversion and easier testing through mocking.
"""

from typing import Protocol

from ..models.paper import Paper


# Protocol: it is an interface that defines a set of methods a service must
# implement without providing the implementation itself.
class LLMServiceProtocol(Protocol):
    """Protocol for Language Model service interactions."""

    async def generate(self, prompt: str, **kwargs: dict) -> str:
        """Generate text completion from a prompt.

        Args:
            prompt: The input prompt for the LLM
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        ...

    async def generate_with_structure(
        self, prompt: str, schema: dict, **kwargs: dict
    ) -> dict:
        """Generate structured output conforming to a schema.

        Args:
            prompt: The input prompt for the LLM
            schema: JSON schema or Pydantic model for structured output
            **kwargs: Additional generation parameters

        Returns:
            Dictionary conforming to the provided schema
        """
        ...


class PaperSearchServiceProtocol(Protocol):
    """Protocol for academic paper search services."""

    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search for academic papers matching the query.

        Args:
            query: Search query string
            max_results: Maximum number of papers to return

        Returns:
            List of Paper objects matching the query
        """
        ...

    def get_service_name(self) -> str:
        """Get the name of the search service.

        Returns:
            Service name (e.g., 'arxiv', 'semantic_scholar')
        """
        ...


class VisualizationServiceProtocol(Protocol):
    """Protocol for visualization generation services."""

    async def generate_table(self, data: dict, caption: str) -> str:
        """Generate a formatted table.

        Args:
            data: Table data structure
            caption: Table caption

        Returns:
            Markdown or LaTeX table string
        """
        ...

    async def generate_diagram(self, description: str, diagram_type: str) -> str:
        """Generate a diagram from description.

        Args:
            description: Text description of the diagram
            diagram_type: Type of diagram (flowchart, sequence, etc.)

        Returns:
            Diagram markup (Mermaid, DOT, etc.)
        """
        ...
