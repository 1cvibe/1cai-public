"""
Integration tests for Nested Assistants

End-to-end tests for conversational memory.
"""

import pytest

from src.ai.assistants.nested_assistant import NestedAssistant


@pytest.mark.asyncio
class TestNestedAssistantIntegration:
    """Integration tests for nested assistants"""

    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation with context"""
        assistant = NestedAssistant(
            role="developer", name="Dev AI", system_prompt="You are a helpful 1C developer assistant"
        )

        assistant.start_session("integration_test")

        # Turn 1
        result1 = assistant.process_message("Как создать функцию в 1С?", context={"project": "TestProject"})
        assert "response" in result1

        # Turn 2 (should use context from turn 1)
        result2 = assistant.process_message("А как её вызвать?", context={"project": "TestProject"})
        assert "response" in result2
        assert result2["context_used"] >= 0

        # Turn 3
        result3 = assistant.process_message("Покажи пример с параметрами", context={"project": "TestProject"})
        assert "response" in result3

        assistant.end_session()

    async def test_feedback_learning(self):
        """Test learning from feedback"""
        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        assistant.start_session("feedback_test")

        # Positive interaction
        result1 = assistant.process_message("Good query")
        assistant.provide_feedback(result1["response_id"], rating=5)

        # Negative interaction
        result2 = assistant.process_message("Bad query")
        assistant.provide_feedback(result2["response_id"], rating=1)

        # Check preferences
        prefs = assistant.memory.get_user_preferences()
        assert "successful_patterns" in prefs
        assert "unsuccessful_patterns" in prefs

        assistant.end_session()

    async def test_long_conversation(self):
        """Test long conversation with memory retention"""
        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        assistant.start_session("long_test")

        # 20 messages
        for i in range(20):
            result = assistant.process_message(f"Message {i}")
            assert "response" in result

        # Check stats
        assert assistant.stats["total_messages"] == 20

        assistant.end_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
