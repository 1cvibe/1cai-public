"""
Architect Domain Layer

Domain models и exceptions для Architect модуля.
"""

from src.modules.architect.domain.models import (
    AntiPatternType,
    Severity,
    Effort,
    HealthStatus,
    ADRStatus,
    ArchitectureMetrics,
    AntiPattern,
    ArchitectureAnalysisResult,
    Alternative,
    Consequences,
    ADR,
)

from src.modules.architect.domain.exceptions import (
    ArchitectError,
    ArchitectureAnalysisError,
    ADRGenerationError,
    AntiPatternDetectionError,
)

__all__ = [
    # Models
    "AntiPatternType",
    "Severity",
    "Effort",
    "HealthStatus",
    "ADRStatus",
    "ArchitectureMetrics",
    "AntiPattern",
    "ArchitectureAnalysisResult",
    "Alternative",
    "Consequences",
    "ADR",
    # Exceptions
    "ArchitectError",
    "ArchitectureAnalysisError",
    "ADRGenerationError",
    "AntiPatternDetectionError",
]
