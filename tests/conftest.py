"""Pytest configuration and fixtures for testing."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.scientific_articles_engine.config import AgentConfig, DatabaseConfig, EngineConfig, LLMConfig
from src.scientific_articles_engine.models.article import Article, ArticleSection
from src.scientific_articles_engine.models.paper import Paper, PaperAuthor
from src.scientific_articles_engine.models.review import ReviewCriteria, ReviewResult

@pytest.fixture
def test_config():
    """Create a test configuration."""
    return EngineConfig(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test_api_key",
            temperature=0.7,
            max_tokens=4000,
        ),
        agents=AgentConfig(
            max_papers_per_source=5,
            search_timeout=10,
            min_word_count=500,
            max_word_count=2000,
            style_guide="academic",
            quality_threshold=7.0,
            max_revisions=3,
            max_visualizations=3,
            supported_types=["table", "diagram"],
        ),
        database=DatabaseConfig(
            enabled=False,  # Disable for tests
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
        ),
    )


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = AsyncMock()
    service.generate = AsyncMock(return_value="Generated text response")
    service.generate_with_structure = AsyncMock(
        return_value={
            "criteria_scores": [
                {"criterion": "Scientific Rigor", "score": 8, "feedback": "Good rigor"},
                {"criterion": "Citation Quality", "score": 7, "feedback": "Adequate citations"},
                {"criterion": "Coherence", "score": 9, "feedback": "Well organized"},
                {"criterion": "Writing Quality", "score": 8, "feedback": "Clear writing"},
            ],
            "summary": "Good article overall",
            "suggestions": ["Add more recent references"],
            "strengths": ["Clear structure", "Good explanations"],
        }
    )
    return service


@pytest.fixture
def sample_papers():
    """Create sample papers for testing."""
    return [
        Paper(
            title="Attention Is All You Need",
            authors=[
                PaperAuthor(name="Ashish Vaswani", affiliation="Google Brain"),
                PaperAuthor(name="Noam Shazeer", affiliation="Google Brain"),
            ],
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            url="https://arxiv.org/abs/1706.03762",
            pdf_url="https://arxiv.org/pdf/1706.03762.pdf",
            published_date=None,
            source="arxiv",
            paper_id="1706.03762",
            citations_count=50000,
            venue="NeurIPS 2017",
        ),
        Paper(
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors=[
                PaperAuthor(name="Jacob Devlin", affiliation="Google AI"),
            ],
            abstract="We introduce a new language representation model called BERT.",
            url="https://arxiv.org/abs/1810.04805",
            pdf_url="https://arxiv.org/pdf/1810.04805.pdf",
            published_date=None,
            source="arxiv",
            paper_id="1810.04805",
            citations_count=30000,
            venue="NAACL 2019",
        ),
    ]


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        title="Understanding Transformer Architectures",
        abstract="This article explores the transformer architecture and its applications.",
        sections=[
            ArticleSection(
                title="Introduction",
                content="Transformers have revolutionized natural language processing...",
                subsections=[],
            ),
            ArticleSection(
                title="Background",
                content="The original transformer model was introduced in 2017...",
                subsections=[],
            ),
            ArticleSection(
                title="Conclusion",
                content="In conclusion, transformers represent a significant advancement...",
                subsections=[],
            ),
        ],
        references=[
            "Vaswani et al. (2017). Attention Is All You Need.",
            "Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers.",
        ],
        word_count=1500,
        version=1,
    )


@pytest.fixture
def sample_review():
    """Create a sample review for testing."""
    return ReviewResult(
        criteria_scores=[
            ReviewCriteria(
                criterion="Scientific Rigor",
                score=8,
                feedback="Strong scientific foundation",
            ),
            ReviewCriteria(
                criterion="Citation Quality",
                score=7,
                feedback="Good citations but could be more comprehensive",
            ),
            ReviewCriteria(
                criterion="Coherence",
                score=9,
                feedback="Excellent logical flow",
            ),
            ReviewCriteria(
                criterion="Writing Quality",
                score=8,
                feedback="Clear and professional writing",
            ),
        ],
        overall_score=8.0,
        passed=True,
        summary="This is a well-written article with strong foundations.",
        suggestions=["Add more recent citations", "Expand the related work section"],
        strengths=["Clear structure", "Comprehensive coverage"],
    )


@pytest.fixture
def mock_arxiv_service():
    """Create a mock arXiv service."""
    service = AsyncMock()
    service.search = AsyncMock(return_value=[])
    service.get_service_name = MagicMock(return_value="arxiv")
    return service


@pytest.fixture
def mock_semantic_scholar_service():
    """Create a mock Semantic Scholar service."""
    service = AsyncMock()
    service.search = AsyncMock(return_value=[])
    service.get_service_name = MagicMock(return_value="semantic_scholar")
    return service
