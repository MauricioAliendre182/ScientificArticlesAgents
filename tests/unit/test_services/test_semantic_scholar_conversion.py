"""Tests for converting Semantic Scholar SDK model results."""

from types import SimpleNamespace

from src.scientific_articles_engine.services.semantic_scholar_service import (
    SemanticScholarService,
)


def test_convert_paper_with_sdk_author_objects():
    service = SemanticScholarService.__new__(SemanticScholarService)
    result = SimpleNamespace(
        title="Transformer paper",
        paperId="paper-123",
        abstract="A study of transformer models.",
        authors=[SimpleNamespace(name="Ada Lovelace")],
        externalIds={},
        year=2024,
        openAccessPdf=None,
        citationCount=12,
        venue="NLP Conference",
    )

    paper = service._convert_to_paper(result)

    assert paper is not None
    assert paper.paper_id == "paper-123"
    assert [author.name for author in paper.authors] == ["Ada Lovelace"]
    assert paper.citations_count == 12


def test_convert_paper_treats_empty_open_access_url_as_missing():
    service = SemanticScholarService.__new__(SemanticScholarService)
    result = SimpleNamespace(
        title="Transformer paper",
        paperId="paper-456",
        abstract="A study of transformer models.",
        authors=[SimpleNamespace(name="Ada Lovelace")],
        externalIds={},
        year=2024,
        openAccessPdf=SimpleNamespace(url=""),
        citationCount=0,
        venue=None,
    )

    paper = service._convert_to_paper(result)

    assert paper is not None
    assert paper.pdf_url is None
