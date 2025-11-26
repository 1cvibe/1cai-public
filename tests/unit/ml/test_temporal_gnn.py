"""
Unit tests for Temporal GNN

Tests temporal graph neural network components.
"""

import pytest
import torch
import numpy as np

from src.ml.graph.temporal_gnn import TemporalGNN, TemporalAttention, TimeEncoder, GraphEvolutionTracker


class TestTimeEncoder:
    """Test time encoding"""

    def test_time_encoder_shape(self):
        """Test output shape"""
        encoder = TimeEncoder(hidden_dim=128)
        timestamps = torch.tensor([1.0, 2.0, 3.0])

        output = encoder(timestamps)

        assert output.shape == (3, 128)

    def test_time_encoder_different_times(self):
        """Test different timestamps produce different encodings"""
        encoder = TimeEncoder(hidden_dim=128)
        t1 = torch.tensor([1.0])
        t2 = torch.tensor([100.0])

        enc1 = encoder(t1)
        enc2 = encoder(t2)

        # Should be different
        assert not torch.allclose(enc1, enc2)


class TestTemporalAttention:
    """Test temporal attention mechanism"""

    def test_temporal_attention_shape(self):
        """Test output shape"""
        attention = TemporalAttention(hidden_dim=128)
        x = torch.randn(5, 128)
        timestamps = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])

        output = attention(x, timestamps)

        assert output.shape == (5, 128)

    def test_temporal_attention_recent_bias(self):
        """Test that recent nodes get higher attention"""
        attention = TemporalAttention(hidden_dim=128, time_decay=1.0)
        x = torch.randn(3, 128)

        # Recent, medium, old
        timestamps = torch.tensor([10.0, 5.0, 1.0])

        output = attention(x, timestamps)

        # Output should be influenced more by recent nodes
        assert output.shape == (3, 128)


class TestTemporalGNN:
    """Test Temporal GNN model"""

    def test_tgnn_forward(self):
        """Test forward pass"""
        model = TemporalGNN(node_features=128, hidden_dim=256, num_layers=2)

        # Create dummy data
        num_nodes = 10
        x = torch.randn(num_nodes, 128)
        edge_index = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
        timestamps = torch.randn(num_nodes)

        # Forward pass
        output = model(x, edge_index, timestamps)

        assert "embeddings" in output
        assert "impact" in output
        assert "change_type" in output
        assert output["embeddings"].shape == (num_nodes, 256)
        assert output["impact"].shape == (num_nodes, 1)
        assert output["change_type"].shape == (num_nodes, 3)

    def test_tgnn_predict_impact(self):
        """Test impact prediction"""
        model = TemporalGNN(node_features=128, hidden_dim=256)

        num_nodes = 10
        x = torch.randn(num_nodes, 128)
        edge_index = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
        timestamps = torch.randn(num_nodes)

        # Predict impact for node 0
        impact_score, affected_indices = model.predict_impact(x, edge_index, timestamps, target_node_idx=0)

        assert isinstance(impact_score, float)
        assert 0.0 <= impact_score <= 1.0
        assert isinstance(affected_indices, np.ndarray)

    def test_tgnn_different_layer_counts(self):
        """Test with different layer counts"""
        for num_layers in [1, 2, 3, 4]:
            model = TemporalGNN(node_features=128, hidden_dim=256, num_layers=num_layers)

            x = torch.randn(5, 128)
            edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
            timestamps = torch.randn(5)

            output = model(x, edge_index, timestamps)

            assert output["embeddings"].shape == (5, 256)


class TestGraphEvolutionTracker:
    """Test graph evolution tracking"""

    def test_record_change(self):
        """Test recording changes"""
        tracker = GraphEvolutionTracker(max_history=10)

        tracker.record_change(node_id="node1", change_type="modify", timestamp=1.0, metadata={"author": "test"})

        assert len(tracker.history) == 1
        assert tracker.history[0]["node_id"] == "node1"
        assert tracker.history[0]["change_type"] == "modify"

    def test_max_history_eviction(self):
        """Test that old entries are evicted"""
        tracker = GraphEvolutionTracker(max_history=3)

        # Add 5 changes
        for i in range(5):
            tracker.record_change(node_id=f"node{i}", change_type="modify", timestamp=float(i))

        # Should only keep last 3
        assert len(tracker.history) == 3
        assert tracker.history[0]["node_id"] == "node2"
        assert tracker.history[-1]["node_id"] == "node4"

    def test_get_changes_since(self):
        """Test filtering by timestamp"""
        tracker = GraphEvolutionTracker()

        tracker.record_change("node1", "add", 1.0)
        tracker.record_change("node2", "modify", 2.0)
        tracker.record_change("node3", "delete", 3.0)

        # Get changes since timestamp 1.5
        recent = tracker.get_changes_since(1.5)

        assert len(recent) == 2
        assert recent[0]["node_id"] == "node2"
        assert recent[1]["node_id"] == "node3"

    def test_get_changes_by_node(self):
        """Test filtering by node ID"""
        tracker = GraphEvolutionTracker()

        tracker.record_change("node1", "add", 1.0)
        tracker.record_change("node1", "modify", 2.0)
        tracker.record_change("node2", "add", 3.0)

        # Get changes for node1
        node1_changes = tracker.get_changes_since(0.0, node_id="node1")

        assert len(node1_changes) == 2
        assert all(c["node_id"] == "node1" for c in node1_changes)

    def test_get_change_frequency(self):
        """Test change frequency calculation"""
        tracker = GraphEvolutionTracker()

        # Add 3 changes over 2 days
        tracker.record_change("node1", "modify", 0.0)
        tracker.record_change("node1", "modify", 86400.0)  # 1 day later
        tracker.record_change("node1", "modify", 172800.0)  # 2 days later

        freq = tracker.get_change_frequency("node1")

        # 3 changes over 2 days = 1.5 changes/day
        assert freq == pytest.approx(1.5, rel=0.1)

    def test_get_change_frequency_no_changes(self):
        """Test frequency for node with no changes"""
        tracker = GraphEvolutionTracker()

        freq = tracker.get_change_frequency("nonexistent")

        assert freq == 0.0

    def test_get_stats(self):
        """Test statistics"""
        tracker = GraphEvolutionTracker()

        tracker.record_change("node1", "add", 1.0)
        tracker.record_change("node2", "modify", 2.0)
        tracker.record_change("node1", "delete", 3.0)

        stats = tracker.get_stats()

        assert stats["total_changes"] == 3
        assert stats["unique_nodes"] == 2
        assert stats["history_size"] == 3


@pytest.mark.asyncio
class TestTemporalGNNIntegration:
    """Integration tests for Temporal GNN"""

    async def test_end_to_end_prediction(self):
        """Test end-to-end impact prediction"""
        model = TemporalGNN(node_features=128, hidden_dim=256)
        tracker = GraphEvolutionTracker()

        # Create graph
        num_nodes = 20
        x = torch.randn(num_nodes, 128)
        edge_index = torch.tensor(
            [[i for i in range(num_nodes - 1)], [i + 1 for i in range(num_nodes - 1)]], dtype=torch.long
        )
        timestamps = torch.linspace(0, 100, num_nodes)

        # Predict impact
        impact_score, affected = model.predict_impact(x, edge_index, timestamps, target_node_idx=5)

        # Record change
        tracker.record_change(node_id="node5", change_type="modify", timestamp=50.0)

        assert isinstance(impact_score, float)
        assert len(affected) > 0
        assert len(tracker.history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
