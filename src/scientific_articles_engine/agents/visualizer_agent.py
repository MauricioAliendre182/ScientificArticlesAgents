"""Visualizer agent for generating diagrams and tables."""

from typing import Any

from ..core.agent_base import BaseAgent
from ..core.protocols import LLMServiceProtocol
from ..core.state import AgentState
from ..models.article import Article
from ..models.visualization import Visualization, VisualizationType


class VisualizerAgent(BaseAgent[list[Visualization]]):
    """Agent responsible for generating visualizations for articles.

    This agent:
    1. Analyzes articles for visualization opportunities
    2. Generates tables, diagrams, and flowcharts
    3. Creates visualizations in appropriate formats (Markdown, Mermaid, etc.)

    Supports visualization types:
    - Tables: Comparison tables, data summaries
    - Diagrams: Conceptual diagrams, architecture diagrams
    - Flowcharts: Process flows, decision trees
    - Timelines: Historical progression, development stages
    """

    def __init__(
        self,
        llm_service: LLMServiceProtocol,
        config: dict[str, Any],
    ):
        """Initialize the Visualizer agent.

        Args:
            llm_service: LLM service for generation
            config: Agent configuration with keys:
                - max_visualizations: Maximum visualizations to generate
                - supported_types: List of supported visualization types
        """
        super().__init__(llm_service, config, agent_name="VisualizerAgent")

    async def execute(self, state: AgentState) -> list[Visualization]:
        """Execute the visualizer agent's task.

        Args:
            state: Current workflow state

        Returns:
            List of Visualization objects

        Raises:
            AgentExecutionException: If visualization generation fails
        """
        try:
            article = state["article"]
            topic = state["topic"]

            self.logger.info("Analyzing article for visualization opportunities")

            visualizations = await self._generate_visualizations(article, topic)

            self.logger.info(f"Generated {len(visualizations)} visualizations")

            return visualizations

        except Exception as e:
            self._handle_error(e)
            return []  # For type checking

    async def _generate_visualizations(
        self, article: Article, topic: str
    ) -> list[Visualization]:
        """Generate visualizations for an article.

        Args:
            article: Article to visualize
            topic: Article topic

        Returns:
            List of Visualization objects
        """
        article_text = article.to_markdown()
        max_viz = self.get_config_value("max_visualizations", 5)

        # First, identify visualization opportunities
        opportunities_prompt = self._get_opportunities_prompt(article_text, topic)
        opportunities_text = await self.llm_service.generate(opportunities_prompt)

        # Parse opportunities
        opportunities = self._parse_opportunities(opportunities_text)

        # Generate each visualization
        visualizations = []
        for i, opportunity in enumerate(opportunities[:max_viz], 1):
            viz = await self._generate_single_visualization(
                opportunity, article_text, i
            )
            if viz:
                visualizations.append(viz)

        return visualizations

    async def _generate_single_visualization(
        self, opportunity: dict[str, str], article_text: str, index: int
    ) -> Visualization:
        """Generate a single visualization.

        Args:
            opportunity: Visualization opportunity description
            article_text: Full article text for context
            index: Visualization index

        Returns:
            Visualization object
        """
        viz_type = opportunity.get("type", "table")
        title = opportunity.get("title", f"Visualization {index}")
        description = opportunity.get("description", "")

        # Generate visualization content
        prompt = self._get_generation_prompt(
            viz_type, title, description, article_text
        )
        content = await self.llm_service.generate(prompt)

        # Determine format based on type
        format_map = {
            "table": "markdown",
            "flowchart": "mermaid",
            "diagram": "mermaid",
            "graph": "mermaid",
            "timeline": "markdown",
        }

        return Visualization(
            type=VisualizationType(viz_type),
            title=title,
            content=content.strip(),
            format=format_map.get(viz_type, "markdown"),
            description=description,
        )

    def _parse_opportunities(self, opportunities_text: str) -> list[dict[str, str]]:
        """Parse visualization opportunities from LLM response.

        Args:
            opportunities_text: Text describing opportunities

        Returns:
            List of opportunity dictionaries
        """
        opportunities = []
        lines = opportunities_text.strip().split("\n")

        current_opp = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Type:"):
                if current_opp:
                    opportunities.append(current_opp)
                current_opp = {"type": line.split(":", 1)[1].strip().lower()}
            elif line.startswith("Title:"):
                current_opp["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("Description:"):
                current_opp["description"] = line.split(":", 1)[1].strip()

        if current_opp:
            opportunities.append(current_opp)

        return opportunities

    def _get_opportunities_prompt(self, article_text: str, topic: str) -> str:
        """Get prompt for identifying visualization opportunities.

        Args:
            article_text: Article text
            topic: Article topic

        Returns:
            Prompt string
        """
        max_viz = self.get_config_value("max_visualizations", 5)
        supported_types = self.get_config_value(
            "supported_types", ["table", "diagram", "flowchart"]
        )

        return f"""Analyze this scientific article and identify opportunities for visualizations.

                **Topic**: {topic}

                **Article**:
                {article_text}

                Identify up to {max_viz} visualizations that would enhance the article. For each, specify:
                - Type: One of {', '.join(supported_types)}
                - Title: Descriptive title for the visualization
                - Description: Brief description of what it should show

                Format each opportunity as:
                Type: <type>
                Title: <title>
                Description: <description>

                Focus on visualizations that would genuinely add value, such as:
                - Comparison tables for different approaches/methods
                - Flowcharts for processes or workflows
                - Diagrams for architectures or concepts
                - Timelines for historical developments"""

    def _get_generation_prompt(
        self, viz_type: str, title: str, description: str, article_text: str
    ) -> str:
        """Get prompt for generating a specific visualization.

        Args:
            viz_type: Type of visualization
            title: Visualization title
            description: What to visualize
            article_text: Article text for context

        Returns:
            Prompt string
        """
        if viz_type == "table":
            return f"""Create a Markdown table for the following:

**Title**: {title}
**Description**: {description}

**Article Context** (extract relevant data):
{article_text[:2000]}

Generate a well-formatted Markdown table. Include a clear header row and relevant data rows.
Provide ONLY the table, no additional text."""

        elif viz_type in ["flowchart", "diagram", "graph"]:
            return f"""Create a Mermaid diagram for the following:

**Title**: {title}
**Description**: {description}

**Article Context**:
{article_text[:2000]}

Generate valid Mermaid syntax for this visualization.
Use appropriate Mermaid diagram type (graph, flowchart, sequenceDiagram, etc.).
Provide ONLY the Mermaid code, no markdown code blocks or additional text."""

        else:  # timeline or other
            return f"""Create a visualization for the following:

**Type**: {viz_type}
**Title**: {title}
**Description**: {description}

**Article Context**:
{article_text[:2000]}

Generate the visualization in Markdown format.
Provide ONLY the visualization content, no additional text."""

    def get_prompt_template(self) -> str:
        """Get the prompt template.

        Returns:
            Prompt template string
        """
        return "Visualizer agent prompt (see _get_opportunities_prompt and _get_generation_prompt)"
