"""
Unit tests for QA Engineer Agent Enhanced

Tests cover:
- Vanessa BDD generation (LLM + fallback)
- CI/CD integration stub
- Smart test selection stub
- Self-healing tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.ai.agents.qa_engineer_agent_enhanced import QAEngineerAgentEnhanced


@pytest.fixture
def qa_agent():
    """Create QA Agent instance"""
    return QAEngineerAgentEnhanced()


@pytest.fixture
def mock_llm():
    """Mock LLM Selector"""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={
        "response": """# language: ru
Функционал: Тест
Сценарий: Проверка
  Дано условие
  Когда действие
  Тогда результат""",
        "model": "qwen-test"
    })
    return mock


class TestVanessaBDDGeneration:
    """Test Vanessa BDD generation"""
    
    @pytest.mark.asyncio
    async def test_generate_vanessa_tests_with_llm(self, qa_agent, mock_llm):
        """Test BDD generation with LLM"""
        qa_agent.llm_selector = mock_llm
        
        result = await qa_agent.generate_vanessa_tests(
            module_name="ПродажиСервер",
            functions=["СоздатьЗаказ", "РассчитатьСумму"],
            use_llm=True
        )
        
        assert "Функционал" in result
        assert "Сценарий" in result
        mock_llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_vanessa_tests_fallback(self, qa_agent):
        """Test BDD generation fallback"""
        qa_agent.llm_selector = None
        
        result = await qa_agent.generate_vanessa_tests(
            module_name="ТестМодуль",
            functions=["Функция1"],
            use_llm=True
        )
        
        assert "# language: ru" in result
        assert "ТестМодуль" in result
        assert "Функция1" in result
    
    @pytest.mark.asyncio
    async def test_generate_vanessa_tests_llm_error(self, qa_agent, mock_llm):
        """Test BDD generation with LLM error"""
        mock_llm.generate.side_effect = Exception("LLM Error")
        qa_agent.llm_selector = mock_llm
        
        result = await qa_agent.generate_vanessa_tests(
            module_name="Тест",
            functions=["Ф1"],
            use_llm=True
        )
        
        # Should fallback to template
        assert "# language: ru" in result


class TestCICDIntegration:
    """Test CI/CD integration"""
    
    @pytest.mark.asyncio
    async def test_trigger_ci_tests_stub(self, qa_agent):
        """Test CI/CD trigger stub"""
        result = await qa_agent.trigger_ci_tests(
            pipeline="test-pipeline",
            test_suite="smoke"
        )
        
        assert result["status"] == "ci_not_configured"
    
    @pytest.mark.asyncio
    async def test_trigger_ci_tests_configured(self, qa_agent):
        """Test CI/CD trigger when configured"""
        qa_agent.ci_client = MagicMock()
        
        result = await qa_agent.trigger_ci_tests(
            pipeline="test",
            test_suite="all"
        )
        
        assert "pipeline_id" in result


class TestSmartTestSelection:
    """Test smart test selection"""
    
    @pytest.mark.asyncio
    async def test_select_tests_for_change_stub(self, qa_agent):
        """Test smart selection stub"""
        result = await qa_agent.select_tests_for_change(
            changed_files=["module1.bsl", "module2.bsl"]
        )
        
        assert isinstance(result, list)
        assert len(result) == 0  # Stub returns empty
    
    @pytest.mark.asyncio
    async def test_select_tests_empty_changes(self, qa_agent):
        """Test selection with no changes"""
        result = await qa_agent.select_tests_for_change(
            changed_files=[]
        )
        
        assert isinstance(result, list)


class TestSelfHealingTests:
    """Test self-healing tests"""
    
    @pytest.mark.asyncio
    async def test_heal_failing_test_with_llm(self, qa_agent, mock_llm):
        """Test healing with LLM"""
        mock_llm.generate.return_value = {
            "response": "Fixed test code",
            "model": "qwen-test"
        }
        qa_agent.llm_selector = mock_llm
        
        result = await qa_agent.heal_failing_test(
            test_name="Тест проверки",
            failure_reason="Assertion failed"
        )
        
        assert result["status"] == "fixed"
        assert "fixed_test" in result
        mock_llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_heal_failing_test_no_llm(self, qa_agent):
        """Test healing without LLM"""
        qa_agent.llm_selector = None
        
        result = await qa_agent.heal_failing_test(
            test_name="Test",
            failure_reason="Error"
        )
        
        assert result["status"] == "llm_not_available"


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_generate_tests_empty_functions(self, qa_agent):
        """Test generation with empty function list"""
        result = await qa_agent.generate_vanessa_tests(
            module_name="Модуль",
            functions=[],
            use_llm=False
        )
        
        assert "Функционал" in result
    
    @pytest.mark.asyncio
    async def test_heal_empty_test_name(self, qa_agent, mock_llm):
        """Test healing with empty test name"""
        qa_agent.llm_selector = mock_llm
        
        result = await qa_agent.heal_failing_test(
            test_name="",
            failure_reason="Error"
        )
        
        assert "status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
