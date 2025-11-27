"""
Business Analyst Domain Exceptions

Custom exceptions для Business Analyst модуля.
"""


class BusinessAnalystError(Exception):
    """Базовое исключение для Business Analyst модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class RequirementExtractionError(BusinessAnalystError):
    """Ошибка при извлечении требований"""
    pass


class BPMNGenerationError(BusinessAnalystError):
    """Ошибка при генерации BPMN диаграммы"""
    pass


class GapAnalysisError(BusinessAnalystError):
    """Ошибка при gap analysis"""
    pass


class TraceabilityError(BusinessAnalystError):
    """Ошибка при генерации матрицы прослеживаемости"""
    pass


__all__ = [
    "BusinessAnalystError",
    "RequirementExtractionError",
    "BPMNGenerationError",
    "GapAnalysisError",
    "TraceabilityError",
]
