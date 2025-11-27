"""
Technical Writer Domain Exceptions

Custom exceptions для Technical Writer модуля.
"""


class TechnicalWriterError(Exception):
    """Базовое исключение для Technical Writer модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class APIDocGenerationError(TechnicalWriterError):
    """Ошибка при генерации API документации"""
    pass


class UserGuideGenerationError(TechnicalWriterError):
    """Ошибка при генерации user guide"""
    pass


class ReleaseNotesGenerationError(TechnicalWriterError):
    """Ошибка при генерации release notes"""
    pass


class CodeDocGenerationError(TechnicalWriterError):
    """Ошибка при генерации code documentation"""
    pass


__all__ = [
    "TechnicalWriterError",
    "APIDocGenerationError",
    "UserGuideGenerationError",
    "ReleaseNotesGenerationError",
    "CodeDocGenerationError",
]
