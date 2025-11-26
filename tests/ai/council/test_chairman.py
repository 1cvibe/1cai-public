"""
Tests for Chairman
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.ai.council.chairman import Chairman, SynthesisResult
from src.ai.council.peer_review import ReviewResult


@pytest.fixture
def mock_orchestrator():
    """Mock AI orchestrator"""
    orchestrator = MagicMock()
    orchestrator._get_provider = MagicMock()
    return orchestrator


@pytest.fixture
def chairman(mock_orchestrator):
    """Chairman instance"""
    return Chairman(mock_orchestrator, "kimi")


@pytest.mark.asyncio
async def test_synthesize_success(chairman, mock_orchestrator):
    """Test successful synthesis"""
    # Mock provider
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(return_value="Final synthesized answer")
    mock_orchestrator._get_provider.return_value = mock_provider

    # Test data
    responses = [
        {"model": "kimi", "response": "Response 1"},
        {"model": "qwen", "response": "Response 2"},
    ]
    reviews = [
        ReviewResult("kimi", [1, 2], "test", 0.9),
        ReviewResult("qwen", [2, 1], "test", 0.9),
    ]

    # Execute
    result = await chairman.synthesize(query="Test query", responses=responses, reviews=reviews, context={})

    # Verify
    assert isinstance(result, SynthesisResult)
    assert result.final_response == "Final synthesized answer"
    assert result.confidence > 0


def test_create_synthesis_prompt(chairman):
    """Test synthesis prompt creation"""
    responses = [
        {"model": "kimi", "response": "Response 1"},
        {"model": "qwen", "response": "Response 2"},
    ]
    reviews = [
        ReviewResult("kimi", [1, 2], "test", 0.9),
    ]

    prompt = chairman._create_synthesis_prompt(query="Test query", responses=responses, reviews=reviews)

    assert "Test query" in prompt
    assert "Response 1" in prompt
    assert "Response 2" in prompt
    assert "Chairman" in prompt


def test_fallback_synthesis_with_reviews(chairman, mock_orchestrator):
    """Test fallback synthesis with reviews"""
    responses = [
        {"model": "kimi", "response": "Best response"},
        {"model": "qwen", "response": "Second response"},
    ]
    reviews = [
        ReviewResult("kimi", [1, 2], "test", 1.0),
        ReviewResult("qwen", [1, 2], "test", 1.0),
    ]

    result = chairman._fallback_synthesis(responses, reviews)

    assert isinstance(result, SynthesisResult)
    assert result.final_response == "Best response"
    assert result.confidence == 0.6


def test_fallback_synthesis_without_reviews(chairman, mock_orchestrator):
    """Test fallback synthesis without reviews"""
    responses = [
        {"model": "kimi", "response": "First response"},
    ]
    reviews = []

    result = chairman._fallback_synthesis(responses, reviews)

    assert isinstance(result, SynthesisResult)
    assert result.final_response == "First response"
    assert result.confidence == 0.5
