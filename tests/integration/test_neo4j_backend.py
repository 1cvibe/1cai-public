import pytest
import os
from src.ai.code_analysis.graph import Node, NodeKind, Edge, EdgeKind
from src.ai.code_analysis.neo4j_backend import Neo4jCodeGraphBackend
from src.db.neo4j_client import get_neo4j_client

# Check if Neo4j is available
try:
    # We just check if we can get a client and it connects.
    # We do NOT disconnect because get_neo4j_client returns a global singleton.
    # If we close it, it stays closed for the tests.
    client = get_neo4j_client()
    NEO4J_AVAILABLE = client.connect()
except Exception:
    NEO4J_AVAILABLE = False


@pytest.mark.skipif(not NEO4J_AVAILABLE, reason="Neo4j not available")
@pytest.mark.asyncio
class TestNeo4jBackend:
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        # Setup: Clear test data
        self.backend = Neo4jCodeGraphBackend()
        # Use a unique prefix or label for test data to avoid wiping real data?
        # For now, we assume a test database or we clean up specific IDs.
        self.test_ids = []
        yield
        # Teardown: Delete test nodes
        for nid in self.test_ids:
            # We need a delete method in backend or raw query
            # Adding a raw delete for cleanup
            self.backend.client.execute_query("MATCH (n:Node {id: $id}) DETACH DELETE n", {"id": nid})

    async def test_upsert_and_get_node(self):
        node = Node(
            id="test_node_1",
            kind=NodeKind.SERVICE,
            display_name="Test Service",
            labels=["Test"],
            props={"version": "1.0"},
        )
        self.test_ids.append(node.id)

        await self.backend.upsert_node(node)

        fetched = await self.backend.get_node("test_node_1")
        assert fetched is not None
        assert fetched.id == node.id
        assert fetched.kind == node.kind
        assert fetched.display_name == node.display_name
        assert fetched.props["version"] == "1.0"

    async def test_upsert_edge_and_neighbors(self):
        node1 = Node(id="test_n1", kind=NodeKind.MODULE, display_name="M1")
        node2 = Node(id="test_n2", kind=NodeKind.FUNCTION, display_name="F1")
        self.test_ids.extend([node1.id, node2.id])

        await self.backend.upsert_node(node1)
        await self.backend.upsert_node(node2)

        edge = Edge(source=node1.id, target=node2.id, kind=EdgeKind.OWNS, props={"weight": 1})

        await self.backend.upsert_edge(edge)

        neighbors = await self.backend.neighbors(node1.id)
        assert len(neighbors) == 1
        assert neighbors[0].id == node2.id

        # Test filter by kind
        neighbors_filtered = await self.backend.neighbors(node1.id, kinds=[EdgeKind.OWNS])
        assert len(neighbors_filtered) == 1

        neighbors_wrong = await self.backend.neighbors(node1.id, kinds=[EdgeKind.DEPENDS_ON])
        assert len(neighbors_wrong) == 0

    async def test_find_nodes(self):
        node = Node(id="test_find_1", kind=NodeKind.DB_TABLE, display_name="Table1", props={"criticality": "high"})
        self.test_ids.append(node.id)
        await self.backend.upsert_node(node)

        found = await self.backend.find_nodes(kind=NodeKind.DB_TABLE, prop_equals={"criticality": "high"})
        # There might be other nodes in DB, so check if ours is in list
        ids = [n.id for n in found]
        assert node.id in ids
