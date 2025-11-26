"""
Unit tests for Deep Optimizer

Tests deep optimizer with nested momentum.
"""

import pytest
import torch
import torch.nn as nn

from src.ml.training.deep_optimizer import DeepOptimizer


class SimpleModel(nn.Module):
    """Simple model for testing"""

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 1)

    def forward(self, x):
        return self.linear(x)


class TestDeepOptimizer:
    """Test deep optimizer"""

    def test_initialization(self):
        """Test optimizer initialization"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model)

        assert optimizer.model is model
        assert optimizer.loss_fn_type == "l2_regression"
        assert optimizer.momentum_type == "nested"

    def test_l2_regression_loss(self):
        """Test L2 regression loss"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model, loss_fn="l2_regression")

        predictions = torch.randn(5, 1)
        targets = torch.randn(5, 1)

        loss = optimizer.l2_regression_loss(predictions, targets)

        assert isinstance(loss, torch.Tensor)
        assert loss.item() >= 0

    def test_optimization_step(self):
        """Test optimization step"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model)

        # Create dummy data
        batch_data = torch.randn(10, 10)
        batch_labels = torch.randn(10, 1)

        # Perform step
        loss = optimizer.step(batch_data, batch_labels)

        assert isinstance(loss, float)
        assert loss >= 0
        assert optimizer.stats["total_steps"] == 1

    def test_retry_logic(self):
        """Test retry on failure"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model, max_retries=3)

        # This should work without retries
        batch_data = torch.randn(10, 10)
        batch_labels = torch.randn(10, 1)

        loss = optimizer.step(batch_data, batch_labels)

        assert optimizer.stats["total_retries"] == 0

    def test_nested_momentum(self):
        """Test nested momentum"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model, momentum_type="nested")

        # Run multiple steps
        for i in range(15):
            batch_data = torch.randn(10, 10)
            batch_labels = torch.randn(10, 1)
            optimizer.step(batch_data, batch_labels)

        # Should have updated medium momentum
        assert optimizer.step_count == 15

    def test_checkpoint_save_load(self):
        """Test checkpoint save/load"""
        import tempfile
        import os

        model = SimpleModel()
        optimizer = DeepOptimizer(model)

        # Train a bit
        for _ in range(5):
            batch_data = torch.randn(10, 10)
            batch_labels = torch.randn(10, 1)
            optimizer.step(batch_data, batch_labels)

        # Save checkpoint
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = os.path.join(tmpdir, "checkpoint.pt")
            optimizer.save_checkpoint(checkpoint_path)

            # Create new optimizer and load
            model2 = SimpleModel()
            optimizer2 = DeepOptimizer(model2)
            optimizer2.load_checkpoint(checkpoint_path)

            assert optimizer2.stats["total_steps"] == optimizer.stats["total_steps"]

    def test_get_stats(self):
        """Test statistics"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model)

        stats = optimizer.get_stats()

        assert "total_steps" in stats
        assert "avg_loss" in stats
        assert "current_lr" in stats

    def test_health_check(self):
        """Test health check"""
        model = SimpleModel()
        optimizer = DeepOptimizer(model)

        health = optimizer.health_check()

        assert health["status"] == "healthy"
        assert "total_steps" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
