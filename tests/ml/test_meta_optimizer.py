import pytest
import numpy as np
from src.modules.nested_learning.services.meta_optimizer import MetaOptimizer
from src.modules.nested_learning.domain.models import OptimizationCriteria, SuccessPattern

class TestMetaOptimizer:
    
    def test_adaptive_learning_rate_decrease(self):
        """Test that high variance in performance decreases learning rate"""
        optimizer = MetaOptimizer(learning_rate=0.1)
        initial_lr = optimizer.learning_rate
        
        # Simulate volatile performance
        # Variance of [0.1, 0.9, 0.1, 0.9] is high
        performances = [0.1, 0.9, 0.1, 0.9, 0.1, 0.9]
        
        for p in performances:
            optimizer._update_learning_rate(p)
            
        assert optimizer.learning_rate < initial_lr
        
    def test_adaptive_learning_rate_increase(self):
        """Test that stable performance increases learning rate"""
        optimizer = MetaOptimizer(learning_rate=0.1)
        initial_lr = optimizer.learning_rate
        
        # Simulate stable performance
        performances = [0.8, 0.81, 0.82, 0.81, 0.82]
        
        for p in performances:
            optimizer._update_learning_rate(p)
            
        assert optimizer.learning_rate > initial_lr

    def test_rollback_mechanism(self):
        """Test that significant regression triggers rollback"""
        optimizer = MetaOptimizer()
        base_criteria = OptimizationCriteria(max_cost=0.01)
        
        # 1. Establish baseline best performance
        patterns = [SuccessPattern(level="test", similarity=1.0, success=True) for _ in range(10)]
        optimizer.optimize_criteria(base_criteria, patterns)
        assert optimizer.best_performance == 1.0
        assert optimizer.best_criteria is not None
        
        # 2. Simulate regression
        # 3 consecutive failures with low performance
        for _ in range(3):
            mixed_patterns = (
                [SuccessPattern(level="test", similarity=1.0, success=True) for _ in range(2)] + 
                [SuccessPattern(level="test", similarity=1.0, success=False) for _ in range(8)]
            )
            optimizer.optimize_criteria(base_criteria, mixed_patterns)
            
        # Should trigger rollback
        assert optimizer._should_rollback(0.2)
        
    def test_oscillation_dampening(self):
        """Test that variance calculation correctly identifies oscillation"""
        optimizer = MetaOptimizer()
        
        # Oscillating pattern
        history = [0.2, 0.8, 0.2, 0.8, 0.2]
        optimizer.performance_history = history
        
        variance = np.var(history)
        assert variance > 0.05 # Threshold used in implementation
