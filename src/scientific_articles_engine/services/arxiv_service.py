"""arXiv API service for searching academic papers."""

from datetime import datetime
from typing import Any, Dict, List

import arxiv

from ..core.protocols import PaperSearchServiceProtocol
from ..models.paper import Paper, PaperAuthor
from .base_service import BaseService


class ArxivService(BaseService, PaperSearchServiceProtocol):
    """Service for searching papers from arXiv.

    Uses the arxiv Python package to search and retrieve paper metadata.

    Attributes:
        client: arXiv client instance
        max_results: Maximum results to return per search
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the arXiv service.

        Args:
            config: Configuration dictionary with optional keys:
                - max_results: Maximum papers per search (default: 10)
                - timeout: Search timeout in seconds (default: 30)
        """
        super().__init__(service_name="arxiv", config=config)

        self.max_results = config.get("max_results", 10)
        self.timeout = config.get("timeout", 30)

        # Initialize arXiv client
        # Parameters for arXiv client initialization
        # page_size: Number of results per page
        # delay_seconds: Delay between requests in seconds
        # num_retries: Number of retry attempts for failed requests
        self.client = arxiv.Client(
            page_size=self.max_results,
            delay_seconds=config.get("delay_seconds", 3.0),
            num_retries=config.get("num_retries", 3),
        )
        self.logger.info(f"Initialized arXiv service (max_results={self.max_results})")

    async def search(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search for papers on arXiv.

        Args:
            query: Search query string
            max_results: Maximum number of papers to return

        Returns:
            List of Paper objects

        Raises:
            ServiceException: If search fails
        """
        try:
            self.logger.info(f"Searching arXiv for: '{query}' (max={max_results})")

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            papers = []
            for result in self.client.results(search):
                paper = self._convert_to_paper(result)
                papers.append(paper)

            self.logger.info(f"Found {len(papers)} papers from arXiv")
            return papers

        except Exception as e:
            self._handle_error(e, f"arXiv search failed for query: '{query}'")
            return []  # For type checking

    def get_service_name(self) -> str:
        """Get the service name.

        Returns:
            Service name string
        """
        return "arxiv"

    def _convert_to_paper(self, result: arxiv.Result) -> Paper:
        """Convert arXiv result to Paper model.

        Args:
            result: arXiv search result

        Returns:
            Paper object
        """
        authors = [
            PaperAuthor(name=author.name, affiliation=None)
            for author in result.authors
        ]

        return Paper(
            title=result.title,
            authors=authors,
            abstract=result.summary,
            url=result.entry_id,
            pdf_url=result.pdf_url,
            published_date=result.published,
            source="arxiv",
            paper_id=result.entry_id.split("/")[-1],  # Extract ID from URL
            citations_count=None,  # arXiv doesn't provide citation counts
            venue=result.journal_ref or "arXiv preprint",
        )
