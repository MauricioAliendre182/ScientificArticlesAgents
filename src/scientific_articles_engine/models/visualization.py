"""Pydantic models for visualizations."""

from enum import Enum

from pydantic import BaseModel, Field


class VisualizationType(str, Enum):
    """Types of visualizations that can be generated.

    Attributes:
        TABLE: Data table (Markdown or LaTeX)
        FLOWCHART: Process flowchart
        DIAGRAM: General diagram
        GRAPH: Graph/network visualization
        TIMELINE: Timeline visualization
    """

    TABLE = "table"
    FLOWCHART = "flowchart"
    DIAGRAM = "diagram"
    GRAPH = "graph"
    TIMELINE = "timeline"


class Visualization(BaseModel):
    """Generated visualization (diagram, table, etc.).

    Attributes:
        type: Type of visualization
        title: Visualization title/caption
        content: Visualization content (Markdown, Mermaid, LaTeX, etc.)
        format: Content format (markdown, mermaid, latex, dot)
        description: Description of what the visualization shows
    """

    type: VisualizationType = Field(..., description="Type of visualization")
    title: str = Field(..., description="Visualization title/caption")
    content: str = Field(..., description="Visualization content/markup")
    format: str = Field(..., description="Content format (markdown, mermaid, latex, dot, etc.)")
    description: str | None = Field(None, description="Description of the visualization")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "type": "table",
                "title": "Comparison of Transformer Architectures",
                "content": (
                    "| Model | Parameters | Year |\n"
                    "|-------|------------|------|\n"
                    "| BERT | 340M | 2018 |\n"
                    "| GPT-3 | 175B | 2020 |"
                ),
                "format": "markdown",
                "description": (
                    "Comparison of key transformer models by parameter count " "and release year"
                ),
            }
        }

    def to_markdown(self) -> str:
        """Render visualization in Markdown format.

        Returns:
            Markdown-formatted visualization
        """
        md_parts = [f"### {self.title}\n"]

        if self.description:
            md_parts.append(f"*{self.description}*\n")

        if self.format == "markdown":
            md_parts.append(self.content)
        elif self.format == "mermaid":
            md_parts.append(f"```mermaid\n{self.content}\n```")
        elif self.format == "latex":
            md_parts.append(f"```latex\n{self.content}\n```")
        elif self.format == "dot":
            md_parts.append(f"```dot\n{self.content}\n```")
        else:
            md_parts.append(f"```\n{self.content}\n```")

        return "\n".join(md_parts)
