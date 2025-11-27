"""
QA Engineer Domain Layer

Domain models и exceptions для QA Engineer модуля.
"""

from src.modules.qa.domain.models import (
    TestType,
    TestFramework,
    CoverageGrade,
    TestParameter,
    TestCase,
    TestGenerationResult,
    CoverageReport,
    TestTemplate,
)

from src.modules.qa.domain.exceptions import (
    QAError,
    TestGenerationError,
    CoverageAnalysisError,
)

__all__ = [
    # Models
    "TestType",
    "TestFramework",
    "CoverageGrade",
    "TestParameter",
    "TestCase",
    "TestGenerationResult",
    "CoverageReport",
    "TestTemplate",
    # Exceptions
    "QAError",
    "TestGenerationError",
    "CoverageAnalysisError",
]
