"""
Nested Learning Domain Models
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class OptimizationCriteria(BaseModel):
    """Criteria for provider selection optimization"""
    max_cost: float = Field(default=0.01, description="Maximum cost per 1K tokens")
    max_latency_ms: int = Field(default=1000, description="Maximum latency in milliseconds")
    quality_weight: float = Field(default=0.5, description="Weight for quality vs cost/latency")
    
    class Config:
        extra = "allow"

class SuccessPattern(BaseModel):
    """Pattern of successful execution"""
    level: str
    similarity: float
    success: bool
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default=0.0)

class OptimizerState(BaseModel):
    """State of the meta-optimizer"""
    learning_rate: float
    best_performance: float
    consecutive_failures: int
    total_optimizations: int
