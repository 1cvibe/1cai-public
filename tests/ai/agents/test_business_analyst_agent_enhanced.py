"""
Unit tests for Business Analyst Agent Enhanced

Tests cover:
- Requirements analysis
- Acceptance criteria generation
- BPMN generation
- Requirements traceability stub
"""

import pytest
from unittest.mock import AsyncMock
from src.ai.agents.business_analyst_agent_enhanced import BusinessAnalystAgentEnhanced


@pytest.fixture
def ba_agent():
    """Create BA Agent instance"""
    return BusinessAnalystAgentEnhanced()


@pytest.fixture
def mock_llm():
    """Mock LLM Selector"""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={
        "response": '{"functional": [], "non_functional": []}',
        "model": "qwen-test"
    })
    return mock


class TestRequirementsAnalysis:
    """Test requirements analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_requirements(self, ba_agent, mock_llm):
        """Test requirements analysis"""
        ba_agent.llm_selector = mock_llm
        
        result = await ba_agent.analyze_requirements(
            requirements_text="Система должна поддерживать продажи"
        )
        
        assert result["status"] == "completed"
        assert "analysis" in result
    
    @pytest.mark.asyncio
    async def test_analyze_requirements_no_llm(self, ba_agent):
        """Test analysis without LLM"""
        ba_agent.llm_selector = None
        
        result = await ba_agent.analyze_requirements(
            requirements_text="Test"
        )
        
        assert result["status"] == "llm_not_available"


class TestAcceptanceCriteria:
    """Test acceptance criteria generation"""
    
    @pytest.mark.asyncio
    async def test_generate_acceptance_criteria(self, ba_agent, mock_llm):
        """Test criteria generation"""
        mock_llm.generate.return_value = {
            "response": "Дано условие\nКогда действие\nТогда результат",
            "model": "qwen-test"
        }
        ba_agent.llm_selector = mock_llm
        
        result = await ba_agent.generate_acceptance_criteria(
            user_story="Как пользователь я хочу создать заказ"
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_criteria_no_llm(self, ba_agent):
        """Test criteria without LLM"""
        ba_agent.llm_selector = None
        
        result = await ba_agent.generate_acceptance_criteria(
            user_story="Test story"
        )
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestBPMNGeneration:
    """Test BPMN generation"""
    
    @pytest.mark.asyncio
    async def test_generate_bpmn(self, ba_agent, mock_llm):
        """Test BPMN generation"""
        mock_llm.generate.return_value = {
            "response": "<bpmn>test</bpmn>",
            "model": "qwen-test"
        }
        ba_agent.llm_selector = mock_llm
        
        result = await ba_agent.generate_bpmn(
            process_description="Процесс продажи товара"
        )
        
        assert result["status"] == "generated"
        assert "bpmn_xml" in result


class TestRequirementsTraceability:
    """Test requirements traceability"""
    
    @pytest.mark.asyncio
    async def test_trace_requirements_stub(self, ba_agent):
        """Test traceability stub"""
        result = await ba_agent.trace_requirements(
            requirement_id="REQ-001"
        )
        
        assert result["status"] == "change_graph_not_available"
        assert result["requirement_id"] == "REQ-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
