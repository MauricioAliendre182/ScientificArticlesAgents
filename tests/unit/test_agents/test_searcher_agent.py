"""Unit tests for SearcherAgent paper-source fallback behavior."""

from unittest.mock import AsyncMock

import pytest

from src.scientific_articles_engine.agents.searcher_agent import SearcherAgent
from src.scientific_articles_engine.core.exceptions import AgentExecutionError


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_source", ["arxiv", "semantic_scholar"])
async def test_searcher_continues_when_one_source_fails(
    failed_source,
    mock_arxiv_service,
    mock_llm_service,
    mock_semantic_scholar_service,
    sample_papers,
):
    arxiv_service = mock_arxiv_service
    semantic_scholar_service = mock_semantic_scholar_service

    failed_service = (
        arxiv_service if failed_source == "arxiv" else semantic_scholar_service
    )
    successful_service = (
        semantic_scholar_service if failed_source == "arxiv" else arxiv_service
    )
    failed_service.search.side_effect = ConnectionError("service unavailable")
    successful_service.search.return_value = sample_papers

    agent = SearcherAgent(
        llm_service=mock_llm_service,
        arxiv_service=arxiv_service,
        semantic_scholar_service=semantic_scholar_service,
        config={"max_papers_per_source": 5},
    )

    papers, outline = await agent.execute({"topic": "Transformer architectures"})

    assert papers == sample_papers
    assert outline == "Generated text response"
    mock_llm_service.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_searcher_fails_clearly_when_both_sources_fail(
    mock_arxiv_service,
    mock_llm_service,
    mock_semantic_scholar_service,
):
    mock_arxiv_service.search.side_effect = ConnectionError("arXiv unavailable")
    mock_semantic_scholar_service.search.side_effect = ConnectionError(
        "Semantic Scholar unavailable"
    )
    agent = SearcherAgent(
        llm_service=mock_llm_service,
        arxiv_service=mock_arxiv_service,
        semantic_scholar_service=mock_semantic_scholar_service,
        config={"max_papers_per_source": 5},
    )

    with pytest.raises(AgentExecutionError) as error:
        await agent.execute({"topic": "Transformer architectures"})

    assert "Live searches produced no papers" in str(error.value)
    assert "Provider errors" in str(error.value)
    assert "arXiv unavailable" in str(error.value)
    assert "Semantic Scholar unavailable" in str(error.value)
    mock_llm_service.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_searcher_uses_cache_when_both_sources_fail(
    mock_arxiv_service,
    mock_llm_service,
    mock_semantic_scholar_service,
    sample_papers,
):
    mock_arxiv_service.search.side_effect = ConnectionError("arXiv unavailable")
    mock_semantic_scholar_service.search.side_effect = ConnectionError(
        "Semantic Scholar unavailable"
    )
    cache = AsyncMock()
    cache.get.return_value = sample_papers
    agent = SearcherAgent(
        llm_service=mock_llm_service,
        arxiv_service=mock_arxiv_service,
        semantic_scholar_service=mock_semantic_scholar_service,
        config={"max_papers_per_source": 5},
        paper_cache=cache,
    )

    papers, _ = await agent.execute({"topic": "Transformer architectures"})

    assert papers == sample_papers
    cache.get.assert_awaited_once_with("Transformer architectures")
    mock_llm_service.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_searcher_supplements_partial_live_results_from_cache(
    mock_arxiv_service,
    mock_llm_service,
    mock_semantic_scholar_service,
    sample_papers,
):
    mock_arxiv_service.search.return_value = sample_papers[:1]
    mock_semantic_scholar_service.search.side_effect = ConnectionError(
        "Semantic Scholar unavailable"
    )
    cache = AsyncMock()
    cache.get.return_value = sample_papers
    agent = SearcherAgent(
        llm_service=mock_llm_service,
        arxiv_service=mock_arxiv_service,
        semantic_scholar_service=mock_semantic_scholar_service,
        config={"max_papers_per_source": 5},
        paper_cache=cache,
    )

    papers, _ = await agent.execute({"topic": "Transformer architectures"})

    assert papers == sample_papers
    cache.put.assert_awaited_once_with("Transformer architectures", sample_papers)


@pytest.mark.asyncio
async def test_searcher_continues_when_cache_is_unavailable(
    mock_arxiv_service,
    mock_llm_service,
    mock_semantic_scholar_service,
    sample_papers,
):
    mock_arxiv_service.search.return_value = sample_papers
    mock_semantic_scholar_service.search.return_value = []
    cache = AsyncMock()
    cache.put.side_effect = ConnectionError("database unavailable")
    agent = SearcherAgent(
        llm_service=mock_llm_service,
        arxiv_service=mock_arxiv_service,
        semantic_scholar_service=mock_semantic_scholar_service,
        config={"max_papers_per_source": 5},
        paper_cache=cache,
    )

    papers, _ = await agent.execute({"topic": "Transformer architectures"})

    assert papers == sample_papers
    mock_llm_service.generate.assert_awaited_once()
