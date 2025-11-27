"""
Technical Writer Domain Layer

Domain models и exceptions для Technical Writer модуля.
"""

from src.modules.technical_writer.domain.models import (
    HTTPMethod,
    Audience,
    DocumentationType,
    APIParameter,
    APIEndpoint,
    APIExample,
    APIDocumentation,
    GuideSection,
    FAQItem,
    UserGuide,
    ReleaseNotes,
    Parameter,
    FunctionDocumentation,
)

from src.modules.technical_writer.domain.exceptions import (
    TechnicalWriterError,
    APIDocGenerationError,
    UserGuideGenerationError,
    ReleaseNotesGenerationError,
    CodeDocGenerationError,
)

__all__ = [
    # Models
    "HTTPMethod",
    "Audience",
    "DocumentationType",
    "APIParameter",
    "APIEndpoint",
    "APIExample",
    "APIDocumentation",
    "GuideSection",
    "FAQItem",
    "UserGuide",
    "ReleaseNotes",
    "Parameter",
    "FunctionDocumentation",
    # Exceptions
    "TechnicalWriterError",
    "APIDocGenerationError",
    "UserGuideGenerationError",
    "ReleaseNotesGenerationError",
    "CodeDocGenerationError",
]
