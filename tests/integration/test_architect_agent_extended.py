import pytest
from src.ai.agents.architect_agent_extended import ArchitectAgentExtended
from src.ai.code_analysis.graph import Node, NodeKind, Edge, EdgeKind
from src.db.neo4j_client import get_neo4j_client

# Check availability
try:
    client = get_neo4j_client()
    NEO4J_AVAILABLE = client.connect()
except Exception:
    NEO4J_AVAILABLE = False

@pytest.mark.skipif(not NEO4J_AVAILABLE, reason="Neo4j not available")
@pytest.mark.asyncio
class TestArchitectAgentExtended:
    
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        self.agent = ArchitectAgentExtended()
        self.test_ids = []
        yield
        # Cleanup
        for nid in self.test_ids:
            self.agent.client.execute_query("MATCH (n:Node {id: $id}) DETACH DELETE n", {"id": nid})

    async def test_analyze_system_basic(self):
        # Create a simple graph
        n1 = Node(id="arch_test_1", kind=NodeKind.MODULE, display_name="Mod1")
        n2 = Node(id="arch_test_2", kind=NodeKind.MODULE, display_name="Mod2")
        self.test_ids.extend([n1.id, n2.id])
        
        await self.agent.backend.upsert_node(n1)
        await self.agent.backend.upsert_node(n2)
        
        # Connect them
        edge = Edge(source=n1.id, target=n2.id, kind=EdgeKind.DEPENDS_ON)
        await self.agent.backend.upsert_edge(edge)
        
        result = await self.agent.analyze_system("Test System")
        
        assert result["analysis"]["modules_count"] >= 2
        assert result["architecture"]["metrics"]["coupling"] >= 0.0

    async def test_detect_cycles(self):
        # Create a cycle: A -> B -> A
        n1 = Node(id="cycle_1", kind=NodeKind.MODULE, display_name="Cycle1")
        n2 = Node(id="cycle_2", kind=NodeKind.MODULE, display_name="Cycle2")
        self.test_ids.extend([n1.id, n2.id])
        
        await self.agent.backend.upsert_node(n1)
        await self.agent.backend.upsert_node(n2)
        
        await self.agent.backend.upsert_edge(Edge(source=n1.id, target=n2.id, kind=EdgeKind.DEPENDS_ON))
        await self.agent.backend.upsert_edge(Edge(source=n2.id, target=n1.id, kind=EdgeKind.DEPENDS_ON))
        
        cycles = await self.agent._detect_cycles()
        
        # We expect at least one cycle involving these nodes
        # Note: Cycle detection might return multiple permutations or existing cycles in DB
        found = False
        for cycle in cycles:
            if "Cycle1" in cycle and "Cycle2" in cycle:
                found = True
                break
        assert found
