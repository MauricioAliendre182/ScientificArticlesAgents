"""Semantic Scholar API service for searching academic papers."""

import os
from datetime import datetime
from typing import Any

from semanticscholar import SemanticScholar

from ..core.protocols import PaperSearchServiceProtocol
from ..models.paper import Paper, PaperAuthor
from .base_service import BaseService


class SemanticScholarService(BaseService, PaperSearchServiceProtocol):
    """Service for searching papers from Semantic Scholar.

    Uses the semanticscholar Python package to search and retrieve paper metadata.

    Attributes:
        client: Semantic Scholar client instance
        max_results: Maximum results to return per search
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize the Semantic Scholar service.

        Args:
            config: Configuration dictionary with optional keys:
                - max_results: Maximum papers per search (default: 10)
                - timeout: Search timeout in seconds (default: 30)
        """
        super().__init__(service_name="semantic_scholar", config=config)

        self.max_results = config.get("max_results", 10)
        self.timeout = config.get("timeout", 30)
        api_key = config.get("api_key") or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        retry = config.get("retry", False)

        # Initialize Semantic Scholar client
        self.client = SemanticScholar(
            timeout=self.timeout,
            api_key=api_key,
            retry=retry,
        )
        self.logger.info(f"Initialized Semantic Scholar service (max_results={self.max_results})")

    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search for papers on Semantic Scholar.

        Args:
            query: Search query string
            max_results: Maximum number of papers to return

        Returns:
            List of Paper objects

        Raises:
            ServiceException: If search fails
        """
        try:
            self.logger.info(f"Searching Semantic Scholar for: '{query}' (max={max_results})")

            # Search papers
            results = self.client.search_paper(query, limit=max_results)

            papers = []
            for result in results[:max_results]:
                paper = self._convert_to_paper(result)
                if paper:  # Only add if conversion was successful
                    papers.append(paper)

            self.logger.info(f"Found {len(papers)} papers from Semantic Scholar")
            return papers

        except Exception as e:
            self._handle_error(e, f"Semantic Scholar search failed for query: '{query}'")
            return []  # For type checking

    def get_service_name(self) -> str:
        """Get the service name.

        Returns:
            Service name string
        """
        return "semantic_scholar"

    def _convert_to_paper(self, result: Any) -> Paper | None:
        """Convert Semantic Scholar result to Paper model.

        Args:
            result: Semantic Scholar search result

        Returns:
            Paper object or None if conversion fails
        """
        try:
            # Extract authors
            authors = []
            if hasattr(result, "authors") and result.authors:
                for author in result.authors:
                    if isinstance(author, dict):
                        author_name = author.get("name", "Unknown")
                    else:
                        author_name = getattr(author, "name", "Unknown")
                    authors.append(PaperAuthor(name=author_name, affiliation=None))

            # Build URL
            paper_url = f"https://www.semanticscholar.org/paper/{result.paperId}"
            if hasattr(result, "externalIds") and result.externalIds:
                if "ArXiv" in result.externalIds:
                    paper_url = f"https://arxiv.org/abs/{result.externalIds['ArXiv']}"
                elif "DOI" in result.externalIds:
                    paper_url = f"https://doi.org/{result.externalIds['DOI']}"

            # Parse publication date
            pub_date = None
            if hasattr(result, "year") and result.year:
                try:
                    pub_date = datetime(result.year, 1, 1)
                except (ValueError, TypeError):
                    pass

            # Get PDF URL if available
            pdf_url = None
            if hasattr(result, "openAccessPdf") and result.openAccessPdf:
                open_access_pdf = result.openAccessPdf
                if isinstance(open_access_pdf, dict):
                    pdf_url = open_access_pdf.get("url")
                else:
                    pdf_url = getattr(open_access_pdf, "url", None)
                pdf_url = pdf_url or None

            return Paper(
                title=result.title or "Untitled",
                authors=authors,
                abstract=result.abstract or "No abstract available.",
                url=paper_url,
                pdf_url=pdf_url,
                published_date=pub_date,
                source="semantic_scholar",
                paper_id=result.paperId,
                citations_count=result.citationCount if hasattr(result, "citationCount") else None,
                venue=result.venue if hasattr(result, "venue") else None,
            )
        except Exception as e:
            self.logger.warning(f"Failed to convert Semantic Scholar result: {e}")
            return None
