"""Service layer with AgentFactory for Dependency Injection.

This module implements the Dependency Inversion Principle (DIP) by providing
a factory that creates agents with their required dependencies.
"""

from typing import Any, Dict

from ..config import EngineConfig
from .arxiv_service import ArxivService
from .llm_service import LLMService
from .paper_cache_service import PaperCacheService
from .semantic_scholar_service import SemanticScholarService

__all__ = [
    "AgentFactory",
    "LLMService",
    "ArxivService",
    "SemanticScholarService",
    "PaperCacheService",
]


class AgentFactory:
    """Factory for creating agents with dependency injection.

    This class implements the Dependency Inversion Principle by:
    1. Creating service instances (LLM, arXiv, Semantic Scholar)
    2. Injecting these dependencies into agents
    3. Ensuring agents depend on abstractions (protocols) not concrete implementations

    Attributes:
        config: Engine configuration
        llm_service: Shared LLM service instance
        arxiv_service: Shared arXiv service instance
        semantic_scholar_service: Shared Semantic Scholar service instance
    """

    def __init__(self, config: EngineConfig):
        """Initialize the factory with configuration.

        Args:
            config: Engine configuration containing LLM and agent settings
        """
        self.config = config

        # Initialize shared services
        self.llm_service = LLMService(config.llm.model_dump())
        self.arxiv_service = ArxivService(
            {
                "max_results": config.agents.max_papers_per_source,
                "timeout": config.agents.search_timeout,
            }
        )
        self.semantic_scholar_service = SemanticScholarService(
            {
                "max_results": config.agents.max_papers_per_source,
                "timeout": config.agents.search_timeout,
            }
        )
        self.paper_cache_service = (
            PaperCacheService(config.database.model_dump())
            if config.database.enabled
            else None
        )

    def create_searcher(self) -> Any:
        """Create a Searcher agent with dependencies.

        Returns:
            SearcherAgent instance

        Note:
            Lazy import to avoid circular dependencies
        """
        from ..agents.searcher_agent import SearcherAgent

        return SearcherAgent(
            llm_service=self.llm_service,
            arxiv_service=self.arxiv_service,
            semantic_scholar_service=self.semantic_scholar_service,
            paper_cache=self.paper_cache_service,
            config=self._get_searcher_config(),
        )

    def create_writer(self) -> Any:
        """Create a Writer agent with dependencies.

        Returns:
            WriterAgent instance

        Note:
            Lazy import to avoid circular dependencies
        """
        from ..agents.writer_agent import WriterAgent

        return WriterAgent(
            llm_service=self.llm_service,
            config=self._get_writer_config(),
        )

    def create_reviewer(self) -> Any:
        """Create a Reviewer agent with dependencies.

        Returns:
            ReviewerAgent instance

        Note:
            Lazy import to avoid circular dependencies
        """
        from ..agents.reviewer_agent import ReviewerAgent

        return ReviewerAgent(
            llm_service=self.llm_service,
            config=self._get_reviewer_config(),
        )

    def create_visualizer(self) -> Any:
        """Create a Visualizer agent with dependencies.

        Returns:
            VisualizerAgent instance

        Note:
            Lazy import to avoid circular dependencies
        """
        from ..agents.visualizer_agent import VisualizerAgent

        return VisualizerAgent(
            llm_service=self.llm_service,
            config=self._get_visualizer_config(),
        )

    def _get_searcher_config(self) -> Dict[str, Any]:
        """Get configuration for Searcher agent.

        Returns:
            Configuration dictionary
        """
        return {
            "max_papers_per_source": self.config.agents.max_papers_per_source,
            "search_timeout": self.config.agents.search_timeout,
        }

    def _get_writer_config(self) -> Dict[str, Any]:
        """Get configuration for Writer agent.

        Returns:
            Configuration dictionary
        """
        return {
            "min_word_count": self.config.agents.min_word_count,
            "max_word_count": self.config.agents.max_word_count,
            "style_guide": self.config.agents.style_guide,
        }

    def _get_reviewer_config(self) -> Dict[str, Any]:
        """Get configuration for Reviewer agent.

        Returns:
            Configuration dictionary
        """
        return {
            "quality_threshold": self.config.agents.quality_threshold,
            "max_revisions": self.config.agents.max_revisions,
        }

    def _get_visualizer_config(self) -> Dict[str, Any]:
        """Get configuration for Visualizer agent.

        Returns:
            Configuration dictionary
        """
        return {
            "max_visualizations": self.config.agents.max_visualizations,
            "supported_types": self.config.agents.supported_types,
        }
