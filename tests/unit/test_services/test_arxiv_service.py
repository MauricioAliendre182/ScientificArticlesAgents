"""Tests for arXiv client request configuration."""

from unittest.mock import patch

from src.scientific_articles_engine.services.arxiv_service import ArxivService


def test_arxiv_client_uses_configured_page_size():
    with patch("src.scientific_articles_engine.services.arxiv_service.arxiv.Client") as client:
        ArxivService({"max_results": 7, "timeout": 20})

    client.assert_called_once_with(
        page_size=7,
        delay_seconds=3.0,
        num_retries=3,
    )