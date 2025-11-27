"""
Unit tests for Architect Agent Enhanced

Tests cover:
- Architecture analysis
- C4 diagram generation
- Technical debt analysis
- Pattern suggestions
- Impact analysis stub
"""

import pytest
from unittest.mock import AsyncMock
from src.ai.agents.architect_agent_enhanced import ArchitectAgentEnhanced


@pytest.fixture
def architect_agent():
    """Create Architect Agent instance"""
    return ArchitectAgentEnhanced()


@pytest.fixture
def mock_llm():
    """Mock LLM Selector"""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={
        "response": '{"analysis": "Good architecture", "issues": [], "recommendations": []}',
        "model": "qwen-test"
    })
    return mock


class TestArchitectureAnalysis:
    """Test architecture analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_architecture_with_llm(self, architect_agent, mock_llm):
        """Test architecture analysis with LLM"""
        architect_agent.llm_selector = mock_llm
        
        result = await architect_agent.analyze_architecture(
            system_description="1С система управления продажами"
        )
        
        assert result["status"] == "completed"
        assert "analysis" in result
        mock_llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_architecture_no_llm(self, architect_agent):
        """Test analysis without LLM"""
        architect_agent.llm_selector = None
        
        result = await architect_agent.analyze_architecture(
            system_description="Test system"
        )
        
        assert result["status"] == "llm_not_available"


class TestC4DiagramGeneration:
    """Test C4 diagram generation"""
    
    @pytest.mark.asyncio
    async def test_generate_c4_diagram_context(self, architect_agent, mock_llm):
        """Test C4 context diagram"""
        mock_llm.generate.return_value = {
            "response": "@startuml\nSystem(sys, \"Test\")\n@enduml",
            "model": "qwen-test"
        }
        architect_agent.llm_selector = mock_llm
        
        result = await architect_agent.generate_c4_diagram(
            system_description="Test system",
            level="context"
        )
        
        assert result["status"] == "generated"
        assert result["level"] == "context"
        assert result["format"] == "plantuml"
        assert "diagram" in result
    
    @pytest.mark.asyncio
    async def test_generate_c4_diagram_no_llm(self, architect_agent):
        """Test C4 generation without LLM"""
        architect_agent.llm_selector = None
        
        result = await architect_agent.generate_c4_diagram(
            system_description="Test",
            level="container"
        )
        
        assert result["status"] == "llm_not_available"


class TestTechnicalDebtAnalysis:
    """Test technical debt analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_technical_debt(self, architect_agent, mock_llm):
        """Test debt analysis"""
        architect_agent.llm_selector = mock_llm
        
        result = await architect_agent.analyze_technical_debt(
            codebase_path="/path/to/code"
        )
        
        assert result["status"] == "completed"
        assert "debt_analysis" in result
    
    @pytest.mark.asyncio
    async def test_analyze_debt_no_llm(self, architect_agent):
        """Test debt analysis without LLM"""
        architect_agent.llm_selector = None
        
        result = await architect_agent.analyze_technical_debt(
            codebase_path="/test"
        )
        
        assert result["status"] == "llm_not_available"


class TestPatternSuggestions:
    """Test pattern suggestions"""
    
    @pytest.mark.asyncio
    async def test_suggest_patterns(self, architect_agent, mock_llm):
        """Test pattern suggestions"""
        architect_agent.llm_selector = mock_llm
        
        result = await architect_agent.suggest_patterns(
            problem_description="Нужна интеграция с внешней системой"
        )
        
        assert result["status"] == "completed"
        assert "patterns" in result


class TestImpactAnalysis:
    """Test impact analysis"""
    
    @pytest.mark.asyncio
    async def test_analyze_impact_stub(self, architect_agent):
        """Test impact analysis stub"""
        result = await architect_agent.analyze_impact(
            change_description="Изменение модуля продаж"
        )
        
        assert result["status"] == "change_graph_not_available"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
