"""Unit tests for WriterAgent."""

import pytest

from src.scientific_articles_engine.agents.writer_agent import WriterAgent
from src.scientific_articles_engine.core.state import AgentState


@pytest.mark.asyncio
async def test_writer_creates_draft(mock_llm_service, sample_papers):
    """Test that WriterAgent creates an initial draft."""
    # Arrange
    config = {"min_word_count": 500, "max_word_count": 2000, "style_guide": "academic"}
    writer = WriterAgent(llm_service=mock_llm_service, config=config)

    state = AgentState(
        topic="Transformer Architectures",
        papers=sample_papers,
        outline="## Introduction\n## Background\n## Conclusion",
        article=None,
        review=None,
        visualizations=[],
        revision_count=0,
        quality_passed=False,
        searcher_approved=True,
        final_approved=False,
        error_message=None,
        messages=[],
    )

    # Mock LLM response
    mock_llm_service.generate.return_value = """# Transformer Architectures

This is an abstract about transformers.

## Introduction
Transformers have revolutionized NLP.

## Background
The original transformer was introduced in 2017.

## Conclusion
Transformers are important."""

    # Act
    article = await writer.execute(state)

    # Assert
    assert article is not None
    assert article.title == "Transformer Architectures"
    assert article.version == 1
    assert len(article.sections) > 0
    assert article.word_count > 0
    mock_llm_service.generate.assert_called_once()


@pytest.mark.asyncio
async def test_writer_revises_article(mock_llm_service, sample_article, sample_review):
    """Test that WriterAgent revises an article based on feedback."""
    # Arrange
    config = {"min_word_count": 500, "max_word_count": 2000, "style_guide": "academic"}
    writer = WriterAgent(llm_service=mock_llm_service, config=config)

    # Create review with needs_revision = True
    failing_review = sample_review
    failing_review.passed = False

    state = AgentState(
        topic="Transformer Architectures",
        papers=[],
        outline="",
        article=sample_article,
        review=failing_review,
        visualizations=[],
        revision_count=1,
        quality_passed=False,
        searcher_approved=True,
        final_approved=False,
        error_message=None,
        messages=[],
    )

    mock_llm_service.generate.return_value = """# Understanding Transformer Architectures (Revised)

Revised abstract.

## Introduction
Revised introduction.

## Conclusion
Revised conclusion."""

    # Act
    revised_article = await writer.execute(state)

    # Assert
    assert revised_article is not None
    assert revised_article.version == 2  # Version incremented
    assert revised_article.revision_notes is not None
    mock_llm_service.generate.assert_called_once()


def test_writer_parse_sections():
    """Test article section parsing."""
    # Arrange
    config = {"min_word_count": 500, "max_word_count": 2000, "style_guide": "academic"}
    writer = WriterAgent(llm_service=None, config=config)

    article_text = """# Test Article

## Introduction
This is the introduction.

## Methods
This is the methods section.

## Conclusion
This is the conclusion."""

    # Act
    sections = writer._parse_sections(article_text)

    # Assert
    assert len(sections) == 3
    assert sections[0].title == "Introduction"
    assert sections[1].title == "Methods"
    assert sections[2].title == "Conclusion"
    assert "introduction" in sections[0].content.lower()
