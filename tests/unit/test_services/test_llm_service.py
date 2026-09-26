"""Unit tests for LLMService."""

import pytest
from unittest.mock import AsyncMock, patch

from src.scientific_articles_engine.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_initialization():
    """Test LLM service initialization."""
    # Arrange
    config = {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "test_key",
        "temperature": 0.7,
    }

    # Act
    with patch("scientific_articles_engine.services.llm_service.ChatOpenAI"):
        service = LLMService(config)

    # Assert
    assert service.provider == "openai"
    assert service.model == "gpt-4"


@pytest.mark.asyncio
async def test_llm_service_generate():
    """Test text generation."""
    # Arrange
    config = {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "test_key",
    }

    with patch("scientific_articles_engine.services.llm_service.ChatOpenAI"):
        service = LLMService(config)

    service.llm = AsyncMock()
    # Mock the LLM response
    mock_response = AsyncMock()
    mock_response.content = "Generated text"
    service.llm.ainvoke = AsyncMock(return_value=mock_response)

    # Act
    result = await service.generate("Test prompt")

    # Assert
    assert result == "Generated text"
    service.llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_llm_service_structured_output():
    """Test structured output generation."""
    # Arrange
    config = {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "test_key",
    }

    with patch("scientific_articles_engine.services.llm_service.ChatOpenAI"):
        service = LLMService(config)

    service.llm = AsyncMock()
    # Mock the LLM response with JSON
    mock_response = AsyncMock()
    mock_response.content = '{"result": "success", "score": 10}'
    service.llm.ainvoke = AsyncMock(return_value=mock_response)

    schema = {"type": "object", "properties": {"result": {"type": "string"}}}

    # Act
    result = await service.generate_with_structure("Test prompt", schema)

    # Assert
    assert result == {"result": "success", "score": 10}
    service.llm.ainvoke.assert_called_once()
