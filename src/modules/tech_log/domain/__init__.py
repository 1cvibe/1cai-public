"""
Tech Log Analyzer Domain Layer

Domain models и exceptions для Tech Log Analyzer модуля.
"""

from src.modules.tech_log.domain.models import (
    Severity,
    EventType,
    IssueType,
    TechLogEvent,
    PerformanceIssue,
    LogAnalysisResult,
    PerformanceAnalysisResult,
)

from src.modules.tech_log.domain.exceptions import (
    TechLogError,
    LogParsingError,
    PerformanceAnalysisError,
    LogFileNotFoundError,
)

__all__ = [
    # Models
    "Severity",
    "EventType",
    "IssueType",
    "TechLogEvent",
    "PerformanceIssue",
    "LogAnalysisResult",
    "PerformanceAnalysisResult",
    # Exceptions
    "TechLogError",
    "LogParsingError",
    "PerformanceAnalysisError",
    "LogFileNotFoundError",
]
