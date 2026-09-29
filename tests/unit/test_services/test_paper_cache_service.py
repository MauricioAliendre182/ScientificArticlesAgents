"""Tests for the persistent paper search cache."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from psycopg.types.json import Jsonb

from src.scientific_articles_engine.services.paper_cache_service import PaperCacheService


def make_cache() -> PaperCacheService:
    return PaperCacheService(
        {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_password",
        }
    )


def test_paper_cache_normalizes_case_and_whitespace():
    assert PaperCacheService.normalize_query("  Transformer   Architectures\n NLP ") == (
        "transformer architectures nlp"
    )


@pytest.mark.asyncio
async def test_cache_get_reconstructs_paper_models(monkeypatch, sample_papers):
    cursor = SimpleNamespace(
        fetchone=AsyncMock(
            return_value=([paper.model_dump(mode="json") for paper in sample_papers],)
        )
    )
    connection = SimpleNamespace(
        execute=AsyncMock(return_value=cursor),
        close=AsyncMock(),
    )
    connect = AsyncMock(return_value=connection)
    monkeypatch.setattr(
        "src.scientific_articles_engine.services.paper_cache_service.AsyncConnection.connect",
        connect,
    )

    papers = await make_cache().get(" Transformer   Architectures ")

    assert papers == sample_papers
    assert type(papers[0]) is type(sample_papers[0])
    assert connection.execute.await_count == 2
    assert "SELECT papers" in connection.execute.await_args_list[1].args[0]
    assert connection.execute.await_args_list[1].args[1][1] == 30
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_cache_put_persists_jsonb_paper_data(monkeypatch, sample_papers):
    connection = SimpleNamespace(execute=AsyncMock(), close=AsyncMock())
    connect = AsyncMock(return_value=connection)
    monkeypatch.setattr(
        "src.scientific_articles_engine.services.paper_cache_service.AsyncConnection.connect",
        connect,
    )

    await make_cache().put("Transformer Architectures", sample_papers)

    sql, parameters = connection.execute.await_args_list[1].args
    assert "ON CONFLICT (query_key) DO UPDATE" in sql
    assert parameters[1] == "transformer architectures"
    assert isinstance(parameters[2], Jsonb)
    assert parameters[2].obj == [paper.model_dump(mode="json") for paper in sample_papers]
    connection.close.assert_awaited_once()
