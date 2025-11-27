"""
SQL Optimizer Domain Layer

Domain models и exceptions для SQL Optimizer модуля.
"""

from src.modules.sql_optimizer.domain.models import (
    QueryComplexity,
    OptimizationImpact,
    IndexType,
    SQLQuery,
    QueryAnalysis,
    IndexRecommendation,
    OptimizedQuery,
    PerformancePrediction,
    OptimizationResult,
)

from src.modules.sql_optimizer.domain.exceptions import (
    SQLOptimizerError,
    QueryAnalysisError,
    QueryOptimizationError,
    InvalidQueryError,
)

__all__ = [
    # Models
    "QueryComplexity",
    "OptimizationImpact",
    "IndexType",
    "SQLQuery",
    "QueryAnalysis",
    "IndexRecommendation",
    "OptimizedQuery",
    "PerformancePrediction",
    "OptimizationResult",
    # Exceptions
    "SQLOptimizerError",
    "QueryAnalysisError",
    "QueryOptimizationError",
    "InvalidQueryError",
]
