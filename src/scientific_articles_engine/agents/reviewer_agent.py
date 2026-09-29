"""Reviewer agent for evaluating article quality."""

from typing import Any

from ..core.agent_base import BaseAgent
from ..core.protocols import LLMServiceProtocol
from ..core.state import AgentState
from ..models.article import Article
from ..models.review import ReviewCriteria, ReviewResult


class ReviewerAgent(BaseAgent[ReviewResult]):
    """Agent responsible for reviewing and evaluating articles.

    This agent:
    1. Evaluates articles against multiple criteria
    2. Provides structured feedback and scores
    3. Determines if the article passes quality threshold
    4. Suggests specific improvements

    Evaluation criteria:
    - Scientific Rigor: Accuracy, depth, and methodology
    - Citation Quality: Appropriate and comprehensive references
    - Coherence: Logical flow and organization
    - Writing Quality: Clarity, grammar, and style
    """

    def __init__(
        self,
        llm_service: LLMServiceProtocol,
        config: dict[str, Any],
    ):
        """Initialize the Reviewer agent.

        Args:
            llm_service: LLM service for evaluation
            config: Agent configuration with keys:
                - quality_threshold: Minimum passing score (default: 7.0)
                - max_revisions: Maximum revision attempts (default: 3)
        """
        super().__init__(llm_service, config, agent_name="ReviewerAgent")

    async def execute(self, state: AgentState) -> ReviewResult:
        """Execute the reviewer agent's task.

        Args:
            state: Current workflow state

        Returns:
            ReviewResult with scores and feedback

        Raises:
            AgentExecutionException: If review fails
        """
        try:
            article = state["article"]
            topic = state["topic"]

            self.logger.info(f"Reviewing article (version {article.version})")

            # Generate structured review
            review = await self._review_article(article, topic)

            self.logger.info(
                f"Review complete: {review.overall_score}/10 "
                f"({'PASSED' if review.passed else 'NEEDS REVISION'})"
            )

            return review

        except Exception as e:
            self._handle_error(e)
            return None  # For type checking

    async def _review_article(self, article: Article, topic: str) -> ReviewResult:
        """Review an article and generate structured feedback.

        Args:
            article: Article to review
            topic: Original topic

        Returns:
            ReviewResult with scores and feedback
        """
        article_text = article.to_markdown()

        # Define review schema for structured output
        review_schema = {
            "type": "object",
            "properties": {
                "criteria_scores": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "criterion": {"type": "string"},
                            "score": {"type": "integer", "minimum": 1, "maximum": 10},
                            "feedback": {"type": "string"},
                        },
                        "required": ["criterion", "score", "feedback"],
                    },
                },
                "summary": {"type": "string"},
                "suggestions": {"type": "array", "items": {"type": "string"}},
                "strengths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["criteria_scores", "summary", "suggestions", "strengths"],
        }

        prompt = self._get_review_prompt(article_text, topic)

        # Get structured review from LLM
        review_data = await self.llm_service.generate_with_structure(prompt, review_schema)

        # Calculate overall score
        criteria_scores = [
            ReviewCriteria(**criterion) for criterion in review_data["criteria_scores"]
        ]
        overall_score = sum(c.score for c in criteria_scores) / len(criteria_scores)

        # Check if passed
        threshold = self.get_config_value("quality_threshold", 7.0)
        passed = overall_score >= threshold

        return ReviewResult(
            criteria_scores=criteria_scores,
            overall_score=overall_score,
            passed=passed,
            summary=review_data["summary"],
            suggestions=review_data.get("suggestions", []),
            strengths=review_data.get("strengths", []),
        )

    def _get_review_prompt(self, article_text: str, topic: str) -> str:
        """Get prompt for reviewing article.

        Args:
            article_text: Article to review
            topic: Original topic

        Returns:
            Prompt string
        """
        threshold = self.get_config_value("quality_threshold", 7.0)

        return f"""You are a scientific peer reviewer evaluating an article for publication quality.

                    **Original Topic**: {topic}

                    **Article to Review**:
                    {article_text}

                    Evaluate this article across four criteria, providing a score (1-10)
                    and detailed feedback for each:

                    1. **Scientific Rigor**: Is the content accurate, thorough, and
                    well-researched? Are claims properly supported?

                    2. **Citation Quality**: Are sources appropriate, recent, and
                    comprehensive? Are all claims properly cited?

                    3. **Coherence**: Does the article flow logically? Are sections
                    well-organized and transitions smooth?

                    4. **Writing Quality**: Is the writing clear, professional, and free
                    of errors? Is the style appropriate for a scientific audience?

                    Also provide:
                    - An overall summary of the article's quality
                    - Specific suggestions for improvement (3-5 items)
                    - Key strengths of the article (2-3 items)

                    The quality threshold for passing is {threshold}/10. Be constructive
                    but rigorous in your evaluation."""

    def get_prompt_template(self) -> str:
        """Get the prompt template.

        Returns:
            Prompt template string
        """
        return "Reviewer agent prompt (see _get_review_prompt)"
