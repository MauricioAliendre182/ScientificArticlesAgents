"""Writer agent for drafting and revising articles."""

from typing import Any

from ..core.agent_base import BaseAgent
from ..core.protocols import LLMServiceProtocol
from ..core.state import AgentState
from ..models.article import Article, ArticleSection
from ..models.paper import Paper
from ..models.review import ReviewResult


class WriterAgent(BaseAgent[Article]):
    """Agent responsible for writing and revising articles.

    This agent:
    1. Creates initial article drafts from outlines
    2. Revises articles based on reviewer feedback
    3. Ensures articles meet word count and style requirements

    The agent checks if a review exists in state to determine if it should
    create a new draft or revise an existing one.
    """

    def __init__(
        self,
        llm_service: LLMServiceProtocol,
        config: dict[str, Any],
    ):
        """Initialize the Writer agent.

        Args:
            llm_service: LLM service for text generation
            config: Agent configuration with keys:
                - min_word_count: Minimum article word count
                - max_word_count: Maximum article word count
                - style_guide: Writing style (academic, informal, etc.)
        """
        super().__init__(llm_service, config, agent_name="WriterAgent")

    async def execute(self, state: AgentState) -> Article:
        """Execute the writer agent's task.

        Args:
            state: Current workflow state

        Returns:
            Article object (new draft or revised version)

        Raises:
            AgentExecutionException: If writing fails
        """
        try:
            # Check if this is a revision or new draft
            if state.get("review") and state.get("article"):
                # Revision mode
                self.logger.info("Revising article based on reviewer feedback")
                article = await self._revise_article(
                    state["article"],
                    state["review"],
                    state["papers"],
                )
            else:
                # New draft mode
                self.logger.info("Creating new article draft")
                article = await self._create_draft(
                    state["topic"],
                    state["outline"],
                    state["papers"],
                )

            self.logger.info(
                f"Article completed: {article.word_count} words, version {article.version}"
            )
            return article

        except Exception as e:
            self._handle_error(e)
            return None  # For type checking

    async def _create_draft(
        self, topic: str, outline: str, papers: list[Paper]
    ) -> Article:
        """Create a new article draft.

        Args:
            topic: Article topic
            outline: Article outline
            papers: Source papers

        Returns:
            Article object with initial draft
        """
        # Build context from papers
        papers_context = self._build_papers_context(papers)

        # Generate article content
        prompt = self._get_draft_prompt(topic, outline, papers_context)
        article_text = await self.llm_service.generate(prompt)

        # Parse article into structured format
        article = self._parse_article(article_text, papers, version=1)

        return article

    async def _revise_article(
        self, article: Article, review: ReviewResult, papers: list[Paper]
    ) -> Article:
        """Revise an existing article based on feedback.

        Args:
            article: Existing article
            review: Review with feedback
            papers: Source papers

        Returns:
            Revised Article object
        """
        # Build context
        papers_context = self._build_papers_context(papers)
        current_article_text = article.to_markdown()
        feedback = review.get_feedback_for_revision()

        # Generate revised article
        prompt = self._get_revision_prompt(
            current_article_text, feedback, papers_context
        )
        revised_text = await self.llm_service.generate(prompt)

        # Parse revised article
        revised_article = self._parse_article(
            revised_text,
            papers,
            version=article.version + 1,
            revision_notes=review.summary,
        )

        return revised_article

    def _build_papers_context(self, papers: list[Paper]) -> str:
        """Build context string from papers.

        Args:
            papers: List of papers

        Returns:
            Formatted context string
        """
        context_parts = []
        for i, paper in enumerate(papers[:15], 1):  # Use top 15 papers
            context = f"[{i}] {paper.title}\n"
            context += f"    Authors: {', '.join(a.name for a in paper.authors[:3])}\n"
            context += f"    Abstract: {paper.abstract[:300]}...\n"
            context_parts.append(context)

        return "\n".join(context_parts)

    def _get_draft_prompt(
        self, topic: str, outline: str, papers_context: str
    ) -> str:
        """Get prompt for creating initial draft.

        Args:
            topic: Article topic
            outline: Article outline
            papers_context: Context from papers

        Returns:
            Prompt string
        """
        min_words = self.get_config_value("min_word_count", 1000)
        max_words = self.get_config_value("max_word_count", 5000)
        style = self.get_config_value("style_guide", "academic")

        return f"""You are a scientific writer creating a comprehensive article.

                    **Topic**: {topic}

                    **Outline**:
                    {outline}

                    **Source Papers**:
                    {papers_context}

                    Write a complete, well-structured article following the outline. Requirements:
                    - Word count: {min_words}-{max_words} words
                    - Style: {style}
                    - Include proper citations in the format [n] where n is the paper number
                    - Use clear section headings matching the outline
                    - Provide an abstract summarizing the article
                    - Include a references section at the end

                    Format your article with:
                    - Title on the first line (prefix with "# ")
                    - Abstract as a separate paragraph
                    - Clear section headings (prefix with "## ")
                    - Subsections where appropriate (prefix with "### ")
                    - A references section at the end

                    Write ONLY the article content, no meta-commentary."""

    def _get_revision_prompt(
        self, current_article: str, feedback: str, papers_context: str
    ) -> str:
        """Get prompt for revising article.

        Args:
            current_article: Current article text
            feedback: Reviewer feedback
            papers_context: Context from papers

        Returns:
            Prompt string
        """
        return f"""You are revising a scientific article based on reviewer feedback.

                    **Current Article**:
                    {current_article}

                    **Reviewer Feedback**:
                    {feedback}

                    **Source Papers (for additional citations if needed)**:
                    {papers_context}

                    Revise the article to address ALL the reviewer's suggestions and feedback.
                    Maintain the same format (title with #, sections with ##, subsections with ###).
                    Keep what works well and improve areas that need work.

                    Write ONLY the revised article, no meta-commentary."""

    def _parse_article(
        self,
        article_text: str,
        papers: list[Paper],
        version: int = 1,
        revision_notes: str | None = None,
    ) -> Article:
        """Parse generated article text into structured Article object.

        Args:
            article_text: Generated article text
            papers: Source papers for references
            version: Article version number
            revision_notes: Notes from revision (if applicable)

        Returns:
            Structured Article object
        """
        lines = article_text.strip().split("\n")

        # Extract title (first line starting with #)
        title = "Untitled"
        for line in lines:
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip()
                break

        # Extract abstract (paragraph after title, before first ##)
        abstract = ""
        in_abstract = False
        for line in lines:
            if line.strip().startswith("##"):
                break
            if in_abstract and line.strip():
                abstract += line.strip() + " "
            if title in line and not in_abstract:
                in_abstract = True

        abstract = abstract.strip() or "No abstract provided."

        # Parse sections
        sections = self._parse_sections(article_text)

        # Build references
        references = [paper.to_citation() for paper in papers[:20]]

        # Calculate word count
        word_count = len(article_text.split())

        return Article(
            title=title,
            abstract=abstract[:500],  # Limit abstract length
            sections=sections,
            references=references,
            word_count=word_count,
            version=version,
            revision_notes=revision_notes,
        )

    def _parse_sections(self, article_text: str) -> list[ArticleSection]:
        """Parse article text into sections.

        Args:
            article_text: Article text with markdown headings

        Returns:
            List of ArticleSection objects
        """
        lines = article_text.split("\n")
        sections = []
        current_section = None
        current_content = []

        for line in lines:
            # Main section (##)
            if line.strip().startswith("## "):
                # Save previous section
                if current_section:
                    current_section.content = "\n".join(current_content).strip()
                    sections.append(current_section)

                # Start new section
                title = line.strip().lstrip("#").strip()
                current_section = ArticleSection(
                    title=title, content="", subsections=[]
                )
                current_content = []

            # Skip title line (#) and subsections (###)
            elif line.strip().startswith("#"):
                continue

            # Regular content
            else:
                if current_section:
                    current_content.append(line)

        # Add last section
        if current_section:
            current_section.content = "\n".join(current_content).strip()
            sections.append(current_section)

        return sections

    def get_prompt_template(self) -> str:
        """Get the prompt template.

        Returns:
            Prompt template string
        """
        return "Writer agent prompt (see _get_draft_prompt and _get_revision_prompt)"
