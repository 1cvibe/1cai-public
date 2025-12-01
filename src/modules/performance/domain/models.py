from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SLOConfig(BaseModel):
    """Конфигурация для Service Level Objective (SLO)."""

    target: float
    window: int  # секунды


class SLOMetric(BaseModel):
    """Записанное значение метрики для SLO."""

    value: float
    timestamp: float


class SLIStatus(BaseModel):
    """Текущий статус Service Level Indicator (SLI)."""

    sli: float
    target: float
    error_budget: float
    violation: bool


class GPUStats(BaseModel):
    """Статистика для GPU."""

    gpu_weights: Dict[int, float]
    gpu_load: Dict[int, float]
    gpu_performance: Dict[int, float]
    gpu_request_count: Dict[int, int]


class BatcherStats(BaseModel):
    """Статистика для батчера."""

    current_batch_size: int
    current_memory_mb: float
    max_memory_mb: float


class OptimizationFeatures(BaseModel):
    """Признаки, используемые для предиктивной оптимизации."""

    text_length: int
    available_memory: float
    density: float
    log_length: float
    log_memory: float
    avg_time: float = 0.0
    avg_efficiency: float = 0.0
    std_time: float = 0.0
    std_efficiency: float = 0.0
