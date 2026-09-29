"""Pydantic models for academic papers."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class PaperAuthor(BaseModel):
    """Author of an academic paper.

    Attributes:
        name: Full name of the author
        affiliation: Institution or organization affiliation
    """

    name: str = Field(..., description="Author's full name")
    affiliation: str | None = Field(None, description="Author's affiliation")


class Paper(BaseModel):
    """Academic paper metadata.

    Represents a scientific paper from sources like arXiv or Semantic Scholar.

    Attributes:
        title: Paper title
        authors: List of paper authors
        abstract: Paper abstract
        url: URL to the paper
        pdf_url: Direct URL to PDF if available
        published_date: Publication date
        source: Source database (arxiv, semantic_scholar, etc.)
        paper_id: Unique identifier from the source
        citations_count: Number of citations (if available)
        venue: Publication venue (journal/conference)
    """

    title: str = Field(..., description="Title of the paper")
    authors: list[PaperAuthor] = Field(default_factory=list, description="List of authors")
    abstract: str = Field(..., description="Paper abstract")
    url: HttpUrl = Field(..., description="URL to the paper")
    pdf_url: HttpUrl | None = Field(None, description="Direct PDF URL")
    published_date: datetime | None = Field(None, description="Publication date")
    source: str = Field(..., description="Source database (arxiv, semantic_scholar)")
    paper_id: str = Field(..., description="Unique ID from source")
    citations_count: int | None = Field(None, description="Number of citations")
    venue: str | None = Field(None, description="Publication venue")

    # Define Config class for Pydantic model settings
    # It is to provide additional configuration for the Pydantic model, such as example data for JSON schema.
    # For example: Paper.Config.json_schema_extra provides example data for the JSON schema.
    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "title": "Attention Is All You Need",
                "authors": [
                    {"name": "Ashish Vaswani", "affiliation": "Google Brain"},
                    {"name": "Noam Shazeer", "affiliation": "Google Brain"},
                ],
                "abstract": "The dominant sequence transduction models...",
                "url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
                "published_date": "2017-06-12T00:00:00",
                "source": "arxiv",
                "paper_id": "1706.03762",
                "citations_count": 50000,
                "venue": "NeurIPS 2017",
            }
        }

    def to_citation(self) -> str:
        """Generate a citation string for this paper.

        Returns:
            Formatted citation string
        """
        author_names = ", ".join(author.name for author in self.authors[:3])
        if len(self.authors) > 3:
            author_names += " et al."

        year = self.published_date.year if self.published_date else "n.d."
        return f"{author_names} ({year}). {self.title}. {self.venue or 'Preprint'}."
