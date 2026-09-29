"""Pydantic models for article reviews."""


from pydantic import BaseModel, Field


class ReviewCriteria(BaseModel):
    """Individual review criterion with score and feedback.

    Attributes:
        criterion: Name of the criterion (e.g., "rigor", "coherence")
        score: Score from 1-10
        feedback: Detailed feedback for this criterion
    """

    criterion: str = Field(..., description="Criterion name")
    score: int = Field(..., ge=1, le=10, description="Score from 1 to 10")
    feedback: str = Field(..., description="Detailed feedback")


class ReviewResult(BaseModel):
    """Complete review result from the reviewer agent.

    Contains scores across multiple criteria and overall assessment.

    Attributes:
        criteria_scores: List of individual criterion evaluations
        overall_score: Average score across all criteria
        passed: Whether the article meets quality threshold
        summary: Overall review summary
        suggestions: Specific suggestions for improvement
        strengths: Identified strengths of the article
    """

    criteria_scores: list[ReviewCriteria] = Field(
        ..., description="Scores for each criterion"
    )
    overall_score: float = Field(..., ge=1.0, le=10.0, description="Overall average score")
    passed: bool = Field(..., description="Whether quality threshold was met")
    summary: str = Field(..., description="Overall review summary")
    suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )
    strengths: list[str] = Field(default_factory=list, description="Article strengths")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "criteria_scores": [
                    {
                        "criterion": "Scientific Rigor",
                        "score": 8,
                        "feedback": "The article demonstrates strong scientific rigor...",
                    },
                    {
                        "criterion": "Citation Quality",
                        "score": 7,
                        "feedback": "Citations are relevant but could be more comprehensive...",
                    },
                    {
                        "criterion": "Coherence",
                        "score": 9,
                        "feedback": "The article flows logically from introduction to conclusion...",  # noqa: E501
                    },
                    {
                        "criterion": "Writing Quality",
                        "score": 8,
                        "feedback": "Well-written with clear explanations...",
                    },
                ],
                "overall_score": 8.0,
                "passed": True,
                "summary": "This is a well-written article with strong scientific foundations...",
                "suggestions": [
                    "Expand the related work section",
                    "Add more recent citations from 2023-2024",
                ],
                "strengths": [
                    "Clear and logical structure",
                    "Comprehensive coverage of transformer architectures",
                ],
            }
        }

    @property
    def needs_revision(self) -> bool:
        """Check if the article needs revision.

        Returns:
            True if the article did not pass review
        """
        return not self.passed

    def get_feedback_for_revision(self) -> str:
        """Generate formatted feedback for the writer agent.

        Returns:
            Formatted feedback string with all suggestions
        """
        feedback_parts = [f"**Overall Score**: {self.overall_score}/10\n"]
        feedback_parts.append(f"**Status**: {'PASSED' if self.passed else 'NEEDS REVISION'}\n")
        feedback_parts.append(f"\n**Summary**: {self.summary}\n")

        if self.suggestions:
            feedback_parts.append("\n**Suggestions for Improvement**:")
            for i, suggestion in enumerate(self.suggestions, 1):
                feedback_parts.append(f"{i}. {suggestion}")

        feedback_parts.append("\n**Detailed Scores**:")
        for criterion in self.criteria_scores:
            feedback_parts.append(
                f"- **{criterion.criterion}**: {criterion.score}/10 - {criterion.feedback}"
            )

        return "\n".join(feedback_parts)
