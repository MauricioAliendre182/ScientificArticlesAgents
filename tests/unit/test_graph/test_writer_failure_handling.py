"""Regression tests for failures in the writing and review workflow."""

from unittest.mock import AsyncMock

import pytest

from src.scientific_articles_engine.graph.edges import route_after_reviewer
from src.scientific_articles_engine.graph.nodes import reviewer_node, writer_node


@pytest.mark.asyncio
async def test_writer_node_reports_missing_article():
    writer = AsyncMock()
    writer.execute.return_value = None

    result = await writer_node({}, writer)

    assert result["error_message"] == "WriterAgent returned no article"


@pytest.mark.asyncio
async def test_reviewer_preserves_prior_workflow_error():
    reviewer = AsyncMock()
    state = {"error_message": "WriterAgent failed"}

    result = await reviewer_node(state, reviewer)

    assert result["error_message"] == "WriterAgent failed"
    reviewer.execute.assert_not_awaited()


def test_reviewer_route_ends_after_workflow_error():
    state = {"error_message": "WriterAgent failed", "revision_count": 0}

    assert route_after_reviewer(state) == "__end__"