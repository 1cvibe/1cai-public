"""
Meta Optimizer Service
"""
from typing import Any, Dict, List, Optional
import numpy as np

from src.utils.structured_logging import StructuredLogger
from src.modules.nested_learning.domain.models import OptimizationCriteria, SuccessPattern, OptimizerState

logger = StructuredLogger(__name__).logger


class MetaOptimizer:
    """
    Service for self-referential optimization of learning criteria.
    """

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.performance_history: List[float] = []
        self.best_criteria: Optional[OptimizationCriteria] = None
        self.best_performance: float = 0.0
        self.consecutive_failures: int = 0
        self.optimization_history: List[Dict] = []

        logger.info("Created MetaOptimizer service", extra={"lr": learning_rate})

    def optimize_criteria(
        self, base_criteria: OptimizationCriteria, success_patterns: List[SuccessPattern]
    ) -> OptimizationCriteria:
        """
        Optimize selection criteria based on success patterns.
        """
        if not success_patterns:
            return base_criteria

        # 1. Analyze patterns
        analysis = self._analyze_patterns(success_patterns)
        current_success_rate = analysis.get("success_rate", 0.0)

        # 2. Update adaptive learning rate
        self._update_learning_rate(current_success_rate)

        # 3. Check for regression and rollback
        if self._should_rollback(current_success_rate):
            logger.warning("Detected performance regression, rolling back criteria")
            return self.best_criteria if self.best_criteria else base_criteria

        # 4. Update best criteria
        if current_success_rate > self.best_performance:
            self.best_performance = current_success_rate
            self.best_criteria = base_criteria.model_copy()
            self.consecutive_failures = 0
        elif current_success_rate < self.best_performance * 0.8:
            self.consecutive_failures += 1

        # 5. Modify criteria
        modified = base_criteria.model_copy()

        # Adjust cost threshold
        if "cost_threshold" in analysis:
            current_cost = modified.max_cost
            optimal_cost = analysis["cost_threshold"]
            new_cost = current_cost + self.learning_rate * (optimal_cost - current_cost)
            modified.max_cost = new_cost

        # Adjust latency threshold
        if "latency_threshold" in analysis:
            current_latency = modified.max_latency_ms
            optimal_latency = analysis["latency_threshold"]
            new_latency = current_latency + self.learning_rate * (optimal_latency - current_latency)
            modified.max_latency_ms = int(new_latency)

        self._record_history(base_criteria, modified, analysis)
        return modified

    def _update_learning_rate(self, current_performance: float):
        """Adaptively update learning rate"""
        self.performance_history.append(current_performance)
        if len(self.performance_history) > 10:
            self.performance_history.pop(0)

        if len(self.performance_history) >= 3:
            variance = np.var(self.performance_history)
            if variance > 0.05:
                self.learning_rate = max(0.01, self.learning_rate * 0.8)
            elif variance < 0.01 and self.learning_rate < 0.5:
                self.learning_rate = min(0.5, self.learning_rate * 1.1)

    def _should_rollback(self, current_performance: float) -> bool:
        """Check if rollback is needed"""
        if not self.best_criteria:
            return False
        if current_performance < self.best_performance * 0.6:
            if self.consecutive_failures >= 3:
                return True
        return False

    def _analyze_patterns(self, patterns: List[SuccessPattern]) -> Dict[str, Any]:
        """Analyze patterns for insights"""
        successful = [p for p in patterns if p.success]

        analysis = {}
        if successful:
            costs = [p.metrics.get("cost", 0.0) for p in successful]
            if costs:
                analysis["cost_threshold"] = np.percentile(costs, 75)

            latencies = [p.metrics.get("latency_ms", 0) for p in successful]
            if latencies:
                analysis["latency_threshold"] = np.percentile(latencies, 75)

        analysis["success_rate"] = len(successful) / len(patterns)
        return analysis

    def _record_history(self, base, modified, analysis):
        self.optimization_history.append(
            {
                "base": base.model_dump(),
                "modified": modified.model_dump(),
                "analysis": analysis,
                "lr": self.learning_rate,
            }
        )

    def get_state(self) -> OptimizerState:
        return OptimizerState(
            learning_rate=self.learning_rate,
            best_performance=self.best_performance,
            consecutive_failures=self.consecutive_failures,
            total_optimizations=len(self.optimization_history),
        )
