"""Tests for Semantic Scholar client configuration."""

from unittest.mock import patch

from src.scientific_articles_engine.services.semantic_scholar_service import (
    SemanticScholarService,
)


def test_service_uses_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "test-key")

    with patch(
        "src.scientific_articles_engine.services.semantic_scholar_service.SemanticScholar"
    ) as client:
        SemanticScholarService({"timeout": 12})

    client.assert_called_once_with(timeout=12, api_key="test-key", retry=False)


def test_service_allows_missing_optional_api_key(monkeypatch):
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)

    with patch(
        "src.scientific_articles_engine.services.semantic_scholar_service.SemanticScholar"
    ) as client:
        SemanticScholarService({"timeout": 12})

    client.assert_called_once_with(timeout=12, api_key=None, retry=False)