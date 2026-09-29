"""Searcher agent for finding and curating academic papers."""

import asyncio
from typing import Any

from ..core.agent_base import BaseAgent
from ..core.protocols import LLMServiceProtocol, PaperSearchServiceProtocol
from ..core.state import AgentState
from ..models.paper import Paper
from ..services.paper_cache_service import PaperCacheService


class SearcherAgent(BaseAgent[tuple[list[Paper], str]]):
    """Agent responsible for searching papers and generating an outline.

    This agent:
    1. Searches arXiv and Semantic Scholar for relevant papers
    2. Deduplicates and ranks papers by relevance
    3. Generates an article outline based on the found papers

    Returns:
        Tuple of (papers, outline)
    """

    def __init__(
        self,
        llm_service: LLMServiceProtocol,
        arxiv_service: PaperSearchServiceProtocol,
        semantic_scholar_service: PaperSearchServiceProtocol,
        config: dict[str, Any],
        paper_cache: PaperCacheService | None = None,
    ):
        """Initialize the Searcher agent.

        Args:
            llm_service: LLM service for outline generation
            arxiv_service: arXiv search service
            semantic_scholar_service: Semantic Scholar search service
            config: Agent configuration
        """
        super().__init__(llm_service, config, agent_name="SearcherAgent")
        self.arxiv_service = arxiv_service
        self.semantic_scholar_service = semantic_scholar_service
        self.paper_cache = paper_cache

    async def execute(self, state: AgentState) -> tuple[list[Paper], str]:
        """Execute the searcher agent's task.

        Args:
            state: Current workflow state

        Returns:
            Tuple of (papers, outline)

        Raises:
            AgentExecutionException: If search or outline generation fails
        """
        try:
            topic = state["topic"]
            self.logger.info(f"Searching for papers on topic: '{topic}'")

            # Search both sources in parallel
            arxiv_papers, scholar_papers = await self._search_all_sources(topic)

            # Combine and deduplicate
            all_papers = self._deduplicate_papers(arxiv_papers + scholar_papers)

            # Limit to max papers
            max_papers = self.get_config_value("max_papers_per_source", 10) * 2
            papers = all_papers[:max_papers]

            self.logger.info(f"Found {len(papers)} unique papers")

            # Generate outline
            outline = await self._generate_outline(topic, papers)

            self.logger.info("Outline generated successfully")

            return papers, outline

        except Exception as e:
            self._handle_error(e)
            return [], ""  # For type checking

    async def _search_all_sources(
        self, query: str
    ) -> tuple[list[Paper], list[Paper]]:
        """Search all paper sources in parallel.

        Args:
            query: Search query

        Returns:
            Tuple of (arxiv_papers, semantic_scholar_papers)
        """
        max_per_source = self.get_config_value("max_papers_per_source", 10)

        # Run searches concurrently
        arxiv_task = self.arxiv_service.search(query, max_per_source)
        scholar_task = self.semantic_scholar_service.search(query, max_per_source)

        # Gather search results from both sources concurrently
        # Use asyncio.gather to run both search tasks concurrently and handle exceptions
        results = await asyncio.gather(
            arxiv_task,
            scholar_task,
            return_exceptions=True,
        )

        source_names = ("arXiv", "Semantic Scholar")
        source_papers: list[list[Paper]] = []
        failures: list[str] = []

        # zip() is to pair each source name with its corresponding result for easier handling
        for source_name, result in zip(source_names, results):
            if isinstance(result, BaseException):
                if not isinstance(result, Exception):
                    raise result
                self.logger.warning(
                    "%s search failed; continuing with other source: %s",
                    source_name,
                    result,
                )
                failures.append(f"{source_name}: {result}")
            else:
                source_papers.append(result)

        # Live papers are those retrieved from the sources, deduplicated
        # deduplicate is to remove duplicate papers based on title similarity
        live_papers = self._deduplicate_papers(
            [paper for papers in source_papers for paper in papers]
        )
        cached_papers: list[Paper] = []

        # Review if we should fall back to the cache when there are failures or no live papers
        if self.paper_cache and (failures or not live_papers):
            try:
                cached_papers = await self.paper_cache.get(query)
                if cached_papers:
                    self.logger.info(
                        "Loaded %s cached papers for query '%s'",
                        len(cached_papers),
                        query,
                    )
            except Exception as error:
                self.logger.warning("Paper cache read failed; continuing without it: %s", error)

        # If all sources failed and there are no cached papers, raise an error
        if failures and not live_papers and not cached_papers:
            raise RuntimeError(
                "Live searches produced no papers and no cached results were available. "
                "Provider errors: "
                + "; ".join(failures)
            )

        combined_papers = self._deduplicate_papers(live_papers + cached_papers)

        # If there are live papers, update the cache with the combined results
        if self.paper_cache and live_papers:
            try:
                await self.paper_cache.put(query, combined_papers)
            except Exception as error:
                self.logger.warning("Paper cache write failed; continuing: %s", error)

        return combined_papers, []

    def _deduplicate_papers(self, papers: list[Paper]) -> list[Paper]:
        """Deduplicate papers by title similarity.

        Args:
            papers: List of papers (possibly with duplicates)

        Returns:
            Deduplicated list of papers
        """
        seen_titles = set()
        unique_papers = []

        for paper in papers:
            # Normalize title for comparison
            normalized_title = paper.title.lower().strip()

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_papers.append(paper)

        return unique_papers

    async def _generate_outline(self, topic: str, papers: list[Paper]) -> str:
        """Generate article outline using LLM.

        Args:
            topic: Research topic
            papers: List of papers found

        Returns:
            Article outline as string
        """
        # Build paper summaries for context
        paper_summaries = []
        for i, paper in enumerate(papers[:10], 1):  # Use top 10 papers
            summary = f"{i}. **{paper.title}** ({paper.source})\n"
            summary += f"   Authors: {', '.join(a.name for a in paper.authors[:3])}\n"
            summary += f"   Abstract: {paper.abstract[:200]}...\n"
            paper_summaries.append(summary)

        papers_context = "\n".join(paper_summaries)

        prompt = self.get_prompt_template().format(
            topic=topic, papers_context=papers_context
        )

        outline = await self.llm_service.generate(prompt)
        return outline

    def get_prompt_template(self) -> str:
        """Get the prompt template for outline generation.

        Returns:
            Prompt template string
        """
        return """You are a scientific writing expert tasked with creating an outline for a comprehensive article.

                **Topic**: {topic}

                **Available Papers**:
                {papers_context}

                Based on the papers found, create a detailed outline for a scientific article on this topic. The outline should:
                1. Have a clear Introduction section
                2. Include a Background/Literature Review section
                3. Organize main content into 2-4 thematic sections
                4. Have a Discussion section
                5. End with a Conclusion section

                Format the outline with clear section headings and bullet points for key points to cover.
                Each section should reference which papers will be used (by number).

                Provide ONLY the outline, no additional commentary."""
