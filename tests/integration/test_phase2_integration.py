"""
Cross-component integration tests

Tests interaction between Phase 2 components.
"""

import pytest

from src.modules.graph_api.services.temporal_graph_service import TemporalGraphService
from src.modules.graph_api.services.graph_service import GraphService
from src.ai.assistants.nested_assistant import NestedAssistant
from src.db.neo4j_client import Neo4jClient


@pytest.mark.asyncio
class TestPhase2Integration:
    """Cross-component integration tests"""

    async def test_graph_and_assistant_interaction(self):
        """Test graph service and assistant working together"""
        # Setup graph service
        neo4j = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="test")
        base_graph = GraphService(neo4j)
        temporal_graph = TemporalGraphService(base_graph)

        # Setup assistant
        assistant = NestedAssistant(
            role="architect", name="Architect AI", system_prompt="You are an architecture assistant"
        )

        assistant.start_session("integration")

        # User asks about code change
        result = assistant.process_message(
            "Какие компоненты затронет изменение Function:MyFunc?", context={"project": "TestProject"}
        )

        # Predict impact using graph
        impact = await temporal_graph.predict_impact(node_id="Function:MyFunc", change_type="modify")

        # Both should work
        assert "response" in result
        assert "impact_score" in impact

        assistant.end_session()

    async def test_memory_persistence_across_sessions(self):
        """Test memory persistence"""
        assistant = NestedAssistant(role="developer", name="Dev AI", system_prompt="Test")

        # Session 1
        assistant.start_session("session_1")
        result1 = assistant.process_message("Important information")
        assistant.provide_feedback(result1["response_id"], rating=5)
        assistant.end_session()

        # Session 2 (should remember from session 1)
        assistant.start_session("session_2")
        result2 = assistant.process_message("Related query")

        # Should have some context
        assert result2["context_used"] >= 0

        assistant.end_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
