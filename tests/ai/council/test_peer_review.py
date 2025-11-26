"""
Tests for Peer Review
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.ai.council.peer_review import PeerReview, ReviewResult


@pytest.fixture
def mock_orchestrator():
    """Mock AI orchestrator"""
    orchestrator = MagicMock()
    orchestrator._get_provider = MagicMock()
    return orchestrator


@pytest.fixture
def peer_review(mock_orchestrator):
    """Peer review instance"""
    return PeerReview(mock_orchestrator)


@pytest.mark.asyncio
async def test_conduct_peer_review(peer_review, mock_orchestrator):
    """Test peer review process"""
    # Mock provider
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(return_value="Rankings: [1, 2, 3]\nGood responses")
    mock_orchestrator._get_provider.return_value = mock_provider

    # Test data
    responses = [
        {"model": "kimi", "response": "Response 1"},
        {"model": "qwen", "response": "Response 2"},
        {"model": "gigachat", "response": "Response 3"},
    ]

    # Execute
    reviews = await peer_review.conduct_peer_review(query="Test query", responses=responses, context={})

    # Verify
    assert len(reviews) == 3
    assert all(isinstance(r, ReviewResult) for r in reviews)


def test_anonymize_responses(peer_review):
    """Test response anonymization"""
    responses = [
        {"model": "kimi", "response": "Response 1"},
        {"model": "qwen", "response": "Response 2"},
    ]

    anonymized = peer_review._anonymize_responses(responses)

    assert len(anonymized) == 2
    assert all("label" in r for r in anonymized)
    assert all("Response" in r["label"] for r in anonymized)
    assert all("original_index" in r for r in anonymized)


def test_create_review_prompt(peer_review):
    """Test review prompt creation"""
    responses = [
        {"label": "Response A", "response": "Test 1"},
        {"label": "Response B", "response": "Test 2"},
    ]

    prompt = peer_review._create_review_prompt(query="Test query", responses=responses)

    assert "Test query" in prompt
    assert "Response A" in prompt
    assert "Response B" in prompt
    assert "Rankings:" in prompt


def test_parse_review_response_success(peer_review):
    """Test parsing valid review response"""
    review_text = """
    Rankings: [1, 2, 3]
    
    Response 1 is best because...
    """

    rankings, reasoning = peer_review._parse_review_response(review_text, 3)

    assert rankings == [1, 2, 3]
    assert "Rankings" in reasoning


def test_parse_review_response_fallback(peer_review):
    """Test parsing invalid review response (fallback)"""
    review_text = "Invalid response without rankings"

    rankings, reasoning = peer_review._parse_review_response(review_text, 3)

    # Should return default rankings
    assert rankings == [1, 2, 3]


def test_aggregate_rankings(peer_review):
    """Test ranking aggregation"""
    reviews = [
        ReviewResult("kimi", [1, 2, 3], "test", 1.0),
        ReviewResult("qwen", [2, 1, 3], "test", 1.0),
        ReviewResult("gigachat", [1, 3, 2], "test", 1.0),
    ]

    avg_rankings = peer_review.aggregate_rankings(reviews, 3)

    assert len(avg_rankings) == 3
    assert all(isinstance(r, float) for r in avg_rankings)
    # First response should have best average (lowest number)
    assert avg_rankings[0] < avg_rankings[2]
